---
name: network-resilience
description: Use when designing, building, or reviewing any feature that makes a network call for users on intermittent, slow, expensive, or metered connections. Covers offline queueing, idempotency, retry and backoff, sync conflict resolution, timeout sizing, data-saver handling, and graceful degradation on 2G/3G and congested LTE. Applies to mobile and web. Invoke on specs, PRs, API designs, and any code that fetches, posts, syncs, or retries.
license: MIT
---

# Network resilience

## The constraint

The connection is not slow. It is intermittent, asymmetric, and dishonest — it
disappears mid-request, reports itself as live while carrying no traffic to your
origin, and costs the user money per megabyte from a prepaid bundle they top up
in fifty-cent increments. Latency to your origin is 300–800ms before congestion.
The device changes network three times on a matatu ride to work.

Design for a connection that fails *ambiguously*. Total failure is easy: you
show an error. The expensive case is the request that neither succeeds nor
fails, and the user who taps again.

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| NET-001 | Render from local state first; never block first paint on a network call. | critical |
| NET-002 | Queue every state-changing request durably before attempting it. | critical |
| NET-003 | Every state-changing request carries a client-generated idempotency key. | critical |
| NET-004 | Pending, queued, and failed states are visible and honest in the UI. | critical |
| NET-005 | Set explicit request timeouts sized for the target network, not the default. | warning |
| NET-006 | Retry with capped exponential backoff and jitter; never tight-loop. | warning |
| NET-007 | Treat the connectivity flag as a hint, not a fact. | warning |
| NET-008 | Honour metered-connection and data-saver signals. | warning |
| NET-009 | Declare a conflict-resolution policy for every entity that syncs. | warning |
| NET-010 | Batch and compress; minimise round trips over payload elegance. | advisory |
| NET-011 | Size a partner integration for their slowest component, not for their API's stated limits. | critical |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Judgment

**Offline-first is not free, and it is not always right.** A durable queue costs
storage, a sync engine, and install size — and install size costs you installs
(see `payload-budgets`). The test is whether the user's intent survives the app
being killed. A "like" does not need to; a loan repayment does. Apply NET-002
to actions where losing the intent costs the user money, time, or a trip, and
let the rest fail loudly and cheaply.

**Caching trades staleness for availability, and the exchange rate depends on
the data.** A film recommendation may be a week stale with no harm. A wallet
balance may not be stale at all — but it also must not vanish when the network
does. The resolution is not to pick one: show the cached value, label it with
the time it was fetched, and never let a cached balance authorise a transaction.
NET-001 and NET-004 are the same rule seen from two directions — always render
something, always be honest about what it is.

**Optimistic UI is a claim about the server, so scope the claim.** Optimism is
correct for anything you can reverse without the user noticing, and dishonest
for anything that moves money or grants access. When you cannot be optimistic,
be *fast about being pending*: acknowledge in under 100ms that the intent was
captured. Users tolerate waiting for confirmation. They do not tolerate not
knowing whether they were heard.

**Retry policy is a shared resource.** Your backoff is not only about your
server. Thousands of clients on the same congested cell, all retrying on the
same connectivity-restored event, reproduce the congestion that caused the
failure. Jitter is not politeness; it is the thing that makes recovery possible.

**Do not send the user's money to the background.** Every byte of prefetch,
telemetry, and background sync is drawn from a prepaid bundle. Treat background
data as a budget you are spending on the user's behalf, and be able to state the
per-session number (see `integration-cost-modeling`).

## Worked patterns

### An outbox that survives process death

Satisfies NET-002, NET-003, NET-006. The key is generated at *intent* time and
persisted with the request, so every retry — including one after a cold start
three hours later — carries the same key.

```ts
// lib/outbox.ts
type Intent = {
  key: string;          // idempotency key, generated once, at intent time
  url: string;
  body: unknown;
  attempts: number;
  nextAttemptAt: number;
};

export async function enqueue(url: string, body: unknown): Promise<string> {
  const intent: Intent = {
    key: crypto.randomUUID(),
    url,
    body,
    attempts: 0,
    nextAttemptAt: Date.now(),
  };
  await idb.put("outbox", intent);       // durable before any network attempt
  void drain();                           // fire and forget; drain is idempotent
  return intent.key;                      // caller renders "queued" against this
}

export async function drain(): Promise<void> {
  for (const intent of await idb.getAll("outbox")) {
    if (intent.nextAttemptAt > Date.now()) continue;

    try {
      const res = await fetch(intent.url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "idempotency-key": intent.key,   // same key on every attempt
        },
        body: JSON.stringify(intent.body),
        signal: AbortSignal.timeout(30_000), // NET-005: patient, writes must land
      });

      if (res.ok) {
        await idb.delete("outbox", intent.key);
      } else if (res.status >= 400 && res.status < 500) {
        await deadLetter(intent, await res.text()); // will never succeed; stop
      } else {
        await backoff(intent);
      }
    } catch {
      await backoff(intent);               // timeout or transport failure
    }
  }
}

async function backoff(intent: Intent): Promise<void> {
  if (intent.attempts >= 8) return deadLetter(intent, "retry cap reached");
  const ceiling = Math.min(2 ** intent.attempts * 1_000, 5 * 60_000);
  await idb.put("outbox", {
    ...intent,
    attempts: intent.attempts + 1,
    nextAttemptAt: Date.now() + Math.random() * ceiling, // NET-006: full jitter
  });
}
```

Drain on app start, on the connectivity-restored event, and from a periodic
background task. On Android, the equivalent is a `CoroutineWorker` under
`WorkManager` with `setBackoffCriteria(BackoffPolicy.EXPONENTIAL, ...)` and a
`NetworkType.CONNECTED` constraint — the platform already solved persistence
across process death, so do not rebuild it.

### Proving the network before trusting it

Satisfies NET-007. `navigator.onLine` answers "is there an interface up", which
is not the question.

```ts
export async function originReachable(): Promise<boolean> {
  if (!navigator.onLine) return false;              // fast negative is reliable
  try {
    const res = await fetch("/api/ping", {
      cache: "no-store",
      signal: AbortSignal.timeout(4_000),
    });
    // A captive portal or operator upsell page returns 200 with HTML.
    return res.ok && res.headers.get("content-type")?.includes("json") === true;
  } catch {
    return false;
  }
}
```

The content-type check is the point. A depleted prepaid bundle terminates your
request at an operator portal that answers `200 OK` with a top-up page. Status
codes alone will tell you everything is fine.

### Degrading by measured conditions, not by guess

Satisfies NET-001, NET-008. Serve the cheap thing by default and upgrade only
when the connection has earned it.

```tsx
function useAssetTier(): "minimal" | "standard" | "rich" {
  const c = (navigator as any).connection;
  if (!c) return "standard";
  if (c.saveData) return "minimal";                 // explicit user instruction
  if (["slow-2g", "2g"].includes(c.effectiveType)) return "minimal";
  if (c.effectiveType === "3g") return "standard";
  return "rich";
}
```

Tie the tier to image resolution, prefetch, autoplay, and animation — one signal
driving every expensive decision, rather than each component deciding alone.
`saveData` is a user instruction, not a hint; there is no tier above `minimal`
when it is set.

## Anti-patterns

**Retrying on the connectivity-restored event with no jitter.** Every client on
the cell fires at the same instant, the cell saturates, all requests time out,
and every client schedules another synchronised retry. You have built a
self-inflicted DDoS that recovers only when users close the app.

**Generating the idempotency key at send time.** The key must be born with the
intent. Generated inside the retry loop, it changes on every attempt, and the
server sees a duplicate as a new legitimate request. The user pays twice and the
logs show two clean successes.

**Reverting optimistic state silently on failure.** The item was in the cart,
then it was not. Nothing was said. The user assumes they misclicked, redoes it,
and it fails again. Every optimistic update needs a failure path that names what
happened.

**A spinner with no timeout.** On an ambiguous connection it spins for ninety
seconds. The user force-quits, losing any in-memory queue, and reopens to find
their action gone. Every indeterminate state needs a deadline and an exit.

**Treating a cached balance as authoritative.** Cached values are for display.
The moment one is used to authorise a transaction, staleness becomes an
overdraft. See `money-movement` for the server-authoritative pattern.

**Shipping a sync engine before shipping the feature.** Offline-first is
architecture, and architecture chosen before you know which actions matter
produces a 14MB app that syncs everything and installs on nobody's phone.
Identify the two or three intents that must survive, queue those, and grow.

## Verification

```bash
python3 skills/network-resilience/scripts/audit_handlers.py <path>
```

Flags state-changing handlers with no queue write, missing idempotency headers,
`fetch` calls with no timeout, and branches on `navigator.onLine` with no
confirmation round trip.

Static analysis will not tell you whether it works. Also:

- **Test on a throttled link, not a disabled one.** Airplane mode exercises the
  easy path. Use `tc netem` or Chrome DevTools at 400kbps with 400ms RTT and 2%
  packet loss, and drop the connection *mid-request*, which is the case that
  finds bugs. See `field-testing-and-telemetry`.
- **Kill the process during a queued write.** On Android, `adb shell am kill`.
  The intent must be there on restart.
- **Instrument the ambiguous case.** Track time-to-confirmation, queue depth,
  dead-letter rate, and duplicate-intent rate segmented by effective connection
  type. A duplicate-intent rate above zero means NET-003 is not holding
  somewhere.

## Sources

- NET-001, NET-003 — field, Juvo Mobile (6 markets, Central & South America,
  2015–2020).
- NET-002 — field, gethomespace (Kenya/US, 2020–2022); vendor, Android
  WorkManager.
- NET-004 — field, IBM Research Africa (Kenya, 2013–2014).
- NET-006 — vendor, AWS Architecture Blog on exponential backoff and jitter.
- NET-007 — field, Smile Identity (pan-African, 2017–2020).
- NET-008 — vendor, Chrome `Save-Data` and Network Information API.

Full citations in [`docs/SOURCES.md`](../../docs/SOURCES.md).
