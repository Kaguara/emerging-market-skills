# Authoring a skill

This is the spec. Every skill in `skills/` conforms to it, and CI enforces the
mechanical parts. Read `skills/network-resilience/` alongside this — it is the
reference implementation.

## Anatomy

```
skills/<skill-name>/
├── SKILL.md          # required — entry file, loaded whenever the skill triggers
├── rules.yml         # required — deterministic thresholds
├── references/       # optional — loaded on demand, may be long
│   └── *.md
└── scripts/          # optional — runnable validators
    └── *.py
```

`<skill-name>` is kebab-case and must equal the `name` in frontmatter.

## SKILL.md

### Frontmatter

```yaml
---
name: network-resilience
description: Use when designing or reviewing any feature that makes a network call for users on intermittent, slow, or metered connections — offline queueing, retry and backoff, sync conflict handling, and graceful degradation. Covers mobile and web.
license: MIT
---
```

`description` is the only thing the model sees before deciding whether to load
the skill. Write it as a trigger condition, not a summary. Lead with "Use
when…". Under 1024 characters. Name the artifacts and vocabulary someone would
actually have in front of them — "retry", "offline", "sync", "2G" — because
that is what the match is made against.

### Body

Seven sections, in order. Cap the file at ~350 lines.

**1. The constraint.** Two or three sentences of physical reality. What is
actually true about the network, the device, the wallet, the hand holding the
phone. No preamble about the importance of emerging markets — the reader already
installed the skill.

**2. Hard rules.** A table mirroring `rules.yml`: ID, rule, severity. The
validator checks that this table and `rules.yml` contain exactly the same IDs.
Keep the wording identical too — copy it.

**3. Judgment.** Where the rules conflict, and how to choose. Offline-first
costs storage, which costs install size, which costs installs. Aggressive
caching costs staleness, which costs trust in a balance display. This section
is why the skill exists rather than a linter; a general model can guess the
rules but not the tradeoffs.

**4. Worked patterns.** Two to four implementations, with real code that
compiles. TypeScript/React/Next and Kotlin/Android are the house stacks. Each
pattern names the rule IDs it satisfies.

**5. Anti-patterns.** Things that look correct and are not. Each one names the
failure mode concretely — "the request succeeds, the user is charged twice",
not "this can cause issues".

**6. Verification.** How to prove the rule held. Point at the validator script
and at what to measure in production.

**7. Sources.** Rule IDs mapped to their evidence, and a link to
`docs/SOURCES.md` for published references.

## rules.yml

```yaml
prefix: NET
rules:
  - id: NET-001
    rule: Every state-changing request is queued locally before it is attempted.
    severity: critical          # critical | warning | advisory
    applies_to: [android, ios, web]
    detect: |
      Handler mutates server state without writing to a durable local queue first.
    remedy: |
      Write intent to local storage, return optimistic UI, drain the queue from a
      background worker (WorkManager on Android, Background Sync on web).
    evidence:
      - tier: field
        source: Juvo Mobile — 6 markets, Central & South America, 2015–2020
        observation: >
          Users on intermittent connections retried manually and duplicated
          transactions; queueing plus idempotency keys removed the class entirely.
```

Field reference:

| Field | Required | Notes |
|---|---|---|
| `id` | yes | `<PREFIX>-<3 digits>`, globally unique, never reused |
| `rule` | yes | One sentence, imperative, testable. No "should consider". |
| `severity` | yes | See below |
| `applies_to` | yes | Any of `android`, `ios`, `web`, `backend`, `ussd`, `sms` |
| `detect` | yes | What a reviewer or script looks for |
| `remedy` | yes | The specific fix, naming the framework where relevant |
| `kind` | no | `empirical` (default) or `process`. See below. |
| `evidence` | yes for `critical` | See `EVIDENCE.md` |
| `superseded_by` | no | Set when a rule is replaced; never delete a rule |

### Kind

Almost every rule is `empirical`: it claims something about how devices,
networks, or people behave, and must be able to back that claim.

`kind: process` is for rules that govern how we work rather than how the world
behaves — the rules in `emerging-market-review` about establishing the target
before reviewing, or citing a rule ID with every finding. They make no empirical
claim, so there is nothing for them to cite, and they are exempt from the
evidence requirement on `critical`.

Do not reach for `process` to get a rule past the validator. If the rule asserts
that something is true of users or devices, it is empirical, and the honest move
when you cannot source it is `warning` with a `TODO` explaining what evidence
would promote it.

### Severity

- `critical` — the product does not work for the target user. Ship-blocking.
  Requires an evidence tag.
- `warning` — measurable degradation for a meaningful share of users.
- `advisory` — a better default; reasonable teams may decline.

Be sparing with `critical`. A file where everything is critical gets ignored
wholesale the first time one of them is wrong.

## Writing style

Match the register of `frontend-design`: direct, second person, opinionated,
free of hedging. The reader is a competent engineer who has not worked in these
markets. Assume competence, not context.

Concrete beats general every time. "A 12MB APK download fails more often than
it completes on a congested 3G cell, and it is the first thing deleted when
storage fills" carries the rule. "Optimize for low-bandwidth environments" does
not, and the model will ignore it.

Never write a number you cannot source. If a threshold is a judgment call, say
so in the prose and give it `advisory` severity.

## Validation

```bash
python3 tools/validate_skills.py
```

Runs in CI on every PR. It checks frontmatter, the rules schema, ID uniqueness
and prefixing, evidence on critical rules, prose/rules table drift, and source
key resolution. Fix locally before opening a PR.
