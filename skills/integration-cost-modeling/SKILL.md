---
name: integration-cost-modeling
description: Use when choosing or reviewing any paid integration or delivery channel — SMS, USSD, push, WhatsApp, identity and KYC APIs, geocoding, mobile-money rails, LLM and inference calls, CDN and egress. Covers cost per user action, channel selection, rate limiting paid sends, caching third-party lookups, AI token budgets with fallbacks, and fail-open versus fail-closed. Invoke on integration decisions, notification design, AI features, and specs with no cost line.
license: MIT
---

# Integration cost modeling

## The constraint

Two meters are running. Yours: per SMS, per verification, per API call, per
thousand tokens, per gigabyte of egress. Theirs: a prepaid data bundle bought in
small increments, from which every byte you send is deducted.

Both meters are invisible in code review, and neither appears in a design mock.
The result is a well-built feature that costs more per user than it can possibly
be worth, discovered a month after launch by someone reading an invoice. In
markets where per-message and per-call prices vary several-fold between
countries, cost is not a finance concern downstream of the build — it is a
design input that determines the architecture.

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| COST-001 | Every user-facing action has a stated marginal cost before it is built. | critical |
| COST-002 | Choose the delivery channel by cost per delivered outcome, not by convenience. | critical |
| COST-003 | Rate-limit and de-duplicate every paid outbound message. | warning |
| COST-004 | Cap AI and inference spend per session with a hard ceiling and a fallback. | warning |
| COST-005 | Never spend the user's data allowance on telemetry or prefetch you chose. | warning |
| COST-006 | Cache and batch third-party calls against a known per-call price. | warning |
| COST-007 | Decide fail-open or fail-closed for every paid dependency, in writing. | warning |
| COST-008 | Serve from a region near the user and count egress. | warning |
| COST-009 | Re-check unit costs against real usage within a month of launch. | warning |
| COST-010 | Find out whether the operator will zero-rate your traffic before you spend a quarter optimising bytes. | warning |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Judgment

**Cost per delivered outcome, not cost per send.** A push notification costs
essentially nothing and reaches a user who has an active data session, which at
tier C is often not the case for hours at a time. An SMS costs real money and
arrives. Comparing them on unit price is comparing a free thing that does not
happen against a paid thing that does. Work out the delivered rate for each
channel in each market, then decide per message class: high-intent and
time-critical earns SMS, everything else does not.

**Retries multiply the bill by the thing you are designing around.** The whole
premise of these skills is that connections fail, and every failed paid call is
either wasted money or a duplicate charge. This is where `network-resilience`
and this skill meet: idempotency keys (NET-003) are a correctness mechanism and
a cost-control mechanism in the same line of code. A cost model that assumes one
attempt per action is wrong by whatever your retry rate is, and on a congested
cell that is not a rounding error.

**Cache what you have already paid for.** Identity verification results are
stable for months. Geocoding results are stable for years. These get
re-purchased on every request by systems that simply never had a cache put in
front of them. Before optimising anything else, look for the paid call that runs
twice for the same input — it is almost always there, and it is the cheapest
saving available.

**AI features need a ceiling and a floor.** A ceiling because token spend per
session is unbounded by default and a retry loop over a slow connection can
multiply it. A floor because the feature must still do something when the
budget is spent or the provider is down. Decide what the deterministic fallback
is at design time; a feature that degrades to an error message was not designed,
it was assembled.

**The user's meter is your responsibility too.** Background sync, prefetch,
autoplay, and analytics all spend money belonging to someone who never agreed to
it. Being able to state the per-session background-data figure is the difference
between a team that has thought about this and one that has not.

## Worked patterns

### A cost model that lives in the repo

Satisfies COST-001, COST-009. Keep it beside the code so it is reviewable and
so the launch check is a diff rather than an investigation.

```yaml
# costs/signup.yml — cost to acquire one verified user, KE
action: verified_signup
currency: USD
steps:
  - name: otp_sms
    unit_cost: 0.0140
    expected_count: 1.35        # includes resends on failed delivery
  - name: identity_lookup
    unit_cost: 0.1200
    expected_count: 1.0
    cached: true                # repeat verifications served from cache
  - name: welcome_push
    unit_cost: 0.0000
    expected_count: 1.0
modelled_total: 0.1389
# TODO(antony): confirm unit prices per market before this ships.
```

`expected_count` is where the honesty lives. Setting the OTP count to 1.0
assumes every message is delivered and every user types it correctly the first
time. It is the single most common error in these models and it understates the
largest line.

### An AI call with a ceiling and a floor

Satisfies COST-004. The budget check happens before the call, and the fallback
is a real feature rather than an apology.

```ts
export async function summarize(input: string, userId: string) {
  const cached = await cache.get(semanticKey(input));
  if (cached) return cached;                       // COST-006

  if (await spendToday(userId) > SESSION_TOKEN_CEILING) {
    return extractiveSummary(input);               // deterministic floor
  }

  try {
    const result = await model.complete({
      input,
      max_tokens: 300,                             // hard ceiling per call
      signal: AbortSignal.timeout(8_000),
    });
    await cache.set(semanticKey(input), result, { ttl: DAY });
    return result;
  } catch {
    return extractiveSummary(input);               // same floor on failure
  }
}
```

`extractiveSummary` is the important function. Writing it first forces the
question of how good the non-AI path can be, and the answer is often good enough
that the model call becomes an enhancement rather than a dependency.

### Making a paid send endpoint safe

Satisfies COST-003. Both halves are needed: the throttle bounds the damage, the
dedupe key stops the common case ever reaching it.

```ts
async function sendOtp(phone: string) {
  const recent = await redis.get(`otp:sent:${phone}`);
  if (recent) return { status: "already_sent", retryAfter: ttlOf(recent) };

  const dailyCount = await redis.incr(`otp:count:${phone}:${today()}`);
  if (dailyCount > 10) {
    log.warn("otp cap reached", { phone: hash(phone) });
    return { status: "capped" };
  }

  await sms.send(phone, code, { idempotencyKey: `otp:${phone}:${window()}` });
  await redis.setex(`otp:sent:${phone}`, 60, code);   // cooldown
}
```

Return a normal-looking response on cooldown rather than an error. The user who
taps "resend" three times because the network is slow is behaving reasonably,
and should see "we sent it, check your messages", not a failure.

## Anti-patterns

**SMS as the default notification channel.** It works, it always arrives, and it
turns a growth loop into a line item that scales linearly with users. Reserve it
for messages worth its price: verification, money movement, and time-critical
alerts.

**Modelling one attempt per action.** The whole point of these markets is that
attempts fail. A model without a retry multiplier is describing a network you
are not building for.

**Unthrottled resend buttons.** A user on a bad connection taps resend four
times. Without a cooldown that is four paid messages, four codes, and a support
conversation about which one is valid.

**Re-buying stable data.** Paying to verify the same identity, geocode the same
address, or enrich the same phone number repeatedly. Look for the paid call with
no cache in front of it before looking anywhere else.

**A hard dependency on a paid service with no decided failure mode.** When it
goes down — and it will, more often than its status page suggests — you find out
what your system does under an outage by watching it happen in production.
COST-007 is asking you to decide beforehand.

**Counting tokens and ignoring egress.** Media-heavy products routinely spend
more on bandwidth than on inference. Build the histogram before optimising the
line everyone talks about.

## Verification

```bash
python3 skills/integration-cost-modeling/scripts/audit_costs.py <repo-path>
```

Flags paid-call sites with no cost entry in `costs/`, outbound send endpoints
with no rate limit, model calls with no `max_tokens`, and third-party lookups
with no cache layer.

Then confirm against reality:

- **Instrument every paid call** with a counter tagged by market and outcome.
  Cost per active user belongs on a dashboard someone looks at weekly.
- **Compare modelled against actual at four weeks.** A gap above about 20% means
  an assumption was wrong; retry behaviour and OTP resend rates are the usual
  culprits.
- **Alert on rate of spend, not monthly total.** A runaway loop spends a month's
  budget in an afternoon, and a monthly threshold finds out too late.
- **Measure background bytes per session** on a real device, per
  `field-testing-and-telemetry`. That is the user's meter, and you should be
  able to quote the number.

## Sources

- COST-001 — field, Juvo Mobile (6 markets, Central & South America, 2015–2020).
- COST-002 — field, gethomespace (Kenya/US, 2020–2022).
- COST-006 — field, Smile Identity (pan-African, 2017–2020).

Full citations in [`docs/SOURCES.md`](../../docs/SOURCES.md).
