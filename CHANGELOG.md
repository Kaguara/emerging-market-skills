# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Rules are versioned along with the repo. A rule is never silently changed: it is
either amended in place with the change noted here, or superseded by a new ID
with `superseded_by` set on the old one. Anyone who cited a rule in a code review
should be able to find out what happened to it.

## [Unreleased]

### Added
- Six skills: `network-resilience`, `payload-budgets`,
  `low-end-device-performance`, `integration-cost-modeling`,
  `localization-and-literacy-ux`, and the `emerging-market-review` router.
- `tools/validate_skills.py` and `tools/rules.schema.json`, enforcing the
  authoring spec in CI.
- Evidence standard with three tiers (`field`, `published`, `vendor`) and
  device/network tiers A–D.
- Claude Code plugin marketplace manifest.

### Known gaps
- `COST-003` and `COST-004` are held at `warning` pending field evidence that
  would justify promoting them to `critical`. See the `TODO` markers in
  `skills/integration-cost-modeling/rules.yml`.
- Skills 7–9 (`money-movement`, `identity-and-onboarding`,
  `field-testing-and-telemetry`) are referenced by the router but not yet
  written. Targeted for v0.2.0.
