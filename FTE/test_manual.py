"""Manual test script for filesystem watcher."""

import os
import time
from pathlib import Path

# Set environment
os.environ['DEV_MODE'] = 'true'
os.environ['VAULT_PATH'] = './vault'

from src.filesystem_watcher import FileSystemWatcher

# Create watcher FIRST (dry-run mode - set to False to actually create files)
watcher = FileSystemWatcher(dry_run=False)
print(f'✓ Watcher initialized (dry_run={watcher.dry_run})')

# Create test file in Inbox AFTER watcher is initialized
vault_path = Path('./vault')
inbox_path = vault_path / 'Inbox'
inbox_path.mkdir(exist_ok=True)

test_file = inbox_path / f'manual_test_{int(time.time())}.md'
test_file.write_text('# Manual Test\n\nThis is a manual test file.')

print(f'✓ Created test file: {test_file}')
print(f'  Waiting 2 seconds...')
time.sleep(2)

# Check for updates
updates = watcher.check_for_updates()
print(f'✓ Found {len(updates)} new file(s)')

# Create action file
if updates:
    action_path = watcher.create_action_file(updates[0])
    print(f'✓ Created action file: {action_path}')
    
    # Show action file content
    if action_path.exists():
        print('\n--- Action File Content ---')
        print(action_path.read_text())
        print('--- End ---')
    else:
        print(f'\n(Dry-run mode - file would be created at: {action_path})')

print('\n✓ Test complete!')
print(f'\nNext steps:')
print(f'1. Check vault/Needs_Action/ for action files')
print(f'2. Process the file (move to Done/)')
print(f'3. Check vault/Logs/ for audit trail')
