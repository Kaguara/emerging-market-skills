#!/usr/bin/env python3
"""Audit a codebase against the localization-and-literacy-ux rules.

    python3 skills/localization-and-literacy-ux/scripts/audit_i18n.py ~/code/my-app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from audit_lib import Check, run  # noqa: E402

WEB = (".ts", ".tsx", ".js", ".jsx")
STYLE = (".css", ".scss")
NATIVE = (".kt", ".java", ".swift", ".xml")

CHECKS = [
    Check(
        rule="LOC-001",
        severity="critical",
        message="Fixed height on an element that holds text. The English string "
                "fits; the translation does not, and the label is now unreadable.",
        pattern=r"(?<!min-)(?<!max-)height:\s*\d+(px|rem|em)|\bh-\[\d",
        extensions=STYLE + WEB,
    ),
    Check(
        rule="LOC-002",
        severity="critical",
        message="Sentence built by concatenation. Word order, plural categories, and "
                "gender vary in ways this cannot express — use a message formatter.",
        pattern=r"""["'][^"']*\s["']\s*\+\s*\w+|\+\s*\w+\s*\+\s*["']\s""",
        extensions=WEB,
        unless_nearby=r"(?i)className|classNames|clsx|path|url|import",
        window=3,
    ),
    Check(
        rule="LOC-003",
        severity="warning",
        message="Hand-rolled date or number formatting. Separators, grouping, and "
                "symbol position differ between markets that share a language.",
        pattern=r"""toFixed\(|\.split\(["']\/["']\)|getMonth\(\)\s*\+\s*1""",
        extensions=WEB,
        unless_nearby=r"(?i)Intl\.|toLocale",
        window=8,
    ),
    Check(
        rule="LOC-006",
        severity="warning",
        message="Directional CSS property. Use inline-start and inline-end so RTL "
                "works without a second layout.",
        pattern=r"(margin|padding|border)-(left|right):|(?<!\w)(left|right):\s*\d",
        extensions=STYLE,
    ),
    Check(
        rule="LOC-009",
        severity="warning",
        message="Split name fields. Excludes mononymous users and mis-sorts names "
                "where the family name comes first. Use one full-name field.",
        pattern=r"(?i)(first_?name|last_?name|surname|given_?name).*(required|\*)",
        extensions=WEB + NATIVE,
    ),
    Check(
        rule="LOC-005",
        severity="advisory",
        message="Interactive element that may carry meaning by icon alone. Confirm "
                "it has a visible text label, not only an accessible name.",
        pattern=r"<(button|a)\b(?![^>]*>\s*[A-Za-z])[^>]*>\s*<(svg|Icon|[A-Z]\w*Icon)",
        extensions=WEB,
    ),
]

if __name__ == "__main__":
    run("localization-and-literacy-ux", CHECKS, sys.argv)
