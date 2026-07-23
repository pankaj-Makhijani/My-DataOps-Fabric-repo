#!/usr/bin/env python3
"""
Detect hardcoded workspace and lakehouse references in Fabric notebooks.

An absolute path that names a workspace or a GUID is carried unchanged when an
item is promoted between environments. The notebook then continues to read from
the source environment, which is not visible in the item itself.

Exit code 0 = clean, 1 = findings.
Use --warn to always exit 0 while still reporting.
"""

import argparse
import re
import sys
from pathlib import Path

# abfss://<container>@onelake.dfs.fabric.microsoft.com/...
ABFSS = re.compile(r"abfss://[^\s\"')]+", re.IGNORECASE)

# a bare GUID, which in a path is almost always a workspace or item id
GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

# workspace names look like this in our tenant
WORKSPACE_NAME = re.compile(
    r"\b[\w-]*(?:DEV|TEST|QA|UAT|PROD)[\w-]*Workspace\b", re.IGNORECASE
)

NOTEBOOK_SUFFIXES = {".py", ".ipynb"}

# Paths that are relative to the attached lakehouse are fine.
SAFE_HINTS = ("/lakehouse/default/", "Files/", "Tables/")


def is_notebook(path: Path) -> bool:
    return path.suffix.lower() in NOTEBOOK_SUFFIXES


def scan_file(path: Path):
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"  ! could not read {path}: {exc}", file=sys.stderr)
        return findings

    for lineno, line in enumerate(lines, 1):
        for match in ABFSS.finditer(line):
            snippet = match.group(0)
            reason = "absolute abfss path"
            if GUID.search(snippet):
                reason = "absolute abfss path containing a GUID"
            elif WORKSPACE_NAME.search(snippet):
                reason = "absolute abfss path naming a workspace"
            findings.append((lineno, reason, snippet[:110]))

        # a workspace name outside an abfss path is still environment specific
        if not ABFSS.search(line):
            ws = WORKSPACE_NAME.search(line)
            if ws and not any(h in line for h in SAFE_HINTS):
                findings.append(
                    (lineno, "workspace name referenced directly", ws.group(0))
                )

    return findings


def collect(paths):
    out = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out.extend(f for f in p.rglob("*") if f.is_file() and is_notebook(f))
        elif p.is_file() and is_notebook(p):
            out.append(p)
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=["."],
                    help="files or directories to scan")
    ap.add_argument("--warn", action="store_true",
                    help="report findings but always exit 0")
    args = ap.parse_args()

    files = collect(args.paths or ["."])
    if not files:
        print("No notebook files found to scan.")
        return 0

    print(f"Scanning {len(files)} notebook file(s) for hardcoded references\n")

    total = 0
    for f in files:
        findings = scan_file(f)
        if findings:
            print(f"{f}")
            for lineno, reason, snippet in findings:
                print(f"   line {lineno}: {reason}")
                print(f"      {snippet}")
            print()
            total += len(findings)

    if total:
        print(f"Found {total} hardcoded reference(s).")
        print("Reference lakehouses through the attached default context, for example")
        print("  spark.read.table('tbl_name')  or  /lakehouse/default/Files/...")
        print("instead of an absolute abfss path naming a workspace or GUID.")
        return 0 if args.warn else 1

    print("No hardcoded workspace or lakehouse references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
