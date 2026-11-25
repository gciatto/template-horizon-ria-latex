#!/usr/bin/env python3
"""Create a reproducible source ZIP and versioned compiled release assets."""
import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import shutil
import sys
import zipfile

from version import release_version, validate_version

EXCLUDED_DIRS = {".git", "build", "dist", "__pycache__", ".pytest_cache", ".venv", "venv", ".idea", ".vscode"}
EXCLUDED_SUFFIXES = {".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".hemeta", ".log", ".out", ".pyc", ".synctex.gz", ".toc"}


def source_file(path, root):
    relative = path.relative_to(root)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if path.is_symlink() or not path.is_file():
        return False
    if path.name in {".DS_Store", "Thumbs.db"} or path.name.endswith(("~", ".run.xml", ".synctex.gz")):
        return False
    if relative.as_posix() == "VERSION":
        return False  # Replaced with this archive's validated version below.
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if len(relative.parts) == 1 and path.suffix == ".pdf":
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", help="defaults to VERSION or the current UTC minute")
    parser.add_argument("--require-pdfs", action="store_true")
    args = parser.parse_args()
    try:
        version = validate_version(args.version) if args.version else release_version()
        root = args.root.resolve()
        if not (root / "part-b2.tex").is_file():
            raise ValueError("Project root must contain part-b2.tex")
        sources = sorted(p for p in root.rglob("*") if source_file(p, root))
        timestamp = datetime.strptime(version, "%Y.%m.%d-%H-%M").timetuple()[:6]
        if timestamp[0] < 1980:
            raise ValueError("ZIP release versions must be 1980 or later")
        pdfs = {"guidance": root / "build/guidance/part-b2-guidance.pdf",
                "part-b2": root / "build/submission/part-b2.pdf"}
        if args.require_pdfs and any(not path.is_file() for path in pdfs.values()):
            raise ValueError("Both compiled PDFs are required; run make all first")
        dist = root / "dist"
        dist.mkdir(exist_ok=True)
        archive_path = dist / f"he-ria26-{version}-source.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sources:
                info = zipfile.ZipInfo("he-ria26/" + path.relative_to(root).as_posix(), timestamp)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 << 16)
                archive.writestr(info, path.read_bytes())
            info = zipfile.ZipInfo("he-ria26/VERSION", timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            archive.writestr(info, version + "\n")
        outputs = [archive_path]
        for name, path in pdfs.items():
            if path.is_file():
                target = dist / f"he-ria26-{version}-{name}.pdf"
                shutil.copyfile(path, target)
                outputs.append(target)
        report = root / "build/counts.json"
        if report.is_file():
            target = dist / f"he-ria26-{version}-checks.json"
            shutil.copyfile(report, target)
            outputs.append(target)
        checksums = dist / f"he-ria26-{version}-SHA256SUMS.txt"
        checksums.write_text("".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in outputs), encoding="ascii")
        for path in [*outputs, checksums]:
            print(path)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Cannot package release: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
