#!/usr/bin/env python3
"""Validate every skill in skills/ against the spec in docs/AUTHORING.md.

Run with no arguments from anywhere in the repo:

    python3 tools/validate_skills.py

Exits 1 if any error is found. Warnings do not fail the build.
Requires Python 3.9+ and PyYAML.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Install it with: pip install -r requirements.txt")

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"
SOURCES_FILE = REPO / "docs" / "SOURCES.md"

SEVERITIES = {"critical", "warning", "advisory"}
KINDS = {"empirical", "process"}
TIERS = {"field", "published", "vendor"}
PLATFORMS = {"android", "ios", "web", "backend", "ussd", "sms"}
REQUIRED_RULE_FIELDS = ("id", "rule", "severity", "applies_to", "detect", "remedy")
REQUIRED_FRONTMATTER = ("name", "description", "license")

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RULE_ID_RE = re.compile(r"^([A-Z]+)-(\d{3})$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

MAX_DESCRIPTION = 1024
MAX_SKILL_LINES = 350


class Report:
    """Collects errors and warnings, grouped by the file they belong to."""

    def __init__(self) -> None:
        self.errors: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append((where, message))

    def warn(self, where: str, message: str) -> None:
        self.warnings.append((where, message))

    def print_and_exit(self, skill_count: int, rule_count: int) -> None:
        for where, message in self.warnings:
            print("warn  {}: {}".format(where, message))
        for where, message in self.errors:
            print("ERROR {}: {}".format(where, message))

        print()
        print("{} skills, {} rules checked.".format(skill_count, rule_count))
        if self.errors:
            print("{} error(s), {} warning(s). Failed.".format(
                len(self.errors), len(self.warnings)))
            sys.exit(1)
        print("{} warning(s). Passed.".format(len(self.warnings)))


SOURCE_STATUSES = {"unreachable-from-ci", "gone"}
STATUS_RE = re.compile(r"^Status:\s*([a-z-]+)\s+—")


def load_source_keys(report: Report) -> Tuple[Set[str], Set[str]]:
    """Citation keys are the `### key` headings in docs/SOURCES.md.

    Returns (all keys, keys marked `Status: gone`). A gone source is kept for
    the record but can no longer be the only thing holding up a critical rule.
    """
    if not SOURCES_FILE.exists():
        report.error("docs/SOURCES.md", "missing; published and vendor evidence cannot be resolved")
        return set(), set()
    keys: Set[str] = set()
    gone: Set[str] = set()
    current = ""
    for lineno, line in enumerate(SOURCES_FILE.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("### "):
            current = line[4:].strip()
            keys.add(current)
            continue
        match = STATUS_RE.match(line)
        if match and current:
            status = match.group(1)
            if status not in SOURCE_STATUSES:
                report.error("docs/SOURCES.md:{}".format(lineno),
                             "unknown status '{}'; use one of {}".format(
                                 status, ", ".join(sorted(SOURCE_STATUSES))))
            elif status == "gone":
                gone.add(current)
    return keys, gone


def parse_frontmatter(path: Path, report: Report) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        report.error(rel(path), "missing YAML frontmatter delimited by --- at the top of the file")
        return {}
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        report.error(rel(path), "frontmatter is not valid YAML: {}".format(exc))
        return {}
    if not isinstance(data, dict):
        report.error(rel(path), "frontmatter must be a mapping")
        return {}
    return data


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def check_frontmatter(path: Path, data: Dict[str, object], skill_dir: Path, report: Report) -> None:
    for field in REQUIRED_FRONTMATTER:
        if not data.get(field):
            report.error(rel(path), "frontmatter is missing required field '{}'".format(field))

    name = data.get("name")
    if isinstance(name, str):
        if name != skill_dir.name:
            report.error(rel(path), "frontmatter name '{}' does not match directory '{}'".format(
                name, skill_dir.name))
        if not SKILL_NAME_RE.match(name):
            report.error(rel(path), "name '{}' must be kebab-case".format(name))

    description = data.get("description")
    if isinstance(description, str):
        if len(description) > MAX_DESCRIPTION:
            report.error(rel(path), "description is {} chars, limit is {}".format(
                len(description), MAX_DESCRIPTION))
        if "use when" not in description.lower():
            report.warn(rel(path), "description should state when to invoke the skill "
                                   "(begin with 'Use when...'); it is the only text the "
                                   "model matches on")


def table_rule_ids(path: Path) -> Set[str]:
    """Rule IDs appearing in the markdown table in SKILL.md."""
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        first_cell = stripped.strip("|").split("|")[0].strip()
        if RULE_ID_RE.match(first_cell):
            found.add(first_cell)
    return found


def check_rules(
    skill_dir: Path,
    report: Report,
    seen_ids: Dict[str, str],
    seen_prefixes: Dict[str, str],
    source_keys: Set[str],
    gone_sources: Set[str],
) -> int:
    rules_path = skill_dir / "rules.yml"
    if not rules_path.exists():
        report.error(rel(skill_dir), "missing rules.yml")
        return 0

    try:
        doc = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.error(rel(rules_path), "not valid YAML: {}".format(exc))
        return 0

    if not isinstance(doc, dict):
        report.error(rel(rules_path), "must be a mapping with 'prefix' and 'rules'")
        return 0

    prefix = doc.get("prefix")
    if not isinstance(prefix, str) or not prefix.isupper():
        report.error(rel(rules_path), "'prefix' must be an uppercase string")
        return 0

    owner = seen_prefixes.get(prefix)
    if owner and owner != skill_dir.name:
        report.error(rel(rules_path), "prefix '{}' is already used by skill '{}'".format(prefix, owner))
    seen_prefixes[prefix] = skill_dir.name

    rules = doc.get("rules")
    if not isinstance(rules, list) or not rules:
        report.error(rel(rules_path), "'rules' must be a non-empty list")
        return 0

    file_ids: Set[str] = set()

    for index, rule in enumerate(rules):
        where = "{}[{}]".format(rel(rules_path), index)
        if not isinstance(rule, dict):
            report.error(where, "each rule must be a mapping")
            continue

        rule_id = rule.get("id")
        if isinstance(rule_id, str):
            where = "{} {}".format(rel(rules_path), rule_id)
            match = RULE_ID_RE.match(rule_id)
            if not match:
                report.error(where, "id must look like PREFIX-001")
            elif match.group(1) != prefix:
                report.error(where, "id prefix '{}' does not match file prefix '{}'".format(
                    match.group(1), prefix))
            if rule_id in seen_ids:
                report.error(where, "duplicate id, already defined in '{}'".format(seen_ids[rule_id]))
            seen_ids[rule_id] = skill_dir.name
            file_ids.add(rule_id)

        for field in REQUIRED_RULE_FIELDS:
            if not rule.get(field):
                report.error(where, "missing required field '{}'".format(field))

        severity = rule.get("severity")
        if severity is not None and severity not in SEVERITIES:
            report.error(where, "severity '{}' must be one of {}".format(
                severity, ", ".join(sorted(SEVERITIES))))

        applies_to = rule.get("applies_to")
        if isinstance(applies_to, list):
            for platform in applies_to:
                if platform not in PLATFORMS:
                    report.error(where, "applies_to '{}' must be one of {}".format(
                        platform, ", ".join(sorted(PLATFORMS))))
        elif applies_to is not None:
            report.error(where, "applies_to must be a list")

        kind = rule.get("kind", "empirical")
        if kind not in KINDS:
            report.error(where, "kind '{}' must be one of {}".format(
                kind, ", ".join(sorted(KINDS))))

        text = rule.get("rule")
        if isinstance(text, str) and len(text.split()) > 40:
            report.warn(where, "rule text is long; state it in one testable sentence")

        check_evidence(rule, severity, kind, where, report, source_keys, gone_sources)

    check_table_drift(skill_dir, file_ids, report)
    return len(rules)


def check_evidence(
    rule: Dict[str, object],
    severity: object,
    kind: object,
    where: str,
    report: Report,
    source_keys: Set[str],
    gone_sources: Set[str],
) -> None:
    evidence = rule.get("evidence")

    if not evidence:
        # Process rules govern how we work, not how the world behaves, so there is
        # nothing for them to cite. Empirical rules make a claim and must back it.
        if severity == "critical" and kind != "process":
            report.error(where, "critical rules require an evidence tag (see docs/EVIDENCE.md), "
                                "or 'kind: process' if the rule makes no empirical claim")
        return

    if kind == "process":
        report.warn(where, "process rules do not normally carry evidence; "
                           "consider 'kind: empirical'")

    live_sources = 0

    if not isinstance(evidence, list):
        report.error(where, "evidence must be a list")
        return

    for item in evidence:
        if not isinstance(item, dict):
            report.error(where, "each evidence entry must be a mapping")
            continue

        tier = item.get("tier")
        if tier not in TIERS:
            report.error(where, "evidence tier '{}' must be one of {}".format(
                tier, ", ".join(sorted(TIERS))))
            continue

        source = item.get("source")
        if not source:
            report.error(where, "evidence entry is missing 'source'")
            continue

        if tier == "field":
            live_sources += 1
            if not item.get("observation"):
                report.error(where, "field evidence requires an 'observation' stating what was seen")
            if "—" not in str(source) and "-" not in str(source):
                report.warn(where, "field source should name the product, market, and dates")
        else:
            if source not in source_keys:
                report.error(where, "evidence source '{}' has no '### {}' entry in "
                                    "docs/SOURCES.md".format(source, source))
            elif source in gone_sources:
                report.warn(where, "evidence source '{}' is marked gone in "
                                   "docs/SOURCES.md".format(source))
            else:
                live_sources += 1

    if severity == "critical" and live_sources == 0:
        report.error(where, "critical rule's only evidence is a source marked gone; "
                            "re-evidence it or lower the severity")


def check_table_drift(skill_dir: Path, rule_ids: Set[str], report: Report) -> None:
    """The rules table in SKILL.md must list exactly the IDs defined in rules.yml."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return

    in_prose = table_rule_ids(skill_md)

    missing = rule_ids - in_prose
    if missing:
        report.error(rel(skill_md), "rules table omits {}; prose and rules.yml must not drift".format(
            ", ".join(sorted(missing))))

    extra = in_prose - rule_ids
    if extra:
        report.error(rel(skill_md), "rules table lists {} which are not in rules.yml".format(
            ", ".join(sorted(extra))))


def check_length(skill_md: Path, report: Report) -> None:
    lines = len(skill_md.read_text(encoding="utf-8").splitlines())
    if lines > MAX_SKILL_LINES:
        report.warn(rel(skill_md), "{} lines exceeds the {}-line guideline; move detail into "
                                   "references/ so it loads on demand".format(lines, MAX_SKILL_LINES))


def main() -> None:
    report = Report()

    if not SKILLS_DIR.is_dir():
        sys.exit("No skills/ directory found at {}".format(SKILLS_DIR))

    source_keys, gone_sources = load_source_keys(report)
    seen_ids: Dict[str, str] = {}
    seen_prefixes: Dict[str, str] = {}
    rule_count = 0

    skill_dirs = sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))
    if not skill_dirs:
        sys.exit("No skills found in {}".format(SKILLS_DIR))

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            report.error(rel(skill_dir), "missing SKILL.md")
            continue

        data = parse_frontmatter(skill_md, report)
        if data:
            check_frontmatter(skill_md, data, skill_dir, report)
        check_length(skill_md, report)
        rule_count += check_rules(skill_dir, report, seen_ids, seen_prefixes,
                                  source_keys, gone_sources)

    report.print_and_exit(len(skill_dirs), rule_count)


if __name__ == "__main__":
    main()
