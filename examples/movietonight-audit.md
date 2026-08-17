# Worked example: auditing MovieTonight

A real audit of a production Next.js product ([movietonight.ai][mt]) that was
not built against these constraints. It is included because it shows the format,
and because it shows the failure mode the rubric is designed to prevent.

## Step 1 — the target

MovieTonight is a personalised film recommendation product, currently in private
beta on desktop and mobile web, built on Next.js, Supabase, TMDb, and OpenAI.

The audit assumption, stated because REVIEW-001 requires it:

> **Market:** Kenya. **Device tier:** C — entry-level Android, 1–2GB RAM.
> **Network:** congested 3G with frequent handover. **Platform:** web.
> **Stage:** private beta, pre-launch.

This is a hypothetical target. The product's current beta audience is not
primarily tier C, so several findings below are "not yet done" rather than
"wrong" — which REVIEW-004 asks the reviewer to distinguish.

## Step 2 — what the first pass got wrong

The first pass grepped for `fetch(` calls without a timeout and produced ten
hits across the TMDb client, the OMDb client, and three OpenAI services. Ten
NET-005 violations would have been the headline finding.

All ten were false. The options object spans multiple lines, so `AbortSignal`
sits several lines below the `fetch(`. Reading the files:

```ts
// lib/tmdb/client.ts:105 — timeout, and a retry loop with attempt limits above it
const response = await fetch(url, {
  headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
  next: { revalidate: 300 },
  signal: AbortSignal.timeout(timeoutMs),
});
```

```ts
// services/movie-classification.service.ts:349 — token ceiling and timeout both set
max_output_tokens: 1400,
signal: AbortSignal.timeout(6500),
```

Every OpenAI call site sets `max_output_tokens` and a timeout. Every TMDb call
retries with an attempt cap. **The product passes NET-005 and COST-004 cleanly** —
two of the rules most products fail.

This is REVIEW-003 doing its job. A reviewer who trusted the grep would have
filed ten fabricated findings, and the two real ones below would have been
buried underneath them and dismissed along with the rest.

## Step 3 — findings

### 1. No offline capability of any kind

```
[NET-001, NET-002] critical · repository-wide
No service worker, no cache-first rendering path, no queued writes.
`grep -rn "serviceWorker" app lib services components` returns nothing.
```

**Why it matters here:** every screen is server-rendered per request. On a
congested 3G cell the user gets a blank page or a stalled navigation, and a
returning user who has opened the same recommendation four times still pays for
it on the fifth. At tier C this is the difference between a product that feels
slow and one that appears broken.

**Fix:** cache the last Tonight's Pick and the user's watchlist locally, render
them immediately on load, and revalidate in the background. Queue the three
write actions — watchlist add, rating, reaction — behind a durable outbox.
Scoped to those three, this is days of work, not an architecture change.

### 2. Write actions carry no idempotency key

```
[NET-003] critical · app/actions.ts, app/profile/actions.ts
`grep -rni "idempoten"` matches only services/brevo.service.ts:43 (outbound
email) and an admin UI string. No user-facing write path sets a key.
```

**Why it matters here:** a rating submitted over an ambiguous connection has no
dedupe protection. Most of these writes are naturally idempotent — adding a film
to a watchlist twice is the same as once — which is why this ranks below the
offline gap rather than above it. It stops being harmless the moment a write is
appended rather than set, and that will happen without anyone noticing the
distinction.

**Fix:** generate a key at intent time, send it with the action, dedupe
server-side for 24 hours. Cheap now, expensive to retrofit after the first
append-shaped write ships.

## Step 4 — coverage

**Not checked:**

- **Payload budgets (SIZE).** No production build artifact was available. Run
  `npm run build` and re-run against the stats output.
- **Device performance (PERF).** Requires a real tier C device; emulators
  reproduce the layout and hide the performance.
- **Localization (LOC).** The product is English-only today, so the rules apply
  to a decision not yet made rather than to shipped code. Worth reading
  `localization-and-literacy-ux` before the first translation, since LOC-001 and
  LOC-006 are free at the start and a layout rewrite later.
- **Field telemetry (OBS).** No analytics access during the audit.

**Summary:** two findings, both in the same dimension, both fixable in under a
week. The product's network hygiene on outbound calls is better than most —
timeouts, retries, and token ceilings are all in place. What it has no answer
for is the user's own connection dropping.

[mt]: https://movietonight.ai
