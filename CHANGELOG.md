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
- `low-end-device-performance` PERF-010: test every bottom-anchored control
  with three-button navigation and the OEM skin of the reference device. Field
  evidence from Kenya, 2026: an edge-to-edge app whose custom tab bar sat under
  the system navigation bar on an OPPO A58 and was unreachable.
- `network-resilience` NET-012: never let a third party's connectivity probe
  decide whether the app may call your API. Field evidence from Kenya, 2026: an
  app that gated every request on NetInfo's Google-based reachability flag was
  dead on a network where its own API answered in a second.
- `network-resilience` NET-013: key every persisted cache to a confirmed
  account identity and fence it when the session ends. Field evidence from
  Kenya, 2026: a debounced cache write landed after logout, and a query client
  swapped without remounting kept serving the previous account's data.
- `network-resilience` NET-015: distinguish "no data yet" from "stale data" and
  label cached data with its age. Field evidence from Kenya, 2026: screens
  offline showed "No jobs yet" to users who had jobs.
- `identity-and-onboarding` IDN-011: never write credentials, identity
  documents, or payout details into an offline cache. Field evidence from
  Kenya, 2026: a default cache persister would have written KYC status, payout
  details and social access tokens to unencrypted device storage.
- `payload-budgets` SIZE-011: upload media on commit, not on selection, and
  cancel a superseded upload. Field evidence from Kenya, 2026: uploading at pick
  time charged every discarded take to a prepaid bundle and let a late response
  attach a replaced file.
- `localization-and-literacy-ux` LOC-011: render an unknown value as a
  placeholder, never as zero. Field evidence from Kenya, 2026: offline counters
  defaulting to zero read as lost earnings and lost work.

### Changed
- `network-resilience` NET-002 is amended: the rule now covers the decision
  itself — queue or refuse, decided per intent and enforced in one place —
  rather than only the queueing half. Refusing an offline write was always a
  legitimate answer for intents not worth replaying; what was missing was that
  it is a decision, and that it belongs in the transport layer. Second field
  observation added from Kenya, 2026: per-screen offline handling produced a
  stack of identical connectivity toasts on a cold start, and moving the refusal
  to one chokepoint reduced it to one message. No ID was issued for this; it is
  NET-002's scope, not a new rule.
- `network-resilience` NET-012 carries a second field observation: the corrected
  rule shipped and held on airplane mode, a tether, and congested mobile data.

## [0.1.0] — 2026-08-26

### Added
- `identity-and-onboarding`, covering SIM churn, designing around unreliable
  government ID authorities, status transparency as a trust surface, and
  skin-tone-stratified evaluation of biometric capture using the Monk Skin Tone
  scale.
- Audit scripts for every skill, on a shared `tools/audit_lib.py`.
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
- `money-movement` and `field-testing-and-telemetry` are referenced by the
  router but not yet written. Targeted for v0.2.0.
- Smile Identity attribution is dated 2017–2021 throughout; confirm the exact
  range before release.
