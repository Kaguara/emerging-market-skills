# Evidence standard

Every rule in this repo carries a claim about the physical world. This document
is how those claims are backed, and it is the main thing separating these skills
from a plausible-sounding summary an LLM could generate on request.

## The three tiers

### `field`

Observed in a product that shipped to real users. The strongest tier, and the
one that cannot be reproduced by reading the internet.

```yaml
evidence:
  - tier: field
    source: Juvo Mobile — 6 markets, Central & South America, 2015–2020
    observation: >
      Ambiguous timeouts caused manual user retries. Without a stable
      idempotency key the duplicate was indistinguishable from a second
      legitimate action.
```

Requires:
- **`source`** — product, market, and rough date range. "Emerging markets" is
  not a market. "A fintech I worked at" is not a source.
- **`observation`** — what was actually seen, phrased as an observation rather
  than a law. Write "users retried manually and duplicated transactions", not
  "users always retry after 8 seconds".

Do not attach precise figures to field evidence unless they can be substantiated.
An honest qualitative observation outranks an invented statistic, and the first
time a reader catches a fabricated number, every other rule in the repo loses
its authority too. If a number matters and is not to hand, leave a
`TODO(antony):` marker and raise it in the pull request.

### `published`

Research, industry reports, and academic work — GSMA, CGAP, ITU, Google's Next
Billion Users publications, McKinsey, conference papers.

```yaml
evidence:
  - tier: published
    source: gsma-connectivity-2024
```

`source` is a citation key that must resolve to a `### gsma-connectivity-2024`
heading in [`SOURCES.md`](SOURCES.md). The validator fails the build if it does
not. Paraphrase the finding; never paste the source's text into a skill.

### `vendor`

Platform documentation from the people who build the runtime — Android, Chrome,
Apple, Cloudflare, mobile-money API docs.

```yaml
evidence:
  - tier: vendor
    source: android-workmanager
```

Same citation-key rule as `published`. Vendor documentation is authoritative
about the API and only suggestive about user behaviour. Cite it for "WorkManager
survives process death", not for "users abandon downloads above 15MB".

## Which tier for which claim

| The claim is about | Use |
|---|---|
| How an API behaves | `vendor` |
| How a population behaves | `published` or `field` |
| What happened when we shipped it | `field` |
| A threshold with a number in it | `published` or `vendor`, or make it `advisory` |

A `critical` rule must carry at least one evidence tag. The validator enforces
this. It is the mechanism that stops the file filling up with strongly-worded
preferences.

The one exemption is `kind: process` — rules about how we conduct a review
rather than about how the world behaves. They assert nothing empirical, so there
is nothing for them to cite. See [AUTHORING.md](AUTHORING.md#kind).

When you believe a rule is critical and cannot source it, the correct move is
`warning` plus a `TODO` naming the evidence that would promote it. Two rules in
this repo currently sit at `warning` for exactly that reason — `COST-003` and
`COST-004`. Leaving them visibly under-evidenced is the point: it shows the
standard applies to the maintainers too.

## Device and network tiers

Contributions should say which tier they observed, using this vocabulary. These
are the reference points the skills are written against; they describe the
device population in the markets we target, not the global median.

| Tier | Device | Typical spec | Network |
|---|---|---|---|
| **A** | Recent mid-range | 6–8GB RAM, 2020+ SoC | LTE, mostly reliable |
| **B** | Ageing mid-range | 3–4GB RAM, 4–6 years old | LTE that degrades to 3G under load |
| **C** | Entry-level / Android Go | 1–2GB RAM, low-clock SoC | 3G, congested at peak, frequent handover |
| **D** | Feature phone / KaiOS | No app install, 512MB or less | 2G, USSD and SMS as primary rails |

**Tier C is the design target for these skills.** Tier A is what your test device
is, which is the problem. Tier D is out of scope for most rules but is where
`integration-cost-modeling` and `localization-and-literacy-ux` still apply, and
a product that ignores it forfeits a real share of users in several markets.

When you report a finding, name the tier: "on tier C, first contentful paint was
past 11 seconds" is actionable. "It was slow on cheap phones" is not.

## Superseding a rule

Rules are never deleted and IDs are never reused. When a rule is replaced:

```yaml
  - id: NET-004
    rule: ...
    severity: warning
    superseded_by: NET-021
```

Someone out there has cited `NET-004` in a code review. Leaving the ID resolvable
with a forwarding pointer costs one line and keeps every past reference honest.

## Contradicting a rule

Field reports that contradict an existing rule are the most valuable
contribution this repo can receive, and there is an issue template for them.
A rule that holds in Nairobi and fails in Jakarta is not a broken rule — it is a
rule with an undiscovered boundary condition, and naming that boundary makes it
more useful than it was. Open a `field-report` issue with the market, the tier,
and what you observed.
