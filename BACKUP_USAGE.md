# Backup/Restore Usage Guide

## Backup Types

| Type | File | Purpose | When Created |
|------|------|---------|--------------|
| **Auto Backup** | `auto_backup.proto` | Latest automatic backup | On shutdown, manual |
| **Auto Backup Prev** | `auto_backup_prev.proto` | Previous auto backup | Rotation on new auto backup |
| **User Backup (Golden)** | `user_backup.proto` | Known-good snapshot | Manual only |

### Auto Backup
- Created automatically on graceful shutdown
- Rotates: current → prev, then writes new
- Survives interrupted writes (prev is fallback)

### Golden Backup (User Backup)
- Created manually when device is in known-good state
- Never overwritten automatically
- Use after initial setup or major config changes
- Last resort fallback for restore

---

## Creating Backups

## TL:DR for Golden backup

- InkHUD: Settings → Node Config → Backup/Restore
- Over devices: Use python script → golden_backup.py /dev/XXX

### Via InkHUD Menu (Device UI)

```
Settings → Node Config → Backup/Restore
├── Auto Backup    → Creates auto_backup.proto (with rotation)
└── User Backup    → Creates user_backup.proto (golden snapshot)
```

### Via Python API (Remote)

```python
import meshtastic
import meshtastic.serial_interface
from meshtastic import admin_pb2, portnums_pb2

# Connect
interface = meshtastic.serial_interface.SerialInterface('/dev/cu.usbmodem1301')

# Create admin message
admin = admin_pb2.AdminMessage()

# For AUTO backup (FLASH location):
admin.backup_preferences = admin_pb2.AdminMessage.BackupLocation.FLASH

# For GOLDEN backup (SD location):
admin.backup_preferences = admin_pb2.AdminMessage.BackupLocation.SD

# Send
interface.sendData(
    admin.SerializeToString(),
    portNum=portnums_pb2.PortNum.ADMIN_APP,
    wantAck=True
)

interface.close()
```

### Via Meshtastic CLI

> Note: CLI `--backup` command not yet available in released versions.
> Use Python API above or build CLI from source.

---

## Restoring Backups

### Via InkHUD Menu

```
Settings → Node Config → Backup/Restore → Restore Settings
```

Restore priority:
1. `auto_backup.proto` (newest)
2. `auto_backup_prev.proto` (fallback)
3. `user_backup.proto` (golden)
4. `backup.proto` (legacy)

Device reboots after successful restore.

### Via Python API

```python
import meshtastic
import meshtastic.serial_interface
from meshtastic import admin_pb2, portnums_pb2

interface = meshtastic.serial_interface.SerialInterface('/dev/cu.usbmodem1301')

admin = admin_pb2.AdminMessage()

# Restore from auto backup chain (FLASH):
admin.restore_preferences = admin_pb2.AdminMessage.BackupLocation.FLASH

# Or restore from golden backup only (SD):
admin.restore_preferences = admin_pb2.AdminMessage.BackupLocation.SD

interface.sendData(
    admin.SerializeToString(),
    portNum=portnums_pb2.PortNum.ADMIN_APP,
    wantAck=True
)

interface.close()
```

---

## Recommended Workflow

### Initial Setup
1. Configure device completely (channels, settings, owner)
2. Test that everything works
3. Create **Golden Backup** via menu or Python API
4. This snapshot can restore device to working state anytime

### Regular Use
- Auto backup created on each graceful shutdown
- No action needed - rotation preserves history

### After Major Changes
1. Verify new configuration works
2. Create new **Golden Backup**
3. Old golden is overwritten - this is intentional

### Recovery Scenarios

**Corrupted config after update:**
```
Restore Settings → Uses auto_backup (most recent)
```

**Bad config change, shutdown happened:**
```
Restore Settings → Falls back to auto_backup_prev
```

**Everything broken, need factory-like reset:**
```python
# Restore from golden backup
admin.restore_preferences = admin_pb2.AdminMessage.BackupLocation.SD
```

---

## Deleting Backups

### Via Python API

```python
admin = admin_pb2.AdminMessage()

# Delete auto backups:
admin.remove_backup_preferences = admin_pb2.AdminMessage.BackupLocation.FLASH

# Delete golden backup:
admin.remove_backup_preferences = admin_pb2.AdminMessage.BackupLocation.SD

interface.sendData(admin.SerializeToString(), portNum=67, wantAck=True)
```

---

## Troubleshooting

### Check backup files exist
Look in boot logs:
```
DEBUG | backups (directory)
DEBUG |    auto_backup.proto (566 Bytes)
DEBUG |    user_backup.proto (566 Bytes)
```

### Backup command sent but no file created
- Check device has filesystem (FSCom)
- Check `/backups/` directory exists
- Look for ERROR in logs

### Restore doesn't change anything
- Verify backup file exists
- Check backup version matches device version
- Look for "No backup files found" warning

---

## Golden Backup Script

Save as `golden_backup.py`:

```python
#!/usr/bin/env python3
"""Create golden backup on Meshtastic device."""

import sys
import meshtastic
import meshtastic.serial_interface
from meshtastic import admin_pb2, portnums_pb2

def create_golden_backup(port='/dev/cu.usbmodem1301'):
    try:
        interface = meshtastic.serial_interface.SerialInterface(port)
        print(f"Connected to node {interface.myInfo.my_node_num}")

        admin = admin_pb2.AdminMessage()
        admin.backup_preferences = admin_pb2.AdminMessage.BackupLocation.SD

        interface.sendData(
            admin.SerializeToString(),
            portNum=portnums_pb2.PortNum.ADMIN_APP,
            wantAck=True
        )
        print("Golden backup command sent")

        import time
        time.sleep(2)
        interface.close()
        print("Done - reboot device to verify in logs")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/cu.usbmodem1301'
    create_golden_backup(port)
```

Usage example:
```bash
# Find port
ls /dev/cu.usb*

# Create golden backup
python3 golden_backup.py /dev/cu.usbmodem1301
```
