#!/usr/bin/env python3
import os
from tango import Database


def main():
    tango_host = os.environ.get("TANGO_HOST")
    if not tango_host:
        print("TANGO_HOST not set. Example: export TANGO_HOST=localhost:10000")
        return 1
    db = Database()
    devices = db.get_device_name("*", "*")
    print("Registered devices:")
    for name in devices:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
