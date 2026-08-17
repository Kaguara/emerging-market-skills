---
name: emerging-market-review
description: Use when auditing a product, spec, pull request, or architecture for emerging-market viability, or when the user asks whether something will work on low-end devices, poor connections, or in a specific market. The entry point for this skill set — establishes the target market and device tier, dispatches to the specialist skills, and returns findings ranked by user impact. Invoke on "will this work in Kenya/India/Nigeria", "review this for low bandwidth", pre-launch checks, and architecture review.
license: MIT
---

# Emerging market review

## What this skill does

This is the router. It establishes who the product is for, applies the
specialist skills that are relevant, and returns findings ranked by what breaks
the product for the target user.

Use it when the question is broad ("will this work?"). Go straight to a
specialist skill when the question is narrow ("what should our bundle budget
be?").

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| REVIEW-001 | Establish the target market, device tier, and network profile before reviewing. | critical |
| REVIEW-002 | Every finding cites a rule ID, or is labelled as unsourced judgment. | critical |
| REVIEW-003 | Locate every finding in the artifact before reporting it. | critical |
| REVIEW-004 | Rank findings by user impact at the target tier, not by ease of fix. | warning |
| REVIEW-005 | State what was not checked. | warning |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Step 1 — establish the target

Do not skip this. Every threshold in every other skill depends on it, and a
review conducted without it produces advice that is true of software generally
and useful to nobody in particular.

Ask, or state an assumption and continue:

- **Market or markets.** Prices, network conditions, languages, and payment
  rails all differ. "Emerging markets" is not a market.
- **Device tier.** A, B, C, or D from [`docs/EVIDENCE.md`](../../docs/EVIDENCE.md).
  Default to **C** unless told otherwise.
- **Network profile.** Congested 3G with frequent handover is the default
  assumption.
- **Platform.** Android, web, iOS, USSD, SMS — this decides which rules apply.
- **Stage.** A spec can be redirected; a shipped product needs findings ordered
  by what is worth changing now.

Write the assumption into the report. It is what makes the findings checkable.

## Step 2 — dispatch

Load the specialist skills that apply. Most reviews need three or four, not all
eight.

| If the artifact involves | Load |
|---|---|
| Any network call, sync, retry, or offline behaviour | `network-resilience` |
| Dependencies, assets, build config, install or download size | `payload-budgets` |
| Lists, feeds, client-side computation, background work, memory | `low-end-device-performance` |
| SMS, push, USSD, WhatsApp, third-party APIs, AI or inference calls | `integration-cost-modeling` |
| Any user-facing string, layout, form, or icon | `localization-and-literacy-ux` |
| Payments, wallets, balances, disbursement, reconciliation | `money-movement` |
| Signup, login, OTP, KYC, sessions, account recovery | `identity-and-onboarding` |
| Analytics, monitoring, experiments, or "how would we know?" | `field-testing-and-telemetry` |

Read the artifact against each loaded skill's `rules.yml`. Where a rule's
`detect` criteria are met, confirm it in the code before recording it —
REVIEW-003 is the rule most often broken by a model doing this work, because
frameworks have characteristic weaknesses and it is easy to report the
characteristic one instead of the actual one.

## Step 3 — rank and report

Order by user impact at the target tier, not by severity label alone and not by
ease of fix. A `critical` violation on the signup path outranks three
`warning`s in a settings screen. A `warning` on the path every user takes
outranks a `critical` in a flow reached by 2% of them.

Report each finding in this shape:

```
[NET-003] critical · app/api/payments/route.ts:42
Payment handler accepts no idempotency key and has no server-side dedupe.

Why it matters here: a user on a congested cell whose request times out will
tap pay again. Both requests succeed. They are charged twice, and the duplicate
is indistinguishable from a legitimate second payment.

Fix: generate the key at intent time on the client, persist it with the queued
request, dedupe on it server-side for 24h and return the original result.
```

Four elements, every time: **rule ID and location**, **the defect**, **why it
matters for this user**, **the specific fix**. The "why it matters here" line is
what makes a review land — it converts a rule citation into a consequence
someone can picture.

Then close with coverage (REVIEW-005):

```
Not checked: bundle size (no build artifact available), field telemetry
(no analytics access). To check bundle size, run `npm run build` and re-run
with the stats output.
```

## Judgment

**Most products fail on two or three rules, not twenty.** A report with thirty
findings will be read as noise and actioned as nothing. Find the small number
that decide whether the product works, lead with those, and put the rest in an
appendix. If everything is critical, nothing is.

**Distinguish "wrong" from "not yet done".** An early-stage product without
offline sync has made a reasonable sequencing decision. The same product about
to launch in a market where users are offline for hours has a problem. Weight
findings by stage, and say which of the two you are reporting.

**The absence of a rule is not permission.** These skills cover network,
payload, device, cost, language, money, identity, and measurement. They do not
cover everything. When something looks wrong and no rule fits, say so and label
it `judgment` under REVIEW-002 — an honest unsourced observation is more useful
than a rule stretched to cover a case it was not written for.

**Reviewing a spec is more valuable than reviewing code.** At spec stage the
answer can be "queue this action" rather than "retrofit a queue". Push to be
invoked earlier; say so explicitly when a finding would have cost nothing a
month ago.

## Anti-patterns in the review itself

**Reporting the framework's usual weaknesses.** Next.js apps often ship large
first-load bundles. *This* one may not. Open the file. A single fabricated
finding costs the reader's trust in the twelve real ones next to it.

**Grading the code instead of the experience.** A clean codebase can be
unusable at tier C, and a messy one can work beautifully. The subject of this
review is the person holding the phone.

**Recommending a rewrite.** "Adopt offline-first architecture" is not
actionable. "Queue the three write actions in `app/actions.ts` behind a durable
outbox" is. Scope every fix to something a person could do this week.

**Silence about what you could not check.** A report that omits its gaps reads
as comprehensive. Name them.

## Worked example

[`examples/movietonight-audit.md`](../../examples/movietonight-audit.md) is a
full audit of a production Next.js product that was not built against these
constraints — the assumptions, the findings, the ranking, and the coverage gaps.
Read it before running your first review; it calibrates the level of specificity
expected far faster than this file can describe it.

## Sources

The rules in this skill are process rules for conducting a review and carry no
external evidence. The rules they dispatch to are evidenced individually — see
each specialist skill's Sources section and [`docs/SOURCES.md`](../../docs/SOURCES.md).
