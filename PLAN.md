# emerging-market-skills — build plan

Handoff document. Everything needed to scaffold and populate the repo.
Read `docs/AUTHORING.md` and `skills/network-resilience/` first — they are the
spec and the golden reference. Every other skill must match their shape.

- **Repo:** `github.com/kaguara/emerging-market-skills`
- **License:** MIT
- **Tagline:** Agent skills for building software that works on the other five billion phones.
- **Audience:** PMs and engineers using AI coding tools. Technical, build-focused.
  Not business model, not go-to-market, not market sizing.

---

## 1. The core design decision

Each skill is a **triple**, not a prose file:

| File | Purpose | Consumed by |
|---|---|---|
| `SKILL.md` | Judgment, tradeoffs, worked patterns. Prose. | The model, at reasoning time |
| `rules.yml` | Deterministic thresholds with severity, rationale, evidence | The validator, and cited by the prose |
| `scripts/*.py` | Runnable audit that reads `rules.yml` and checks a real artifact | CI, pre-commit, the model via Bash |

This is what makes the repo more than a prompt dump. `rules.yml` is the
connective tissue: the prose cites rule IDs, the validator enforces them, CI
tests them, contributors amend them. A rule that cannot be expressed in
`rules.yml` with a severity and a piece of evidence is taste, not a rule — put
it in the prose and say so.

The attached Google YAML got this half-right (deterministic validations) and the
`frontend-design` skill got the other half right (judgment as prose). We ship both.

---

## 2. Repository layout

```
emerging-market-skills/
├── README.md                       # see §5
├── LICENSE                         # MIT, © Antony Kaguara
├── CONTRIBUTING.md                 # see §6 — the evidence bar is the whole point
├── CODE_OF_CONDUCT.md              # Contributor Covenant 2.1, verbatim
├── SECURITY.md                     # short: no runtime, report via GH advisories
├── CHANGELOG.md                    # Keep a Changelog format
├── CITATION.cff                    # so researchers can cite it
├── requirements.txt                # pyyaml only
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── skill-proposal.yml
│   │   ├── field-report.yml        # "rule NET-003 did not hold in Pakistan"
│   │   ├── rule-change.yml
│   │   └── config.yml              # contact_links → Discussions
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── validate.yml            # runs tools/validate_skills.py on every PR
│       └── release.yml             # tag → GitHub Release + bundle.zip of skills/
├── .claude-plugin/
│   └── marketplace.json            # one-command install in Claude Code
├── docs/
│   ├── AUTHORING.md                # the skill spec — WRITTEN, use as-is
│   ├── EVIDENCE.md                 # evidence tiers and how to tag
│   ├── INSTALL.md                  # per-tool install instructions
│   └── SOURCES.md                  # bibliography, one entry per external claim
├── skills/
│   ├── emerging-market-review/     # router + audit entry point
│   ├── network-resilience/         # WRITTEN — golden reference
│   ├── payload-budgets/
│   ├── low-end-device-performance/
│   ├── integration-cost-modeling/
│   ├── localization-and-literacy-ux/
│   ├── money-movement/
│   ├── identity-and-onboarding/
│   └── field-testing-and-telemetry/
├── examples/
│   └── movietonight-audit.md       # worked audit of a real Next.js product
└── tools/
    ├── validate_skills.py          # frontmatter + rules schema + ID uniqueness
    └── rules.schema.json           # JSON Schema for rules.yml
```

---

## 3. The nine skills

Build in this order. Ship v0.1 when 1–6 are done; 7–9 land in v0.2 within two
weeks of launch. Skills 7–9 are where the unusual expertise lives — they are the
reason someone stars the repo instead of skimming it — so do not let them slip
further than that.

| # | Skill | ID prefix | What it must answer | Validator input |
|---|---|---|---|---|
| 1 | `network-resilience` | `NET` | What happens when the network is absent, slow, lying, or metered? | route/handler manifest, service-worker config |
| 2 | `payload-budgets` | `SIZE` | How many bytes before a user on 2G abandons? | `stats.json`, `.apk`/`.aab`, `package.json` |
| 3 | `low-end-device-performance` | `PERF` | Does it run on 2GB RAM, 4-year-old silicon, a hot battery? | Lighthouse JSON, device-tier matrix |
| 4 | `integration-cost-modeling` | `COST` | What does one user-action cost in SMS/USSD/data/LLM tokens? | a spec + a declared unit-economics table |
| 5 | `localization-and-literacy-ux` | `LOC` | Does the UI survive +40% text expansion, RTL, and low literacy? | i18n bundles, component source |
| 6 | `emerging-market-review` | `REVIEW` | Router. Audits a PR/spec, dispatches to 1–5, 7–9, ranks findings. | any of the above |
| 7 | `money-movement` | `PAY` | Mobile money, idempotency, reconciliation, timeouts, reversals. | payment handler source, webhook config |
| 8 | `identity-and-onboarding` | `IDN` | Phone-as-identity, SIM churn, shared devices, OTP deliverability. | auth flow source |
| 9 | `field-testing-and-telemetry` | `OBS` | How do you *prove* any of the above in production? | analytics event schema |

### Per-skill content requirements

Each `SKILL.md` must contain, in this order:

1. **Frontmatter** — `name`, `description`, `license`. Description must state
   *when to invoke*, not what the skill contains; that is what the model matches on.
2. **The constraint** — two sentences on the physical reality being designed
   around. No throat-clearing about how important emerging markets are.
3. **Hard rules** — a table of the `rules.yml` entries with severity. The prose
   table and `rules.yml` must not drift; the validator checks this.
4. **Judgment** — where the rules conflict and how to trade them off. This is
   the section a generic model cannot write, and the reason the skill exists.
5. **Worked patterns** — 2–4 concrete implementations with code. Real code that
   compiles, in the stack the audience uses (TypeScript/React/Next, Kotlin/Android).
6. **Anti-patterns** — what looks correct and is not, with the failure mode named.
7. **Verification** — how to check the rule held, referencing the validator script.

Cap `SKILL.md` at ~350 lines. Overflow goes to `references/` and is loaded on
demand — that is the whole point of progressive disclosure. Reference files may
be long; the entry file may not.

---

## 4. Evidence standard

Three tiers, tagged on every rule in `rules.yml`:

- `field` — observed in a product you shipped. Requires market, rough date range,
  and the observed effect. Highest weight. This is the repo's moat.
- `published` — GSMA, CGAP, Google NBU, McKinsey, academic. Requires a
  `docs/SOURCES.md` entry with URL and access date.
- `vendor` — platform documentation (Android, Chrome, Cloudflare). Requires URL.

A rule with no evidence tag cannot be `severity: critical`. Enforced by the validator.

Antony's field evidence, drawn from the CV — use these attributions, do not invent others:

| Attribution string | Context available |
|---|---|
| `Juvo Mobile — 6 markets, Central & South America, 2015–2020` | Telecom-data credit risk, >$200M processed, 20M registered / 5M MAU, Android+iOS+Web across 6 markets |
| `Smile Identity — pan-African, 2017–2020` | KYC/identity SDKs on Android, iOS, Web; 200M+ identities under coverage |
| `gethomespace — Kenya/US, 2020–2022` | Background checks for informal workers; 2 Android apps, web portal, SMS chat engine, data API |
| `IBM Research Africa — Kenya, 2013–2014` | Android mobile wallet with smart-card interface |
| `Wowzi — Africa, 2025–present` | Creator platform, advertiser dashboard, creator mobile app, SME segment |

Where a number comes from Antony's memory rather than a document, tag it
`field` and phrase it as an observation ("agent-assisted onboarding halved
drop-off"), never as a universal constant. Do not attach precise percentages to
field evidence unless he confirms them — leave a `TODO(antony):` marker and
raise it in the PR.

**Do not reproduce text from the Google, CGAP, GSMA or McKinsey PDFs.** Cite,
paraphrase, and link. The APK-size and offline-first guidance is Google's
published position — attribute it as `vendor`/`published`, not as ours.

---

## 5. README structure

Order matters; most repos bury the thing people came for.

1. One-line tagline + a 3-line "what this is".
2. **Install** — copy-pasteable, Claude Code first (`/plugin marketplace add ...`),
   then claude.ai, Cursor, generic API. Above the fold.
3. **The nine skills** — table, one line each, linked.
4. **Show it working** — a short before/after: a spec that fails the audit, the
   findings, the fixed spec. Screenshot or fenced transcript. This is what makes
   people star it.
5. **The constraint model** — the four physical constraints in one diagram.
6. Contributing (link) · Evidence standard (link) · License · Citation.

No badges beyond CI status and license. No roadmap section — use Issues.

---

## 6. CONTRIBUTING.md — the load-bearing document

The failure mode for a repo like this is drowning in well-meaning PRs that add
unsourced opinions. The contribution bar is the product.

Required for any new or changed rule:
- **Market** — where was this observed. "Emerging markets" is not a market.
- **Device/network tier** — which of the tiers in `docs/EVIDENCE.md`.
- **Observed effect** — what changed, and how it was measured.
- **Evidence tier** — `field`, `published`, or `vendor`, per §4.

Also specify: how to run the validator locally, that `rules.yml` and the prose
table must be updated together, and that new skills start life as a
`skill-proposal` issue, not a PR.

---

## 7. Distribution

- `.claude-plugin/marketplace.json` so Claude Code users get
  `/plugin marketplace add kaguara/emerging-market-skills`, then
  `/plugin install emerging-market-skills`. Single biggest adoption lever.
- Tagged releases with a `bundle.zip` of `skills/` for users of tools without
  marketplace support (upload directly to claude.ai, drop into `.cursor/rules`).
- `docs/INSTALL.md` covering Claude Code, claude.ai, Cursor, GitHub Copilot, and
  raw system-prompt injection for anyone building on the API.
- Topics on the GitHub repo: `claude-skills`, `agent-skills`, `emerging-markets`,
  `offline-first`, `mobile-development`, `next-billion-users`.

---

## 8. CI

`validate.yml` runs on every PR and must check:

1. Every `skills/*/` has `SKILL.md` with valid frontmatter; `name` matches the
   directory; `description` is under 1024 characters and mentions when to invoke.
2. `rules.yml` validates against `tools/rules.schema.json`.
3. Rule IDs are globally unique and use the skill's registered prefix.
4. Every `severity: critical` rule carries an evidence tag.
5. Every `published` evidence entry resolves to a `docs/SOURCES.md` key.
6. The rules table in `SKILL.md` lists exactly the IDs in `rules.yml` (no drift).
7. Links resolve (lychee or equivalent, warn-only on external).

Ship `tools/validate_skills.py` as a plain Python 3.11+ script; `pyyaml` is the
only dependency. It must be runnable locally with no arguments.

---

## 9. Launch sequence

1. Scaffold repo, write skills 1–6, get CI green. Repo stays private.
2. Run `examples/movietonight-audit.md` — audit the real cinematch codebase with
   the skills and fix what surfaces. If the skills do not find anything real in a
   product that was not built for these constraints, the skills are too soft.
   This example is also the README's proof section.
3. Two external readers — one PM, one Android engineer — install from a clean
   machine using only `docs/INSTALL.md`. Fix whatever they trip on.
4. Public. Tag `v0.1.0`. Post: personal LinkedIn/X, `r/androiddev`,
   Claude Code plugin/skills community listings, Africa-focused dev communities.
   Lead with the audit example, not the philosophy.
5. Skills 7–9, tag `v0.2.0` within two weeks.

## 10. Maintenance commitments to state publicly in the README

Say these plainly so expectations are set and the repo does not look abandoned:
- Issues triaged weekly.
- Rules are versioned; a rule is never silently changed, it is superseded with
  the old ID retained and marked `superseded_by`.
- Field reports that contradict a rule are the most welcome contribution type.
