# emerging-market-skills

**Agent skills for building software that works on the other five billion phones.**

AI coding tools write for the environment they were trained on: fast networks,
recent hardware, English interfaces, and bandwidth nobody pays for by the
megabyte. These skills change that. Install them and your assistant starts
asking what happens on 1GB of RAM, what an SMS costs in Lagos, and whether that
button still fits once it is translated.

Built for PMs and engineers. Technical and build-focused — architecture,
budgets, and code, not market sizing or go-to-market.

[![validate](https://github.com/Kaguara/emerging-market-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/Kaguara/emerging-market-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

## Install

Claude Code:

```
/plugin marketplace add Kaguara/emerging-market-skills
```

```
/plugin install emerging-market-skills@kaguara
```

Skills load on demand — Claude reads each description and pulls in the full
skill only when the work matches.

**Using Codex, Cursor, Copilot, Gemini CLI, Aider, Windsurf, or Zed?** They read
[`AGENTS.md`](AGENTS.md) — one flat file with all 65 rules, generated from the
same source and kept current by CI. Drop it at your project root. Full
instructions for every tool in [docs/INSTALL.md](docs/INSTALL.md).

Then just work. Or invoke a review directly:

```
Use emerging-market-review on this PR. Target market is Kenya, tier C Android.
```

## The skills

| Skill | Answers |
|---|---|
| [emerging-market-review](skills/emerging-market-review/) | The router. Establishes the target, dispatches to the rest, ranks findings by user impact. |
| [network-resilience](skills/network-resilience/) | What happens when the network is absent, slow, metered, or lying? |
| [payload-budgets](skills/payload-budgets/) | How many bytes before someone on 2G gives up? |
| [low-end-device-performance](skills/low-end-device-performance/) | Does it survive 2GB of RAM, an old SoC, and a tired battery? |
| [integration-cost-modeling](skills/integration-cost-modeling/) | What does one user action cost — in SMS, API calls, tokens, and their data bundle? |
| [localization-and-literacy-ux](skills/localization-and-literacy-ux/) | Does the interface survive translation, RTL, and a first-time smartphone user? |
| [identity-and-onboarding](skills/identity-and-onboarding/) | SIM churn, unreliable government ID authorities, and face capture that works on darker skin in bad light. |

Two more land in v0.2: `money-movement` and `field-testing-and-telemetry`.

## What a skill actually is

Not a prompt. Each skill is three files, and the third is the one that makes
this different from a list of best practices:

```
skills/network-resilience/
├── SKILL.md      # judgment and tradeoffs — read by the model when it reasons
├── rules.yml     # thresholds with severity, detection, remedy, and evidence
└── scripts/      # a runnable audit that checks a real artifact
```

`rules.yml` is the connective tissue. The prose cites rule IDs, CI fails if the
two drift apart, and every `critical` rule must carry evidence — field,
published, or vendor — or it cannot be critical. That constraint applies to the
maintainers too: two rules currently sit at `warning` with a `TODO` because the
evidence to promote them does not exist yet.

```yaml
- id: NET-003
  rule: Every state-changing request carries a client-generated idempotency key.
  severity: critical
  evidence:
    - tier: field
      source: Juvo Mobile — 6 markets, Central & South America, 2015–2020
      observation: >
        Ambiguous timeouts caused manual user retries. Without a stable key the
        duplicate was indistinguishable from a second legitimate action.
```

## It works on real code

[examples/movietonight-audit.md](examples/movietonight-audit.md) audits a
production Next.js product. The interesting part is not the two findings — it is
that the first pass produced **ten false ones**, and the review rubric caught
them before they were reported:

> The first pass grepped for `fetch(` without a timeout and found ten hits. All
> ten were false; the options object spans multiple lines. Reading the files
> showed every call site already sets `AbortSignal.timeout` and every model call
> sets `max_output_tokens`. **The product passes NET-005 and COST-004 cleanly.**

A review that reports what a Next.js app *usually* gets wrong, rather than what
this one does, buries its real findings under fabricated ones. That rule is
`REVIEW-003`, and it is in the repo because it is the failure mode these tools
have by default.

## The constraints being designed around

| | |
|---|---|
| **Network** | Not slow — intermittent, ambiguous, and dishonest. Requests that neither succeed nor fail. Connectivity flags that report a live link carrying no traffic. |
| **Device** | 1–2GB RAM shared with the OS, a CPU a quarter as fast as yours, storage permanently near full, a battery at 60% of its original capacity. |
| **Cost** | Two meters running: yours per SMS, per call, per token; theirs a prepaid bundle bought in fifty-cent increments, from which your prefetch is deducted. |
| **Interface** | Read in a language with longer words than English, possibly by someone using a smartphone for the first time, who has not learned that a magnifying glass means search. |

Tier C — entry-level Android on congested 3G — is the design target throughout.
Tiers are defined in [docs/EVIDENCE.md](docs/EVIDENCE.md).

## Where this comes from

A decade of building for these markets: credit risk on telecom data across six
Latin American markets at [Juvo][juvo], identity SDKs covering 200M+ identities
at [Smile Identity][smile], background checks for informal workers in Kenya,
a mobile wallet at IBM Research Africa, and creator tooling across Africa at
Wowzi. Rules tagged `field` come from those products. Rules tagged `published`
or `vendor` cite their source in [docs/SOURCES.md](docs/SOURCES.md).

The field tags are the point. Anything else here, a model could have guessed.

## Contributing

**Field reports that contradict a rule are the most welcome contribution.** If
something here does not hold in your market, on your users' devices, that is a
boundary nobody has mapped yet. You do not need to propose a fix — say what you
saw. [Open a field report][fr].

Rule changes need a market, a device tier, an observed effect, and an evidence
tier. Full detail in [CONTRIBUTING.md](CONTRIBUTING.md); the authoring spec is
[docs/AUTHORING.md](docs/AUTHORING.md).

```bash
pip install -r requirements.txt
python3 tools/validate_skills.py
```

## Maintenance

Issues triaged weekly. Rules are versioned and never silently changed — a
replaced rule keeps its ID with `superseded_by` set, because someone cited it in
a code review once. Maintained by one person, so responses are sometimes slow; a
nudge after two weeks is welcome rather than rude.

MIT licensed. Citation metadata in [CITATION.cff](CITATION.cff).

[fr]: https://github.com/Kaguara/emerging-market-skills/issues/new?template=field-report.yml
[juvo]: https://juvo.com
[smile]: https://usesmileid.com
