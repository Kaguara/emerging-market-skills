#!/usr/bin/env python3
"""Audit a codebase against the low-end-device-performance rules.

    python3 skills/low-end-device-performance/scripts/audit_perf.py ~/code/my-app
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from audit_lib import Check, run  # noqa: E402

WEB = (".ts", ".tsx", ".js", ".jsx")
NATIVE = (".kt", ".java", ".swift")

CHECKS = [
    Check(
        rule="PERF-003",
        severity="critical",
        message="Image loader with no memory-cache ceiling. Library defaults assume "
                "headroom this device does not have; the result is an OOM kill the "
                "user reads as the app closing itself.",
        pattern=r"(?i)ImageLoader|Glide\.with|Picasso\.get|Coil",
        extensions=NATIVE,
        unless_nearby=r"(?i)maxSize|memoryCache|maxSizePercent",
        window=20,
    ),
    Check(
        rule="PERF-002",
        severity="warning",
        message="ViewModel or multi-step state with no persistence. Backgrounding "
                "the app at tier C frequently kills the process; anything held only "
                "in memory is gone.",
        pattern=r"(?i)class\s+\w*ViewModel",
        extensions=NATIVE,
        unless_nearby=r"(?i)SavedStateHandle|onSaveInstanceState|persist|DataStore",
        window=25,
    ),
    Check(
        rule="PERF-005",
        severity="warning",
        message="Collection rendered without virtualisation. Memory should track the "
                "viewport, not the size of the result set.",
        pattern=r"\.map\((\w+)\s*=>\s*<|\.map\(\s*function",
        extensions=WEB,
        unless_nearby=r"(?i)virtual|windowed|FlatList|RecyclerView|react-window|slice\(",
        window=12,
    ),
    Check(
        rule="PERF-007",
        severity="warning",
        message="Polling or short-interval background work. Each wake activates the "
                "radio and draws from an ageing battery, for data nobody is reading.",
        pattern=r"setInterval\s*\(|PeriodicWorkRequest",
        extensions=WEB + NATIVE,
        unless_nearby=r"(?i)unmetered|charging|NetworkType|visibilitychange",
        window=15,
    ),
    Check(
        rule="PERF-008",
        severity="advisory",
        message="Animating a layout property. Width, height, top, and left force "
                "layout on every frame; transform and opacity do not.",
        pattern=r"transition:\s*(width|height|top|left|margin)|animate\(\{\s*(width|height|top|left)",
        extensions=WEB + (".css", ".scss"),
    ),
    Check(
        rule="PERF-009",
        severity="advisory",
        message="On-device inference with no fallback. Confirm there is a server or "
                "static path for devices that cannot carry the model.",
        pattern=r"(?i)tflite|onnxruntime|tensorflow|mlkit|ML Kit|CoreML",
        extensions=WEB + NATIVE,
        unless_nearby=r"(?i)fallback|catch|isAvailable|degrade",
        window=20,
    ),
]

if __name__ == "__main__":
    run("low-end-device-performance", CHECKS, sys.argv)
