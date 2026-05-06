#!/usr/bin/env python3
import os
from tango import Database


def main():
    tango_host = os.environ.get("TANGO_HOST")
    if not tango_host:
        print("TANGO_HOST not set. Example: export TANGO_HOST=localhost:10000")
        return 1
    db = Database()
    if hasattr(db, "get_device_exported_list"):
        exported = db.get_device_exported_list("*")
    else:
        exported = db.get_device_exported("*")
    print("Exported devices:")
    for name in exported:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
