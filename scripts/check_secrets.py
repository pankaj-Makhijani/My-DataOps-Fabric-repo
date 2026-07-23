#!/usr/bin/env python3
"""
Detect credentials committed into notebook or configuration files.

Deliberately conservative. It looks for assignment of a secret-looking value to
a secret-looking name, and for a few well known token shapes. Anything that
reads as a placeholder or a Key Vault reference is ignored.

Exit code 0 = clean, 1 = findings.
Use --warn to always exit 0 while still reporting.
"""

import argparse
import re
import sys
from pathlib import Path

SCAN_SUFFIXES = {".py", ".ipynb", ".json", ".yml", ".yaml", ".sql", ".cfg", ".ini"}

SECRET_NAME = r"(?:password|passwd|pwd|secret|token|api[_-]?key|apikey|access[_-]?key|client[_-]?secret|conn(?:ection)?[_-]?string|sas[_-]?token)"

PATTERNS = [
    (re.compile(rf"{SECRET_NAME}\s*[=:]\s*[\"']([^\"']{{8,}})[\"']", re.I),
     "credential assigned in code"),
    (re.compile(r"AccountKey\s*=\s*[A-Za-z0-9+/=]{20,}", re.I),
     "storage account key in connection string"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}", re.I),
     "Slack token"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
     "GitHub token"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
     "private key"),
    (re.compile(r"\bpat\s*[=:]\s*[\"'][A-Za-z0-9]{20,}[\"']", re.I),
     "personal access token"),
]

# things that look like secrets but are not
IGNORE = re.compile(
    r"(your[_-]?|placeholder|example|dummy|sample|xxx+|\*\*\*+|<[^>]+>|"
    r"changeme|todo|fixme|redacted|\{\{|\$\(|os\.environ|getenv|"
    r"dbutils\.secrets|keyvault|key_vault|mssparkutils\.credentials)",
    re.I,
)


def scan_file(path: Path):
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings

    for lineno, line in enumerate(lines, 1):
        if IGNORE.search(line):
            continue
        for pattern, label in PATTERNS:
            m = pattern.search(line)
            if m:
                shown = line.strip()
                if len(shown) > 90:
                    shown = shown[:90] + "..."
                findings.append((lineno, label, shown))
                break
    return findings


def collect(paths):
    out = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out.extend(
                f for f in p.rglob("*")
                if f.is_file()
                and f.suffix.lower() in SCAN_SUFFIXES
                and ".git" not in f.parts
            )
        elif p.is_file() and p.suffix.lower() in SCAN_SUFFIXES:
            out.append(p)
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--warn", action="store_true")
    args = ap.parse_args()

    files = collect(args.paths or ["."])
    if not files:
        print("No files found to scan.")
        return 0

    print(f"Scanning {len(files)} file(s) for credentials\n")

    total = 0
    for f in files:
        findings = scan_file(f)
        if findings:
            print(f"{f}")
            for lineno, label, snippet in findings:
                print(f"   line {lineno}: {label}")
                print(f"      {snippet}")
            print()
            total += len(findings)

    if total:
        print(f"Found {total} possible credential(s).")
        print("Store credentials in Key Vault and retrieve them at runtime.")
        print("If this is a false positive, adjust scripts/check_secrets.py.")
        return 0 if args.warn else 1

    print("No credentials found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
