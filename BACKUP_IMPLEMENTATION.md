# Meshtastic Backup/Restore Implementation

## Overview

This implementation adds a robust backup/restore system for Meshtastic device preferences with:
- **Auto backup** with rotation (survives interrupted writes)
- **Golden backup** (user-controlled snapshot of known-good state)
- **Auto backup on shutdown** (Power.cpp integration)
- **InkHUD menu UI** for manual backup/restore
- **Admin message support** for remote backup commands

## Architecture

```
/backups/
├── auto_backup.proto       # Current auto backup (newest)
├── auto_backup_prev.proto  # Previous auto backup (rotation)
└── user_backup.proto       # Golden snapshot (user-controlled)
```

### Backup Priority (restore order):
1. `auto_backup.proto` - most recent auto backup
2. `auto_backup_prev.proto` - previous rotation (fallback)
3. `user_backup.proto` - golden snapshot (user fallback)
4. `backup.proto` - legacy format (migration)

### Location Mapping:
- `FLASH` = auto backup with rotation
- `SD` = user/golden backup (no rotation)

> Note: SD location is repurposed for golden backup. Actual SD card support is TODO in upstream.

---

## Modified Files

### Core Backup Logic

#### `src/mesh/NodeDB.h`
```cpp
// File paths
static constexpr const char *autoBackupFileName = "/backups/auto_backup.proto";
static constexpr const char *autoBackupPrevFileName = "/backups/auto_backup_prev.proto";
static constexpr const char *userBackupFileName = "/backups/user_backup.proto";

// Methods
bool backupPreferences(meshtastic_AdminMessage_BackupLocation location);
bool restorePreferences(meshtastic_AdminMessage_BackupLocation location,
                        int restoreWhat = SEGMENT_CONFIG | SEGMENT_MODULECONFIG |
                                          SEGMENT_DEVICESTATE | SEGMENT_CHANNELS);
```

#### `src/mesh/NodeDB.cpp`

**backupPreferences()** - Creates backup with rotation for FLASH, direct write for SD:
```cpp
bool NodeDB::backupPreferences(meshtastic_AdminMessage_BackupLocation location)
{
    // Prepare backup data (shared by both paths)
    meshtastic_BackupPreferences backup = meshtastic_BackupPreferences_init_zero;
    backup.version = DEVICESTATE_CUR_VER;
    backup.timestamp = getValidTime(RTCQuality::RTCQualityDevice, false);
    backup.config = config;
    backup.module_config = moduleConfig;
    backup.channels = channelFile;
    backup.owner = owner;

    if (location == meshtastic_AdminMessage_BackupLocation_FLASH) {
        // Rotation: delete prev -> rename current to prev -> write new
        FSCom.remove(autoBackupPrevFileName);
        FSCom.rename(autoBackupFileName, autoBackupPrevFileName);
        return saveProto(autoBackupFileName, ...);
    } else if (location == meshtastic_AdminMessage_BackupLocation_SD) {
        // Golden snapshot - no rotation
        return saveProto(userBackupFileName, ...);
    }
}
```

**restorePreferences()** - Cascading fallback through all backup files:
```cpp
bool NodeDB::restorePreferences(meshtastic_AdminMessage_BackupLocation location, int restoreWhat)
{
    if (location == FLASH) {
        // Try: auto_backup -> auto_backup_prev -> user_backup -> legacy
        // Restore requested segments (config, moduleConfig, channels, owner)
    } else if (location == SD) {
        // Restore from user_backup only
    }
}
```

### Auto Backup on Shutdown

#### `src/Power.cpp`
```cpp
void Power::shutdown()
{
    // ... existing shutdown code ...

    nodeDB->saveToDisk();

    // Create automatic backup on graceful shutdown
    if (nodeDB->backupPreferences(meshtastic_AdminMessage_BackupLocation_FLASH)) {
        LOG_INFO("Auto backup created on shutdown");
    }

    // ... continue shutdown ...
}
```

### Admin Module Support

#### `src/modules/AdminModule.cpp`
Handles remote backup/restore commands via admin messages:
- `backup_preferences` - Create backup (FLASH or SD location)
- `restore_preferences` - Restore from backup
- `remove_backup_preferences` - Delete backup file

### InkHUD Menu Integration

#### `src/graphics/niche/InkHUD/Applets/System/Menu/MenuPage.h`
```cpp
enum class MenuPage {
    // ...
    NODE_CONFIG_BACKUP,  // New page
    // ...
};
```

#### `src/graphics/niche/InkHUD/Applets/System/Menu/MenuAction.h`
```cpp
enum MenuAction {
    // ...
    // Backup / Restore
    BACKUP_AUTO,
    BACKUP_USER,
    RESTORE_PREFERENCES,
    // ...
};
```

#### `src/graphics/niche/InkHUD/Applets/System/Menu/MenuApplet.cpp`

Menu structure:
```
Node Config
└── Backup/Restore
    ├── Back
    ├── [Create Backup]
    │   ├── Auto Backup      → Creates auto_backup.proto with rotation
    │   └── User Backup      → Creates user_backup.proto (golden)
    ├── [Restore]
    │   └── Restore Settings → Restores from best available backup
    └── Exit
```

Action handlers:
```cpp
case BACKUP_AUTO:
    nodeDB->backupPreferences(meshtastic_AdminMessage_BackupLocation_FLASH);
    break;

case BACKUP_USER:
    nodeDB->backupPreferences(meshtastic_AdminMessage_BackupLocation_SD);
    break;

case RESTORE_PREFERENCES:
    InkHUD::getInstance()->notifyApplyingChanges();
    if (nodeDB->restorePreferences(meshtastic_AdminMessage_BackupLocation_FLASH)) {
        rebootAtMsec = millis() + DEFAULT_REBOOT_SECONDS * 1000;
    }
    break;
```

---

## File Summary

| File | Changes |
|------|---------|
| `src/mesh/NodeDB.h` | Added backup file paths, method signatures |
| `src/mesh/NodeDB.cpp` | Implemented backupPreferences(), restorePreferences() with rotation |
| `src/Power.cpp` | Added auto backup on shutdown |
| `src/modules/AdminModule.cpp` | SD location handling for user backup |
| `src/graphics/niche/InkHUD/.../MenuPage.h` | Added NODE_CONFIG_BACKUP |
| `src/graphics/niche/InkHUD/.../MenuAction.h` | Added BACKUP_AUTO, BACKUP_USER, RESTORE_PREFERENCES |
| `src/graphics/niche/InkHUD/.../MenuApplet.cpp` | Menu UI and action handlers |

---

## Verification

Boot logs should show backup files:
```
DEBUG | Filesystem files:
DEBUG |    backups (directory)
DEBUG |       auto_backup_prev.proto (566 Bytes)
DEBUG |       auto_backup.proto (566 Bytes)
DEBUG |       user_backup.proto (566 Bytes)
```
