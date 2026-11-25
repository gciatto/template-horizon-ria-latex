#!/usr/bin/env python3
"""Emit the UTC release version YYYY.MM.DD-HH-MM; VERSION overrides the clock."""
from datetime import datetime, timezone
import os
import re
import sys


def validate_version(value):
    if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}-\d{2}-\d{2}", value):
        raise ValueError("VERSION must have the form YYYY.MM.DD-HH-MM")
    datetime.strptime(value, "%Y.%m.%d-%H-%M")
    return value


def release_version():
    supplied = os.environ.get("VERSION", "")
    return validate_version(supplied) if supplied else datetime.now(timezone.utc).strftime("%Y.%m.%d-%H-%M")


if __name__ == "__main__":
    try:
        print(release_version())
    except ValueError as error:
        print(f"Invalid release version: {error}", file=sys.stderr)
        raise SystemExit(2)
