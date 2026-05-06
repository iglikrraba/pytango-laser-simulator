#!/usr/bin/env python3
import os
import sys
from tango import Database, DbDevInfo


def main():
    device_name = os.environ.get("DEVICE_NAME", "laser/diag/1")
    class_name = os.environ.get("DEVICE_CLASS", "LaserDiagnostic")
    server_name = os.environ.get("DEVICE_SERVER", "laser_diag_ds/diag")
    host = os.environ.get("SIM_HOST", "127.0.0.1")
    port = os.environ.get("SIM_PORT", "10001")

    db = Database()
    info = DbDevInfo()
    info.name = device_name
    info._class = class_name
    info.server = server_name

    try:
        db.add_device(info)
        print(f"Added device {device_name} -> {class_name} ({server_name})")
    except Exception as exc:
        print(f"Add device: {exc}")

    props = {
        "host": [host],
        "port": [str(port)],
        "timeout": ["2.0"],
        "cache_ttl": ["0.2"],
    }
    try:
        db.put_device_property(device_name, props)
        print(f"Set properties for {device_name}: host={host}, port={port}")
    except Exception as exc:
        print(f"Set properties: {exc}")


if __name__ == "__main__":
    sys.exit(main())
