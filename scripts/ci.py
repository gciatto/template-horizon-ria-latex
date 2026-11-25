#!/usr/bin/env python3
"""Run independent CI checks, retain their logs, and render a GitHub summary."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    id: str
    name: str
    command: tuple[str, ...]
    depends_on: tuple[str, ...] = ()


def default_checks():
    return [
        Check("a-guidance", "Compile Part A with guidance", ("make", "guidance-a")),
        Check("b-guidance", "Compile Part B with guidance", ("make", "guidance-b2")),
        Check("a-clean", "Compile clean Part A", ("make", "submission-a")),
        Check("b-clean", "Compile clean Part B", ("make", "submission-b2")),
        Check("admin", "Administrative fields and character limits", ("make", "check-admin")),
        Check("budget", "Partner budgets and consortium totals", ("make", "check-budget")),
        Check("a-pdf", "Part A page size and guidance removal",
              (sys.executable, "scripts/count_pdf.py", "build/submission/part-a.pdf",
               "--check", "--json", "build/part-a-counts.json"), ("a-clean",)),
        Check("b-pdf", "Part B page limit, page size and guidance removal",
              (sys.executable, "scripts/count_pdf.py", "build/submission/part-b2.pdf",
               "--check", "--json", "build/counts.json"), ("b-clean",)),
        Check("tests", "Regression tests", ("make", "test")),
    ]


def write_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def run_checks(root, checks=None):
    root = Path(root).resolve()
    checks = default_checks() if checks is None else list(checks)
    directory = root / "build/ci"
    directory.mkdir(parents=True, exist_ok=True)
    ids = [check.id for check in checks]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r"[a-z0-9-]+", item) for item in ids):
        raise ValueError("Check IDs must be unique lowercase letters, numbers or hyphens")
    # A repeated local run must not display an old validation report as new evidence.
    for name in ("admin-checks.json", "budget-checks.json", "part-a-counts.json", "counts.json"):
        (root / "build" / name).unlink(missing_ok=True)
    data = {"started_at": datetime.now(timezone.utc).isoformat(), "completed": False,
            "checks": [{"id": check.id, "name": check.name, "status": "pending",
                        "command": list(check.command), "returncode": None,
                        "duration_seconds": 0, "log": f"build/ci/{check.id}.log"}
                       for check in checks]}
    results = directory / "results.json"
    write_json(results, data)
    statuses = {}
    for check, result in zip(checks, data["checks"]):
        blocked = [item for item in check.depends_on if statuses.get(item) != "passed"]
        if blocked:
            result.update(status="skipped", reason="Requires a successful check: " + ", ".join(blocked))
            (root / result["log"]).write_text(result["reason"] + "\n", encoding="utf-8")
        else:
            result["status"] = "running"
            write_json(results, data)
            started = time.monotonic()
            print(f"\n--- {check.name} ---", flush=True)
            with (root / result["log"]).open("w", encoding="utf-8") as log:
                log.write("$ " + shlex.join(check.command) + "\n\n")
                log.flush()
                try:
                    with subprocess.Popen(check.command, cwd=root, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                          errors="replace", bufsize=1) as process:
                        for line in process.stdout:
                            log.write(line)
                            log.flush()
                            print(line, end="", flush=True)
                        code = process.wait()
                except OSError as error:
                    code = 127
                    message = f"Cannot run check: {error}\n"
                    log.write(message)
                    print(message, end="", flush=True)
            result.update(status="passed" if code == 0 else "failed", returncode=code,
                          duration_seconds=round(time.monotonic() - started, 3))
        statuses[check.id] = result["status"]
        write_json(results, data)
    data["completed"] = True
    write_json(results, data)
    (directory / "summary.md").write_text(render_summary(root), encoding="utf-8")
    return 0 if checks and all(status == "passed" for status in statuses.values()) else 1


def md(value):
    text = html.escape(str(value)).replace("\r", " ").replace("\n", " ")
    text = text.replace("|", "&#124;")
    return re.sub(r"([\\`*_{}\[\]#+!])", r"\\\1", text)


def link(label, url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            return ""
    except ValueError:
        return ""
    return f"[{label}]({quote(url, safe='/:#?=&%+@')})"


def read_log(root, result):
    try:
        path = (root / result.get("log", "")).resolve()
        if not path.is_relative_to((root / "build/ci").resolve()):
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, TypeError):
        return ""


def check_detail(root, result):
    if result.get("reason"):
        return result["reason"]
    if result.get("status") == "failed":
        return f"Exit code {result.get('returncode', 'unknown')}"
    if result.get("status") != "passed":
        return "No completed result"
    reports = {"admin": "admin-checks.json", "budget": "budget-checks.json",
               "a-pdf": "part-a-counts.json", "b-pdf": "counts.json"}
    report = read_json(root / "build" / reports[result["id"]]) if result.get("id") in reports else {}
    if result.get("id") == "admin" and report:
        return (f"{report.get('fields_checked', 0)} fields; "
                f"{report.get('partners_checked', 0)} partner(s); "
                f"{len(report.get('incomplete', []))} unfinished items")
    if result.get("id") == "budget" and report:
        return f"{len(report.get('rows', []))} partner(s); {len(report.get('incomplete', []))} unfinished items"
    if "pages" in report:
        cap = report.get("page_limit")
        return f"{report['pages']} / {cap} pages" if cap is not None else f"{report['pages']} pages; no page cap"
    if result.get("id") == "tests":
        matches = re.findall(r"Ran (\d+) tests? in", read_log(root, result))
        if matches:
            return matches[-1] + " tests"
    return "Completed"


def render_summary(root, steps=None, env=None):
    root = Path(root).resolve()
    env = os.environ if env is None else env
    steps = {} if steps is None else steps
    data = read_json(root / "build/ci/results.json")
    checks = data.get("checks", [])
    checks = [item if isinstance(item, dict) else
              {"name": "Unreadable check result", "status": "invalid"}
              for item in checks] if isinstance(checks, list) else []
    passed = sum(item.get("status") == "passed" for item in checks)
    failed = sum(item.get("status") == "failed" for item in checks)
    skipped = sum(item.get("status") == "skipped" for item in checks)
    unfinished = len(checks) - passed - failed - skipped
    stage_failed = any(item.get("outcome") in ("failure", "cancelled")
                       for item in steps.values() if isinstance(item, dict))
    stage_incomplete = any(not isinstance(item, dict) or item.get("outcome") not in
                           ("success", "failure", "skipped", "cancelled") for item in steps.values())
    success = (bool(checks) and data.get("completed") is True and passed == len(checks)
               and not stage_failed and not stage_incomplete)
    heading = "✅ All checks passed" if success else "❌ Checks failed" if failed or stage_failed else "⚠️ Checks incomplete"
    lines = ["# Horizon Europe template — CI", "", f"## {heading}", "",
             f"**{passed} passed · {failed} failed · {skipped} skipped · {unfinished} incomplete**", ""]
    version = env.get("VERSION", "")
    ref = env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME", "")
    if version or ref:
        lines.extend([f"Version: **{md(version or 'unavailable')}** · Branch: **{md(ref or 'local')}**", ""])
    if not checks:
        lines.extend(["No check results are available. Inspect setup and workflow logs below.", ""])
    else:
        labels = {"passed": "✅ Passed", "failed": "❌ Failed", "skipped": "⏭️ Skipped",
                  "pending": "⏳ Not run", "running": "⚠️ Interrupted"}
        lines.extend(["| Check | Result | Time | Details |", "| --- | --- | ---: | --- |"])
        for item in checks:
            duration = item.get("duration_seconds", 0)
            duration = f"{duration:.1f}s" if isinstance(duration, (int, float)) else "—"
            lines.append(f"| {md(item.get('name', item.get('id', 'Unknown check')))} | "
                         f"{labels.get(item.get('status'), '⚠️ Incomplete')} | {duration} | "
                         f"{md(check_detail(root, item))} |")
        lines.extend(["", "Draft checks allow unfinished fields. `make strict` checks administrative completeness.", ""])
    stage_names = {"checkout": "Source checkout", "dependencies": "Build dependencies",
                   "version": "UTC version", "checks": "Build and validation checks",
                   "package": "Release packaging (master)", "pdfs": "PDF artifacts",
                   "release_assets": "Release assets (master)", "logs": "Logs and reports"}
    present = [(key, name) for key, name in stage_names.items() if key in steps]
    if present:
        labels = {"success": "✅ Passed", "failure": "❌ Failed", "skipped": "⏭️ Skipped",
                  "cancelled": "⚠️ Cancelled"}
        lines.extend(["## Workflow stages", "", "| Stage | Result |", "| --- | --- |"])
        for key, name in present:
            value = steps[key] if isinstance(steps[key], dict) else {}
            lines.append(f"| {name} | {labels.get(value.get('outcome'), '⚠️ Incomplete')} |")
        lines.append("")
    urls = [("PDFs", env.get("CI_PDF_URL", "")),
            ("Compilation logs and check reports", env.get("CI_LOGS_URL", "")),
            ("Validated release assets", env.get("CI_RELEASE_URL", ""))]
    if env.get("GITHUB_SERVER_URL") and env.get("GITHUB_REPOSITORY") and env.get("GITHUB_RUN_ID"):
        urls.append(("Full workflow logs", f"{env['GITHUB_SERVER_URL']}/{env['GITHUB_REPOSITORY']}/actions/runs/{env['GITHUB_RUN_ID']}"))
    links = [value for label, url in urls if (value := link(label, url))]
    if links:
        lines.extend(["## Downloads and logs", "", " · ".join(links), ""])
    for item in checks:
        if item.get("status") not in ("failed", "running"):
            continue
        tail = "\n".join(read_log(root, item).splitlines()[-60:])[-12000:]
        if tail:
            lines.extend(["<details>", f"<summary>{html.escape(str(item.get('name', 'Failed check')))} — log excerpt</summary>",
                          "", "<pre>" + html.escape(tail) + "</pre>", "", "</details>", ""])
    lines.extend(["Full command output is retained in `build/ci/*.log`; LaTeX/BibTeX logs are included in the logs artifact.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "summary"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.command == "run":
        return run_checks(args.root)
    try:
        steps = json.loads(os.environ.get("CI_STEPS_JSON", "{}"))
        if not isinstance(steps, dict):
            steps = {}
    except ValueError:
        steps = {}
    summary = render_summary(args.root, steps)
    path = args.root / "build/ci/summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary, encoding="utf-8")
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if destination:
        with Path(destination).open("a", encoding="utf-8") as stream:
            stream.write(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
