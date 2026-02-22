# Meshtastic node Backup/Restore Implementation

### TL;DR

Prevents node settings reset on power failure/device instabilities

### Overview

This implementation adds a robust backup/restore system for Meshtastic node settings:

- `Auto backup` with rotation (survives interrupted writes)
- `Golden backup` (user-controlled snapshot of known-good state)
- `Auto backup` on shutdown
- `InkHUD menu UI` for manual backup/restore
- `Admin message support` for remote backup commands

### Implementation Guide: 

- Read `BACKUP_IMPLEMENTATION.md`

### HowTo: 

- Read `BACKUP_USAGE.md`

### Merge branch

https://github.com/kuroanji/firmware/tree/auto_backup
