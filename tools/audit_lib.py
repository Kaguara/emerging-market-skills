#!/usr/bin/env python3
"""Shared machinery for the per-skill audit scripts.

Each skill's scripts/audit_*.py declares a list of Check objects and calls
run(). Everything else — walking the tree, skipping vendored directories,
formatting findings, exit codes — lives here.

These auditors are deliberately conservative and regex-based. They find
structure, not truth: a hit is a place worth reading, not a confirmed defect.
Every skill's Verification section says what to measure once these pass.

Design constraint: a contributor should be able to run these with Python and
nothing else installed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, NamedTuple, Optional, Sequence

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", ".next", "out",
    "__pycache__", ".venv", "venv", "coverage", ".gradle", "Pods",
}


class Check(NamedTuple):
    """One pattern to look for, tied to the rule it belongs to."""

    rule: str                      # "NET-003"
    severity: str                  # critical | warning | advisory
    message: str                   # what the hit means
    pattern: str                   # regex, applied per line
    extensions: Sequence[str]      # (".ts", ".tsx")
    # A hit is suppressed if this pattern appears in the surrounding window,
    # which is how we avoid flagging code that already does the right thing a
    # few lines below. Multi-line options objects are the common case.
    unless_nearby: Optional[str] = None
    window: int = 12


class Finding(NamedTuple):
    rule: str
    severity: str
    path: Path
    line: int
    message: str
    excerpt: str


SEVERITY_ORDER = {"critical": 0, "warning": 1, "advisory": 2}


def iter_files(root: Path, extensions: Iterable[str]) -> Iterable[Path]:
    exts = tuple(extensions)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in exts:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def scan(root: Path, checks: Sequence[Check]) -> List[Finding]:
    findings: List[Finding] = []

    by_ext: dict = {}
    for check in checks:
        for ext in check.extensions:
            by_ext.setdefault(ext, []).append(check)

    for path in iter_files(root, by_ext.keys()):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for check in by_ext.get(path.suffix, []):
            regex = re.compile(check.pattern)
            nearby = re.compile(check.unless_nearby) if check.unless_nearby else None

            for index, line in enumerate(lines):
                if not regex.search(line):
                    continue

                if nearby:
                    start = max(0, index - check.window)
                    end = min(len(lines), index + check.window + 1)
                    if any(nearby.search(l) for l in lines[start:end]):
                        continue

                findings.append(Finding(
                    rule=check.rule,
                    severity=check.severity,
                    path=path,
                    line=index + 1,
                    message=check.message,
                    excerpt=line.strip()[:120],
                ))

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.rule, str(f.path), f.line))
    return findings


def run(skill: str, checks: Sequence[Check], argv: Sequence[str]) -> None:
    if len(argv) < 2:
        sys.exit("usage: {} <path-to-your-repo>".format(Path(argv[0]).name))

    root = Path(argv[1]).expanduser().resolve()
    if not root.is_dir():
        sys.exit("Not a directory: {}".format(root))

    findings = scan(root, checks)

    print("{} — audited {}".format(skill, root))
    print()

    if not findings:
        print("No structural hits. That is not a pass — see the skill's")
        print("Verification section for what to measure on a real device.")
        return

    for finding in findings:
        try:
            shown = finding.path.relative_to(root)
        except ValueError:
            shown = finding.path
        print("[{}] {} · {}:{}".format(
            finding.rule, finding.severity, shown, finding.line))
        print("  {}".format(finding.message))
        print("  > {}".format(finding.excerpt))
        print()

    counts = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    summary = ", ".join("{} {}".format(counts[s], s)
                        for s in ("critical", "warning", "advisory") if s in counts)
    print("{} hit(s): {}".format(len(findings), summary))
    print()
    print("Each hit is a place to read, not a confirmed defect. Confirm before")
    print("reporting — see REVIEW-003 in skills/emerging-market-review.")

    # Exit non-zero only on critical hits, so these can gate CI without a
    # warning turning into a merge blocker.
    if counts.get("critical"):
        sys.exit(1)
