#!/usr/bin/env python3
"""Count all PDF pages and extracted characters; optionally enforce page/A4 rules."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def poppler(command):
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False, env=environment)
    except OSError as error:
        raise ValueError(f"Cannot run {command[0]}: {error}") from error
    if result.returncode:
        reason = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"{command[0]} failed: {reason}")
    return result.stdout.decode("utf-8")


def inspect_pdf(pdf):
    if not pdf.is_file():
        raise ValueError(f"PDF does not exist: {pdf}")
    info = poppler(["pdfinfo", str(pdf.resolve())])
    match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if match is None or int(match.group(1)) < 1:
        raise ValueError("pdfinfo did not report a positive page count")
    pages = int(match.group(1))
    sizes = poppler(["pdfinfo", "-f", "1", "-l", str(pages), str(pdf.resolve())])
    dimensions = re.findall(r"^Page\s+(\d+)\s+size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts", sizes, re.MULTILINE)
    if len(dimensions) != pages:
        raise ValueError("pdfinfo did not report dimensions for every page")
    # Poppler rounds point values; 0.75 bp is only 0.265 mm.
    non_a4 = []
    for index, width, height in dimensions:
        short, long = sorted((float(width), float(height)))
        if abs(short - 595.2756) > 0.75 or abs(long - 841.8898) > 0.75:
            non_a4.append(int(index))
    text = poppler(["pdftotext", "-enc", "UTF-8", "-eol", "unix", "-nopgbrk", str(pdf.resolve()), "-"])
    return {"pdf": str(pdf), "pages": pages,
            "characters_with_whitespace": len(text),
            "characters_without_whitespace": sum(not c.isspace() for c in text),
            "non_a4_pages": non_a4,
            "character_count_note": "Diagnostic PDF text extraction; includes headers, footers and references. No global Part B character cap."}


def read_metadata(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read build metadata {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("Build metadata must be a JSON object")
    if value.get("funding") not in ("standard", "lump-sum"):
        raise ValueError("Build metadata funding must be standard or lump-sum")
    if type(value.get("page_limit")) is not int or value["page_limit"] < 1:
        raise ValueError("Build metadata page_limit must be a positive integer")
    if type(value.get("guidance")) is not int or value["guidance"] not in (0, 1):
        raise ValueError("Build metadata guidance must be 0 or 1")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--metadata", type=Path, help="defaults to the PDF name with .hemeta extension")
    parser.add_argument("--check", action="store_true", help="fail for excess pages, non-A4 pages or enabled guidance")
    parser.add_argument("--json", type=Path, help="also write a JSON report")
    args = parser.parse_args()
    try:
        report = inspect_pdf(args.pdf)
        report.update(read_metadata(args.metadata or args.pdf.with_suffix(".hemeta")))
        failures = []
        if report["pages"] > report["page_limit"]:
            failures.append(f"page count exceeds the configured {report['page_limit']}-page limit")
        if report["non_a4_pages"]:
            failures.append("non-A4 pages: " + ", ".join(map(str, report["non_a4_pages"])))
        if report["guidance"]:
            failures.append("guidance is enabled; run this check on the submission build")
        report["check_failures"] = failures
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, UnicodeError) as error:
        print(f"Cannot inspect proposal: {error}", file=sys.stderr)
        return 2
    print(f"Pages: {report['pages']} / {report['page_limit']} ({report['funding']}; all pages including references)")
    print(f"Extracted characters: {report['characters_with_whitespace']} including whitespace; "
          f"{report['characters_without_whitespace']} excluding whitespace")
    print("Character counts are diagnostic; Part B has no general character limit.")
    if args.check:
        for failure in failures:
            print(f"FAIL: {failure}")
        if not failures:
            print("PASS: configured page cap, A4 pages and guidance disabled.")
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
