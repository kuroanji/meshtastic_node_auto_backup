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
