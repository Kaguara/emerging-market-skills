# Contributing

The thing that makes this repo worth using is that its rules are backed by
someone's actual experience of a market. That is also the thing easiest to lose.
A hundred plausible, unsourced rules would make it indistinguishable from what
you get by asking a model to list emerging-market best practices — which is
free, and already available.

So the contribution bar is about evidence, not about writing quality. A rough
field report is more valuable here than a polished rule with nothing behind it.

## The most valuable contribution

**A field report that contradicts an existing rule.** If something here does not
hold in your market, on your users' devices, that is not a bug report — it is a
boundary condition nobody has mapped yet, and it makes the rule better than it
was.

Open a [field report][fr]. You do not need to propose a fix, write a rule, or
know why it happened. Say what you saw.

## Before you open a pull request

**New skills start as an issue**, not a PR. Use the [skill proposal][sp]
template so we can agree the scope and the rule ID prefix before you spend a
weekend on it.

**Rule changes** can go straight to a PR if small, or through the
[rule change][rc] template if you would rather discuss first.

## What every rule change needs

Fill this in on the PR — the template asks for it:

| | |
|---|---|
| **Market** | Country or region. "Emerging markets" is not a market. |
| **Device / network tier** | A, B, C, or D. See [docs/EVIDENCE.md](docs/EVIDENCE.md). |
| **Observed effect** | What changed, and how you measured it. |
| **Evidence tier** | `field`, `published`, or `vendor`. |

Rules at `critical` severity require evidence and CI enforces it. If you believe
a rule is critical but cannot source it, set `warning` and leave a `TODO` naming
the evidence that would promote it. That is a successful contribution, not a
failed one — two rules in this repo currently sit there for exactly that reason.

**Do not invent numbers.** An honest qualitative observation — "users retried
manually and duplicated transactions" — outranks a precise-sounding statistic
with nothing behind it. The first time a reader catches a fabricated figure,
every other rule loses its authority too.

**Do not paste text from sources.** Paraphrase and cite. Add a `###` key to
[docs/SOURCES.md](docs/SOURCES.md) with a URL and an access date.

## Mechanics

Read [docs/AUTHORING.md](docs/AUTHORING.md) — it is the spec, and
`skills/network-resilience/` is the reference implementation to match.

```bash
pip install -r requirements.txt
python3 tools/validate_skills.py
```

The validator checks frontmatter, the rules schema, ID uniqueness and prefixing,
evidence on critical rules, drift between `rules.yml` and the rules table in
`SKILL.md`, and that citation keys resolve. Run it before you push; CI runs the
same thing.

Two files always change together: `rules.yml` and the rules table in `SKILL.md`.
The validator will tell you if you forget.

## Style

Match the register of the existing skills: direct, second person, opinionated,
no hedging. The reader is a competent engineer who has not worked in these
markets — assume competence, not context.

Be concrete. "A 12MB download fails more often than it completes on a congested
3G cell" carries a rule. "Optimize for low-bandwidth environments" does not, and
a model reading it will ignore it.

## What happens to your PR

Issues are triaged weekly. Small rule changes with evidence usually merge
quickly. New skills take longer because scope and prefix have to settle first,
which is why they start as issues.

Rules are never silently changed. If yours amends an existing rule, it goes in
[CHANGELOG.md](CHANGELOG.md); if it replaces one, the old ID stays with
`superseded_by` pointing at the new one. Someone out there cited that ID in a
code review.

## Maintainer

This is currently maintained by one person, which means responses are sometimes
slow. If a PR has been sitting for more than two weeks, a comment on it is
welcome rather than rude.

[fr]: https://github.com/Kaguara/emerging-market-skills/issues/new?template=field-report.yml
[sp]: https://github.com/Kaguara/emerging-market-skills/issues/new?template=skill-proposal.yml
[rc]: https://github.com/Kaguara/emerging-market-skills/issues/new?template=rule-change.yml
