#!/usr/bin/env python3
"""Audit a codebase against the integration-cost-modeling rules.

    python3 skills/integration-cost-modeling/scripts/audit_costs.py ~/code/my-app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from audit_lib import Check, run  # noqa: E402

WEB = (".ts", ".tsx", ".js", ".jsx", ".py", ".rb", ".go")

CHECKS = [
    Check(
        rule="COST-003",
        severity="warning",
        message="Paid outbound send with no rate limit or cooldown nearby. An "
                "unthrottled send endpoint is a billing incident waiting to be found.",
        pattern=r"(?i)\b(sms|twilio|africastalking|messagebird|vonage)\b.*\.(send|create)|sendSms|send_sms",
        extensions=WEB,
        unless_nearby=r"(?i)rate.?limit|throttl|cooldown|redis|incr|cap\b",
        window=20,
    ),
    Check(
        rule="COST-004",
        severity="warning",
        message="Model call with no token ceiling. Token spend per session is "
                "unbounded by default, and a retry loop multiplies it.",
        pattern=r"(?i)(openai|anthropic|bedrock|vertex).*(complete|messages|responses|generate)",
        extensions=WEB,
        unless_nearby=r"(?i)max_tokens|max_output_tokens|maxTokens",
        window=25,
    ),
    Check(
        rule="COST-006",
        severity="warning",
        message="Paid third-party lookup with no cache. Verification and geocoding "
                "results are stable for months and are routinely re-purchased.",
        pattern=r"(?i)(geocod|verify|kyc|identity|enrich|lookup).*(fetch|axios|request|client)",
        extensions=WEB,
        unless_nearby=r"(?i)cache|redis|memo|ttl",
        window=20,
    ),
    Check(
        rule="COST-007",
        severity="advisory",
        message="Third-party call with no explicit failure decision. Decide "
                "fail-open or fail-closed in writing before an outage decides for you.",
        pattern=r"(?i)await\s+\w*(client|api|service)\.\w+\(",
        extensions=WEB,
        unless_nearby=r"(?i)try|catch|fallback|circuit|except",
        window=10,
    ),
]

if __name__ == "__main__":
    run("integration-cost-modeling", CHECKS, sys.argv)
