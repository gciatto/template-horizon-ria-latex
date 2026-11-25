#!/usr/bin/env python3
"""Count literal UTF-8 characters, including spaces and line-ending characters."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="plain text to be pasted into a portal field")
    parser.add_argument("--limit", type=int, help="field-specific maximum, including whitespace")
    parser.add_argument("--json", action="store_true", help="print machine-readable counts")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 0:
        parser.error("--limit cannot be negative")
    try:
        # Bytes.decode preserves CRLF exactly; read_text would normalise it.
        text = args.file.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        print(f"Cannot read UTF-8 text: {error}", file=sys.stderr)
        return 2
    count = len(text)
    exceeded = args.limit is not None and count > args.limit
    result = {"file": str(args.file), "characters_with_whitespace": count,
              "characters_without_whitespace": sum(not c.isspace() for c in text),
              "limit": args.limit, "exceeded": exceeded,
              "unit": "Unicode code points; no newline normalisation"}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        suffix = "" if args.limit is None else f" / {args.limit}"
        print(f"{args.file}: {count}{suffix} characters including whitespace"
              + (" — exceeds limit" if exceeded else ""))
    return 1 if exceeded else 0


if __name__ == "__main__":
    raise SystemExit(main())
