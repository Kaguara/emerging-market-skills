#!/usr/bin/env python3
"""Audit a codebase against the identity-and-onboarding rules.

    python3 skills/identity-and-onboarding/scripts/audit_identity.py ~/code/my-app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from audit_lib import Check, run  # noqa: E402

WEB = (".ts", ".tsx", ".js", ".jsx", ".py", ".rb", ".go")
NATIVE = (".kt", ".java", ".swift")
SCHEMA = (".sql", ".prisma")

CHECKS = [
    Check(
        rule="IDN-001",
        severity="critical",
        message="Phone number used as a primary key or unique identity. Prepaid "
                "numbers are recycled and reassigned; the next holder should not "
                "inherit this account.",
        pattern=r"(?i)(phone|msisdn|mobile)(_?number)?\s+.*(primary key|unique)",
        extensions=SCHEMA + WEB,
    ),
    Check(
        rule="IDN-002",
        severity="critical",
        message="Identity or KYC lookup with no explicit deadline. Government ID "
                "authorities degrade without notice; an inherited default becomes "
                "an unbounded wait in your product.",
        pattern=r"(?i)(verify|kyc|identity|nid|bvn|nin|lookup).*(fetch|axios|request|client|post)",
        extensions=WEB,
        unless_nearby=r"(?i)timeout|AbortSignal|deadline",
        window=20,
    ),
    Check(
        rule="IDN-005",
        severity="warning",
        message="Capture upload with no on-device quality gate nearby. A round trip "
                "to learn the frame was too dark costs the user data and a retry.",
        pattern=r"(?i)(selfie|liveness|capture|document).*(upload|post|send)",
        extensions=WEB + NATIVE,
        unless_nearby=r"(?i)FaceDetection|mlkit|ML Kit|detector|luminance|quality",
        window=25,
    ),
    Check(
        rule="IDN-007",
        severity="warning",
        message="OTP flow with no alternate channel or delivery-state handling. SMS "
                "delivery is not reliable enough to be the only path into a product.",
        pattern=r"(?i)\botp\b|verification.?code|one.?time.?(code|password)",
        extensions=WEB + NATIVE,
        unless_nearby=r"(?i)fallback|alternate|voice|whatsapp|email|resend",
        window=20,
    ),
    Check(
        rule="IDN-010",
        severity="warning",
        message="Session or 'remember me' with no expiry. Handsets are commonly "
                "shared within a household.",
        pattern=r"(?i)(rememberMe|persistSession|maxAge:\s*(0|null)|expires:\s*null)",
        extensions=WEB,
        unless_nearby=r"(?i)expir|maxAge:\s*[1-9]|ttl",
        window=10,
    ),
]

if __name__ == "__main__":
    run("identity-and-onboarding", CHECKS, sys.argv)
