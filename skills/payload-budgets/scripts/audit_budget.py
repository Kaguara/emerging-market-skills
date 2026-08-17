#!/usr/bin/env python3
"""Audit a codebase against the payload-budgets rules.

    python3 skills/payload-budgets/scripts/audit_budget.py ~/code/my-app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from audit_lib import Check, iter_files, run, scan  # noqa: E402

WEB = (".ts", ".tsx", ".js", ".jsx")
STYLE = (".css", ".scss")

CHECKS = [
    Check(
        rule="SIZE-005",
        severity="warning",
        message="Image with no explicit quality or sizes. Framework defaults are "
                "tuned for retina on broadband; at thumbnail size the difference "
                "is invisible and roughly double the bytes.",
        pattern=r"<(Image|img)\b",
        extensions=WEB,
        unless_nearby=r"quality=|sizes=|srcSet|srcset",
        window=8,
    ),
    Check(
        rule="SIZE-009",
        severity="warning",
        message="Font loaded with no font-display. A hung font request blocks text "
                "from rendering at all.",
        pattern=r"@font-face|fonts\.googleapis|\.woff2?",
        extensions=STYLE + WEB,
        unless_nearby=r"font-display|display:\s*['\"]?swap",
        window=10,
    ),
    Check(
        rule="SIZE-007",
        severity="advisory",
        message="Third-party script. Confirm it has a named owner and a measured "
                "byte cost — untracked third-party bytes are where budgets die.",
        pattern=r"(?i)googletagmanager|hotjar|intercom|segment\.com|fullstory|mixpanel",
        extensions=WEB + (".html",),
    ),
]


def check_budget_file(root: Path) -> int:
    """SIZE-001 and SIZE-003 are about a file existing and being enforced."""
    candidates = list(root.glob("budgets.json")) + list(root.glob("*/budgets.json"))
    if candidates:
        print("[SIZE-001] ok · found {}".format(candidates[0].relative_to(root)))
        enforced = any(
            "budget" in p.read_text(encoding="utf-8", errors="replace").lower()
            for p in iter_files(root, (".yml", ".yaml"))
            if ".github" in p.parts
        )
        if enforced:
            print("[SIZE-003] ok · a workflow references the budget")
        else:
            print("[SIZE-003] critical · budgets.json exists but no workflow "
                  "references it. A budget no machine checks does not exist.")
            return 1
        print()
        return 0

    print("[SIZE-001] critical · no budgets.json found.")
    print("  Declare the numbers before writing the feature — initial download,")
    print("  first-load JavaScript, largest image. A budget set after the code")
    print("  exists is not a budget, it is a description.")
    print()
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: audit_budget.py <path-to-your-repo>")

    target = Path(sys.argv[1]).expanduser().resolve()
    if not target.is_dir():
        sys.exit("Not a directory: {}".format(target))

    print("payload-budgets — audited {}".format(target))
    print()
    critical = check_budget_file(target)

    findings = scan(target, CHECKS)
    for finding in findings:
        try:
            shown = finding.path.relative_to(target)
        except ValueError:
            shown = finding.path
        print("[{}] {} · {}:{}".format(finding.rule, finding.severity, shown, finding.line))
        print("  {}".format(finding.message))
        print("  > {}".format(finding.excerpt))
        print()

    print("{} pattern hit(s). Static checks find structure; measure the cold-cache "
          "first visit on a tier C device for the truth.".format(len(findings)))

    if critical:
        sys.exit(1)
