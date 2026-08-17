#!/usr/bin/env python3
"""Audit a codebase against the network-resilience rules.

    python3 skills/network-resilience/scripts/audit_handlers.py ~/code/my-app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from audit_lib import Check, run  # noqa: E402

WEB = (".ts", ".tsx", ".js", ".jsx")

CHECKS = [
    Check(
        rule="NET-003",
        severity="critical",
        message="State-changing request with no idempotency key. A user who retries "
                "an ambiguous timeout produces a duplicate the server cannot detect.",
        pattern=r"""method:\s*["']POST["']""",
        extensions=WEB,
        unless_nearby=r"(?i)idempoten",
    ),
    Check(
        rule="NET-005",
        severity="warning",
        message="fetch with no timeout. Library defaults assume broadband; on a "
                "congested cell this hangs until the user force-quits.",
        pattern=r"\bfetch\s*\(",
        extensions=WEB,
        # The options object spans lines, so look well past the call site before
        # concluding there is no timeout. This is the check that produced ten
        # false positives in examples/movietonight-audit.md.
        unless_nearby=r"AbortSignal\.timeout|signal:|timeout",
        window=20,
    ),
    Check(
        rule="NET-006",
        severity="warning",
        message="Retry with no jitter. Synchronised retries across clients on one "
                "congested cell reproduce the congestion that caused the failure.",
        pattern=r"(?i)\bretry|setTimeout\(.*retry",
        extensions=WEB,
        unless_nearby=r"(?i)jitter|Math\.random",
        window=15,
    ),
    Check(
        rule="NET-007",
        severity="warning",
        message="Branching on the connectivity flag alone. A depleted prepaid bundle "
                "reports online and answers every request with an operator portal.",
        pattern=r"navigator\.onLine",
        extensions=WEB,
        unless_nearby=r"(?i)ping|reachab|content-type",
    ),
    Check(
        rule="NET-008",
        severity="warning",
        message="Prefetch or autoplay with no data-saver check. This spends money "
                "from a prepaid bundle the user did not agree to spend.",
        pattern=r"(?i)\bprefetch\b|autoPlay|autoplay",
        extensions=WEB,
        unless_nearby=r"(?i)saveData|save-data|effectiveType|isActiveNetworkMetered",
        window=15,
    ),
]

if __name__ == "__main__":
    run("network-resilience", CHECKS, sys.argv)
