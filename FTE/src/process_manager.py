"""Process Manager for watcher lifecycle management.

Manages the lifecycle of watcher processes (Gmail, WhatsApp, FileSystem) with:
- Health monitoring
- Auto-restart within 10 seconds
- Restart limits (max 3/hour)
- Memory monitoring (200MB threshold)
- Graceful shutdown

Usage:
    manager = ProcessManager(vault_path="./vault")
    manager.start_all_watchers()
    # ... watchers running ...
    manager.stop_all_watchers()
"""

import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

from .audit_logger import AuditLogger


class ProcessManagerError(Exception):
    """Base exception for process manager errors."""

    pass


class WatcherNotFoundError(ProcessManagerError):
    """Raised when watcher executable is not found."""

    pass


class ProcessManager:
    """
    Manages watcher processes with health monitoring and auto-recovery.

    Attributes:
        vault_path: Root path of the vault directory
        health_check_interval: Seconds between health checks (default: 10)
        memory_threshold_mb: Memory limit per watcher in MB (default: 200)
        max_restarts_per_hour: Maximum restarts per watcher per hour (default: 3)
    """

    def __init__(
        self,
        vault_path: str,
        health_check_interval: int = 10,
        memory_threshold_mb: int = 200,
        max_restarts_per_hour: int = 3,
    ) -> None:
        """
        Initialize the process manager.

        Args:
            vault_path: Root path of the vault directory
            health_check_interval: Seconds between health checks (default: 10)
            memory_threshold_mb: Memory limit per watcher in MB (default: 200)
            max_restarts_per_hour: Maximum restarts per watcher per hour (default: 3)
        """
        self.vault_path = Path(vault_path).resolve()
        self.health_check_interval = health_check_interval
        self.memory_threshold_mb = memory_threshold_mb
        self.max_restarts_per_hour = max_restarts_per_hour

        self.logger = AuditLogger(component="ProcessManager")

        # Watcher processes: {name: subprocess.Popen}
        self._processes: dict[str, subprocess.Popen[Any]] = {}

        # Restart tracking: {name: [timestamp1, timestamp2, ...]}
        self._restart_counts: dict[str, list[datetime]] = {}

        # Metrics callbacks
        self._metrics_callbacks: list[Callable[..., None]] = []

        # Shutdown flag
        self._shutdown = False

        # Health check thread
        self._health_check_thread: threading.Thread | None = None

        # Watcher scripts (relative to vault_path)
        self._watcher_scripts = {
            "gmail_watcher": "src/watchers/gmail_watcher.py",
            "whatsapp_watcher": "src/watchers/whatsapp_watcher.py",
            "filesystem_watcher": "src/filesystem_watcher.py",
        }

        # Register signal handlers
        self._register_signal_handlers()

        self.logger.info(
            "process_manager_initialized",
            {
                "vault_path": str(self.vault_path),
                "health_check_interval": self.health_check_interval,
                "memory_threshold_mb": self.memory_threshold_mb,
                "max_restarts_per_hour": self.max_restarts_per_hour,
            },
        )

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.logger.info("signal_handlers_registered", {"signals": ["SIGINT", "SIGTERM"]})

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        self.logger.log("INFO", "signal_received", {"signal": signal_name})
        self._shutdown = True
        self.stop_all_watchers()

    def register_metrics_callback(self, callback: Callable[..., None]) -> None:
        """
        Register a callback for metrics emission.

        Args:
            callback: Function(metric_name, value, tags) to receive metrics
        """
        self._metrics_callbacks.append(callback)

    def _emit_metrics(
        self,
        metric_name: str,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Emit metrics to registered callbacks."""
        for callback in self._metrics_callbacks:
            try:
                callback(metric_name, value, tags)
            except Exception as e:
                self.logger.info("metrics_callback_failed", {"error": str(e)})

    def _get_python_executable(self) -> str:
        """Get the Python executable path."""
        return sys.executable

    def _get_watcher_script_path(self, watcher_name: str) -> Path:
        """
        Get the full path to a watcher script.

        Args:
            watcher_name: Name of the watcher

        Returns:
            Full path to the watcher script

        Raises:
            WatcherNotFoundError: If script doesn't exist
        """
        if watcher_name not in self._watcher_scripts:
            raise WatcherNotFoundError(f"Unknown watcher: {watcher_name}")

        script_rel_path = self._watcher_scripts[watcher_name]
        script_path = self.vault_path.parent / script_rel_path

        if not script_path.exists():
            raise WatcherNotFoundError(f"Watcher script not found: {script_path}")

        return script_path

    def start_all_watchers(self) -> None:
        """
        Start all watcher processes.

        Launches gmail_watcher.py, whatsapp_watcher.py, filesystem_watcher.py
        as subprocesses.

        Raises:
            WatcherNotFoundError: If any watcher executable is not found
        """
        self.logger.info(
            "starting_all_watchers",
            {"watcher_count": len(self._watcher_scripts)},
        )

        for watcher_name in self._watcher_scripts:
            try:
                self._start_watcher(watcher_name)
            except WatcherNotFoundError as e:
                self.logger.error(
                    "watcher_not_found",
                    {"watcher": watcher_name, "error": str(e)},
                )
                raise
            except Exception as e:
                self.logger.error(
                    "watcher_start_failed",
                    {"watcher": watcher_name, "error": str(e)},
                )
                raise

        self.logger.info("all_watchers_started", {"watchers": list(self._processes.keys())})

        # Start health monitoring thread
        self._start_health_monitoring()

    def _start_watcher(self, watcher_name: str) -> None:
        """
        Start a single watcher process.

        Args:
            watcher_name: Name of the watcher to start

        Raises:
            WatcherNotFoundError: If watcher script not found
        """
        script_path = self._get_watcher_script_path(watcher_name)

        # Build command
        cmd = [
            self._get_python_executable(),
            str(script_path),
        ]

        # Add environment variables
        env = os.environ.copy()
        env["VAULT_PATH"] = str(self.vault_path)
        env["DRY_RUN"] = os.getenv("DRY_RUN", "false")
        env["DEV_MODE"] = os.getenv("DEV_MODE", "false")

        self.logger.info(
            "starting_watcher",
            {"watcher": watcher_name, "command": " ".join(cmd)},
        )

        # Start process
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._processes[watcher_name] = process
        self.logger.info(
            "watcher_started",
            {"watcher": watcher_name, "pid": process.pid},
        )

        self._emit_metrics("process_manager_watcher_starts", tags={"watcher_name": watcher_name})

    def stop_all_watchers(self) -> None:
        """
        Stop all watcher processes gracefully.

        Sends SIGTERM, waits 5 seconds, then SIGKILL if necessary.
        """
        self.logger.info("stopping_all_watchers", {"watcher_count": len(self._processes)})

        # Stop health monitoring
        self._shutdown = True

        for watcher_name, process in list(self._processes.items()):
            self._stop_watcher(watcher_name, process)

        self._processes.clear()
        self.logger.info("all_watchers_stopped", {})

    def _stop_watcher(self, watcher_name: str, process: subprocess.Popen[Any]) -> None:
        """
        Stop a single watcher process.

        Args:
            watcher_name: Name of the watcher
            process: subprocess.Popen instance
        """
        if process.poll() is None:  # Still running
            self.logger.info("stopping_watcher", {"watcher": watcher_name, "pid": process.pid})

            # Send SIGTERM
            process.terminate()

            # Wait up to 5 seconds
            try:
                process.wait(timeout=5)
                self.logger.info("watcher_stopped_gracefully", {"watcher": watcher_name})
            except subprocess.TimeoutExpired:
                # Force kill
                self.logger.warning("watcher_force_killed", {"watcher": watcher_name})
                process.kill()
                process.wait()

            self._emit_metrics("process_manager_watcher_stops", tags={"watcher_name": watcher_name})

    def _check_watcher_health(self, name: str) -> bool:
        """
        Check if a watcher is healthy.

        Args:
            name: Name of the watcher

        Returns:
            True if healthy, False if crashed
        """
        process = self._processes.get(name)
        if not process:
            return False

        # Check if process is running
        if process.poll() is not None:
            self.logger.warning(
                "watcher_crashed",
                {"watcher": name, "pid": process.pid, "returncode": process.returncode},
            )
            return False

        return True

    def _restart_watcher(self, name: str) -> None:
        """
        Restart a crashed watcher.

        Args:
            name: Name of the watcher to restart
        """
        # Check restart limits
        if not self._check_restart_limit(name):
            self.logger.error(
                "restart_limit_exceeded",
                {
                    "watcher": name,
                    "max_restarts_per_hour": self.max_restarts_per_hour,
                },
            )
            self._update_dashboard_alert(
                "CRITICAL",
                f"Watcher '{name}' exceeded restart limit "
                f"({self.max_restarts_per_hour}/hour). "
                "Manual intervention required.",
            )
            self._emit_metrics(
                "process_manager_restart_limit_exceeded",
                tags={"watcher_name": name},
            )
            return

        # Track restart
        self._track_restart(name)

        self.logger.info("restarting_watcher", {"watcher": name})

        try:
            # Remove old process
            if name in self._processes:
                del self._processes[name]

            # Start new watcher
            self._start_watcher(name)

            self._emit_metrics("process_manager_watcher_restarts", tags={"watcher_name": name})

        except Exception as e:
            self.logger.error("watcher_restart_failed", {"watcher": name, "error": str(e)})
            self._emit_metrics("process_manager_restart_failures", tags={"watcher_name": name})

    def _track_restart(self, name: str) -> None:
        """
        Track a restart for rate limiting.

        Args:
            name: Name of the watcher
        """
        now = datetime.now()
        if name not in self._restart_counts:
            self._restart_counts[name] = []

        self._restart_counts[name].append(now)

        # Clean old entries (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self._restart_counts[name] = [ts for ts in self._restart_counts[name] if ts > cutoff]

    def _check_restart_limit(self, name: str) -> bool:
        """
        Check if watcher has exceeded restart limit.

        Args:
            name: Name of the watcher

        Returns:
            True if under limit, False if exceeded
        """
        if name not in self._restart_counts:
            return True

        # Clean old entries
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        self._restart_counts[name] = [ts for ts in self._restart_counts[name] if ts > cutoff]

        return len(self._restart_counts[name]) < self.max_restarts_per_hour

    def _check_memory_usage(self, name: str, process: subprocess.Popen[Any]) -> None:
        """
        Check memory usage of a watcher.

        Args:
            name: Name of the watcher
            process: subprocess.Popen instance
        """
        try:
            ps_process = psutil.Process(process.pid)
            memory_mb = ps_process.memory_info().rss / 1024 / 1024

            self._emit_metrics(
                "process_manager_memory_usage",
                value=memory_mb,
                tags={"watcher_name": name},
            )

            if memory_mb > self.memory_threshold_mb:
                self.logger.warning(
                    "watcher_memory_exceeded",
                    {
                        "watcher": name,
                        "memory_mb": memory_mb,
                        "threshold_mb": self.memory_threshold_mb,
                    },
                )

                # Kill watcher if over limit
                self.logger.info("killing_watcher_memory", {"watcher": name})
                process.kill()
                process.wait()

                self._emit_metrics("process_manager_memory_kill", tags={"watcher_name": name})

        except psutil.NoSuchProcess:
            # Process already dead
            pass
        except Exception as e:
            self.logger.info("memory_check_failed", {"watcher": name, "error": str(e)})

    def _start_health_monitoring(self) -> None:
        """Start the health monitoring thread."""
        self._health_check_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True,
        )
        self._health_check_thread.start()
        self.logger.info(
            "health_monitoring_started",
            {"interval": self.health_check_interval},
        )

    def _health_monitoring_loop(self) -> None:
        """Health monitoring loop (runs in background thread)."""
        while not self._shutdown:
            try:
                for name, process in list(self._processes.items()):
                    # Check health
                    if not self._check_watcher_health(name):
                        # Crashed - restart
                        self._restart_watcher(name)
                    else:
                        # Check memory
                        self._check_memory_usage(name, process)

            except Exception as e:
                self.logger.error("health_check_error", {"error": str(e)})

            # Sleep until next check
            time.sleep(self.health_check_interval)

    def _update_dashboard_alert(self, level: str, message: str) -> None:
        """
        Update Dashboard.md with an alert.

        Args:
            level: Alert level (INFO, WARNING, CRITICAL)
            message: Alert message
        """
        dashboard_path = self.vault_path / "Dashboard.md"

        try:
            timestamp = datetime.now().isoformat()
            alert_line = f"- **[{level}]** {timestamp}: {message}\n"

            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding="utf-8")
                # Prepend to alerts section or create if missing
                if "## Alerts" in content:
                    content = content.replace("## Alerts", f"## Alerts\n{alert_line}")
                else:
                    content += f"\n## Alerts\n{alert_line}"
            else:
                content = f"# Dashboard\n\n## Alerts\n{alert_line}"

            dashboard_path.write_text(content, encoding="utf-8")
            self.logger.info("dashboard_updated", {"level": level, "message": message})

        except Exception as e:
            self.logger.error("dashboard_update_failed", {"error": str(e)})

    def get_watcher_status(self, name: str) -> dict[str, Any]:
        """
        Get status of a specific watcher.

        Args:
            name: Name of the watcher

        Returns:
            Dictionary with status information
        """
        process = self._processes.get(name)
        if not process:
            return {"status": "not_started", "pid": None, "running": False}

        running = process.poll() is None
        status = "running" if running else "stopped"

        result = {
            "status": status,
            "pid": process.pid,
            "running": running,
            "returncode": process.returncode,
        }

        # Add memory if running
        if running:
            try:
                ps_process = psutil.Process(process.pid)
                result["memory_mb"] = ps_process.memory_info().rss / 1024 / 1024
            except Exception:
                pass

        return result

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """
        Get status of all watchers.

        Returns:
            Dictionary mapping watcher names to status dicts
        """
        return {name: self.get_watcher_status(name) for name in self._watcher_scripts}


def main() -> None:
    """Main entry point for process manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Process Manager for FTE Watchers")
    parser.add_argument(
        "--vault-path",
        default="./vault",
        help="Path to vault directory",
    )
    parser.add_argument(
        "--health-interval",
        type=int,
        default=10,
        help="Health check interval in seconds",
    )
    parser.add_argument(
        "--memory-threshold",
        type=int,
        default=200,
        help="Memory threshold in MB",
    )
    parser.add_argument(
        "--max-restarts",
        type=int,
        default=3,
        help="Max restarts per hour",
    )

    args = parser.parse_args()

    manager = ProcessManager(
        vault_path=args.vault_path,
        health_check_interval=args.health_interval,
        memory_threshold_mb=args.memory_threshold,
        max_restarts_per_hour=args.max_restarts,
    )

    try:
        manager.start_all_watchers()

        # Keep running until shutdown
        while not manager._shutdown:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except WatcherNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        manager.stop_all_watchers()
        print("Process manager stopped.")


if __name__ == "__main__":
    main()
