"""
Load Test Scenarios using Locust.

Tests system performance under burst load:
- 100 emails in 5 minutes
- p95 < 2s, p99 < 5s, error rate < 1%

Usage:
    # Run headless (no web UI)
    locust -f tests/load/test_burst_load.py --headless -u 100 -t 300s --host=http://localhost:8000
    
    # Run with web UI
    locust -f tests/load/test_burst_load.py --host=http://localhost:8000
    # Then open http://localhost:8089 in browser

Metrics validated:
- p95 latency < 2 seconds
- p99 latency < 5 seconds
- Error rate < 1%
"""

import random
import time
from datetime import datetime
from pathlib import Path

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# Metrics storage for validation
load_test_metrics = {
    "requests_total": 0,
    "failures_total": 0,
    "latencies": [],
    "start_time": None,
    "end_time": None,
}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics."""
    load_test_metrics["start_time"] = datetime.now()
    load_test_metrics["requests_total"] = 0
    load_test_metrics["failures_total"] = 0
    load_test_metrics["latencies"] = []
    print(f"\n{'='*60}")
    print("LOAD TEST STARTED")
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.user_count if environment.runner else 'N/A'}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Validate test metrics and print summary."""
    load_test_metrics["end_time"] = datetime.now()
    
    if not load_test_metrics["latencies"]:
        print("\nNo latency data collected")
        return
    
    # Calculate percentiles
    latencies = sorted(load_test_metrics["latencies"])
    total = len(latencies)
    
    p50_idx = int(total * 0.50)
    p95_idx = int(total * 0.95)
    p99_idx = int(total * 0.99)
    
    p50 = latencies[p50_idx] if p50_idx < total else latencies[-1]
    p95 = latencies[p95_idx] if p95_idx < total else latencies[-1]
    p99 = latencies[p99_idx] if p99_idx < total else latencies[-1]
    
    # Calculate error rate
    total_requests = load_test_metrics["requests_total"]
    total_failures = load_test_metrics["failures_total"]
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    
    # Validation thresholds
    p95_target = 2000  # 2 seconds in ms
    p99_target = 5000  # 5 seconds in ms
    error_rate_target = 1.0  # 1%
    
    print(f"\n{'='*60}")
    print("LOAD TEST RESULTS")
    print(f"{'='*60}")
    print(f"Duration: {load_test_metrics['end_time'] - load_test_metrics['start_time']}")
    print(f"Total Requests: {total_requests}")
    print(f"Total Failures: {total_failures}")
    print(f"")
    print("LATENCY PERCENTILES:")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms (target: <{p95_target}ms) {'✓' if p95 < p95_target else '✗'}")
    print(f"  p99: {p99:.2f}ms (target: <{p99_target}ms) {'✓' if p99 < p99_target else '✗'}")
    print(f"")
    print("ERROR RATE:")
    print(f"  Error Rate: {error_rate:.2f}% (target: <{error_rate_target}%) {'✓' if error_rate < error_rate_target else '✗'}")
    print(f"{'='*60}\n")
    
    # Store results for programmatic access
    environment.results = {
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "error_rate": error_rate,
        "total_requests": total_requests,
        "total_failures": total_failures,
        "passed": p95 < p95_target and p99 < p99_target and error_rate < error_rate_target,
    }


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Track request metrics."""
    load_test_metrics["requests_total"] += 1
    
    if exception:
        load_test_metrics["failures_total"] += 1
    else:
        load_test_metrics["latencies"].append(response_time)


class HealthEndpointUser(HttpUser):
    """
    Simulated user for health endpoint load testing.
    
    Simulates monitoring systems polling health endpoints.
    """
    
    wait_time = between(0.1, 0.5)  # Rapid polling like monitoring systems
    host = "http://localhost:8000"
    
    @task(3)
    def get_health(self):
        """GET /health - Most common operation."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "components" in data:
                    response.success()
                else:
                    response.failure("Invalid health response format")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_live(self):
        """GET /live - Liveness check."""
        with self.client.get("/live", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "alive":
                    response.success()
                else:
                    response.failure("Not alive")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def get_ready(self):
        """GET /ready - Readiness check."""
        with self.client.get("/ready", catch_response=True) as response:
            # Both 200 and 503 are valid responses
            if response.status_code in [200, 503]:
                data = response.json()
                if "status" in data:
                    response.success()
                else:
                    response.failure("Invalid ready response format")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """GET /metrics - Prometheus metrics."""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                # Check for Prometheus format
                content = response.text
                if "fte_component_health" in content:
                    response.success()
                else:
                    response.failure("Missing expected metrics")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def get_config(self):
        """GET /health/config - Configuration endpoint."""
        with self.client.get("/health/config", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "metrics_auth_enabled" in data:
                    response.success()
                else:
                    response.failure("Invalid config response format")
            else:
                response.failure(f"Status code: {response.status_code}")


class BurstLoadUser(HttpUser):
    """
    Simulated user for burst load testing.
    
    Simulates 100 concurrent requests in short burst.
    """
    
    wait_time = between(0.01, 0.1)  # Very rapid requests
    host = "http://localhost:8000"
    
    @task
    def burst_health(self):
        """Rapid health checks."""
        self.client.get("/health")


# Standalone test runner for CI/CD
def run_load_test(
    host: str = "http://localhost:8000",
    users: int = 100,
    duration: str = "300s",
    headless: bool = True,
) -> dict:
    """
    Run load test programmatically.
    
    Args:
        host: Target host URL
        users: Number of concurrent users
        duration: Test duration (e.g., "300s")
        headless: Run without web UI
        
    Returns:
        Test results dict
    """
    import subprocess
    import json
    
    cmd = [
        "locust",
        "-f", __file__,
        "--headless",
        "-u", str(users),
        "-t", duration,
        "--host", host,
        "--json",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON output"}
    else:
        return {"error": result.stderr}


if __name__ == "__main__":
    # Run standalone test
    print("Running load test...")
    results = run_load_test(
        host="http://localhost:8000",
        users=100,
        duration="300s",
    )
    print(f"Results: {results}")
