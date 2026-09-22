---
name: identity-and-onboarding
description: Use when building or reviewing signup, login, verification, KYC, biometric capture, OTP, sessions, or account recovery for emerging-market users. Covers phone-number-as-identity and SIM churn, designing around unreliable government ID authorities, status transparency, skin-tone-stratified evaluation of face capture, on-device quality gating, OTP deliverability, and shared devices. Invoke on auth flows, KYC integrations, selfie or document capture, and onboarding funnels.
license: MIT
---

# Identity and onboarding

## The constraint

The identifier is rented: prepaid SIMs are recycled, users carry several, and
the number on the account may already belong to someone else. The authority you
verify against is often a government database whose uptime you do not control
and cannot escalate. The camera is poor, the light is bad, and the face in front
of it is one that commercially available models have historically been worst at.
The handset belongs to a household, not a person.

Onboarding is where a product loses the most users, and in these markets almost
every reason is upstream of anything the user did.

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| IDN-001 | Treat the phone number as a rented identifier, not as an identity. | critical |
| IDN-002 | Give every identity-authority call an explicit deadline and a defined outcome at that deadline. | critical |
| IDN-003 | Publish upstream authority status to the people depending on it, in real time. | critical |
| IDN-004 | Evaluate biometric capture stratified by skin tone, using the Monk Skin Tone scale. | critical |
| IDN-005 | Gate capture quality on the device, before anything is uploaded. | critical |
| IDN-006 | Design capture for a poor camera in poor light, and say what to fix. | warning |
| IDN-007 | Never assume the OTP arrived. | warning |
| IDN-008 | Account recovery must not depend on one channel or one device. | warning |
| IDN-009 | Do not block onboarding on a document a legitimate user may not hold. | warning |
| IDN-010 | Assume the device is shared. | warning |
| IDN-011 | Never write credentials, identity documents, or payout details into an offline cache. | critical |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Judgment

**An unreliable upstream is a design constraint, not an incident.** The instinct
when a dependency is flaky is to treat each outage as an exception to be
escalated. When the dependency is a national ID database, there is nobody to
escalate to and the flakiness is permanent. That changes the architecture: every
call gets a deadline chosen for *that* authority, every deadline has a decided
outcome, and the product has a defined behaviour in the degraded state rather
than an undefined one. IDN-002 is the difference between a product that works at
99% and one that works at 99% and degrades honestly at the rest.

**Transparency about flaky infrastructure builds trust rather than spending
it.** This is counter-intuitive enough that most teams get it wrong. The
instinct is to hide upstream problems, because surfacing them looks like
admitting your product is unreliable. The opposite happens: an integrator who
can see that a specific ID authority is down knows the problem is not you, and
knows when to retry. An integrator staring at unexplained failures assumes it is
you. A per-authority status surface with real-time alerts converts your worst
infrastructure day into evidence that you are honest.

**Skin-tone performance is a correctness bug, and the aggregate number hides
it.** A face model reported at 98% accuracy can be near-perfect on lighter skin
and materially worse on darker skin, and for a product serving African markets
the aggregate is arithmetic performed on a population you do not have. Report
per Monk Skin Tone band and treat the gap between bands as the metric. Where
that gap cannot be closed with an off-the-shelf model, training on
representative data is the engineering answer. Note the tooling has moved:
Fitzpatrick was designed to predict sunburn risk and has little variance at the
darker end, and MST exists specifically to replace it for computer vision.

**Three capture constraints compound and none predicts the others.** A low-cost
sensor, uneven light, and darker skin tones each degrade capture; together they
degrade it more than the sum. A model validated against any one of them in
isolation will still fail in a doorway at dusk on a two-year-old handset, which
is where the capture actually happens.

**Move the model to the device.** On-device detection removes the round trip
from the retry loop. A user who has to upload a frame, wait on a poor
connection, and be told it was too dark has spent thirty seconds and some of
their data bundle to learn something the device already knew. ML Kit runs
offline with minimal storage; there is no longer a good reason for the quality
gate to be remote.

**Offline support quietly widens what the device holds.** IDN-010 says assume
the phone is shared; a cache persister is how that assumption gets expensive.
The moment a product decides to work offline, something starts writing whatever
passed through it to disk — and by default that includes the KYC submission, the
ID photo, the payout account and the social access tokens. None of it is needed
offline: a user who cannot reach the network cannot submit KYC or change a bank
account either. Decide what may be persisted in one predicate, default it to no,
and keep identity out of it. The cached copy outlives the session, the logout
and often the owner (NET-013).

## Worked patterns

### An authority call that cannot hang

Satisfies IDN-002, IDN-003. The deadline is per authority because they are not
alike, and the outcome at the deadline is a decision made in advance.

```ts
const AUTHORITY = {
  ke_nid: { deadlineMs: 8_000,  onDeadline: "queue" },   // slow but reliable
  ng_bvn: { deadlineMs: 5_000,  onDeadline: "fallback" },
  za_hanis: { deadlineMs: 12_000, onDeadline: "fail_honest" },
} as const;

export async function verify(authority: keyof typeof AUTHORITY, subject: Subject) {
  const { deadlineMs, onDeadline } = AUTHORITY[authority];

  try {
    const result = await lookup(authority, subject, {
      signal: AbortSignal.timeout(deadlineMs),
    });
    await status.record(authority, "ok");
    return result;
  } catch (err) {
    await status.record(authority, "degraded");   // feeds the dashboard, IDN-003

    switch (onDeadline) {
      case "queue":
        await outbox.enqueue({ authority, subject });
        return { state: "pending", message: "We are still checking. We will notify you." };
      case "fallback":
        return verify(secondarySource(authority), subject);
      case "fail_honest":
        return { state: "unavailable", message: `${label(authority)} is not responding right now.` };
    }
  }
}
```

`fail_honest` returns the name of the authority. "Verification failed" reads as
the user's fault; "the national ID service is not responding" reads as what it
is, and stops a support ticket being opened against you.

### Quality gating before the upload

Satisfies IDN-005, IDN-006. Every failure returns one instruction, not a generic
rejection.

```kotlin
private val detector = FaceDetection.getClient(
    FaceDetectorOptions.Builder()
        .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
        .setMinFaceSize(0.35f)          // face must fill the frame; small faces score badly
        .build()
)

// CameraX default backpressure: analyse the latest frame, drop the backlog.
imageAnalysis.setAnalyzer(executor) { proxy ->
    detector.process(proxy.toInputImage())
        .addOnSuccessListener { faces ->
            val verdict = when {
                faces.isEmpty()               -> Guidance("Move your face into the circle")
                faces.size > 1                -> Guidance("Only one person in frame")
                proxy.luminance() < TOO_DARK  -> Guidance("Find more light, or face a window")
                proxy.isBacklit()             -> Guidance("Turn so the light is in front of you")
                else                          -> Ready
            }
            render(verdict)
        }
        .addOnCompleteListener { proxy.close() }
}
```

Tune `TOO_DARK` against captures from your own users' devices, not against a
test set shot in an office. Luminance thresholds derived from well-lit captures
of lighter skin will reject correct captures of darker skin in adequate light,
which is the same bug as IDN-004 wearing a different hat.

### Evaluating the way the failure actually distributes

Satisfies IDN-004. The aggregate is the number that hides the defect.

```python
# Report per band. The gap between bands is the metric that matters.
for band in range(1, 11):                       # Monk Skin Tone scale, 1-10
    subset = evalset.filter(mst=band)
    print(f"MST {band:>2}  n={len(subset):>5}  "
          f"FRR={false_reject_rate(subset):.3%}  "
          f"capture_retries={mean_retries(subset):.2f}")

worst, best = max(rates), min(rates)
assert worst - best < TOLERANCE, (
    f"skin-tone performance gap {worst - best:.2%} exceeds tolerance — "
    f"this is a defect, not a known limitation"
)
```

Failing the build on the gap is the point. A metric that is reported but never
gates anything becomes a slide, and the disparity survives to production.

## Anti-patterns

**Phone number as primary key.** It is a rented identifier on a recycled pool.
Key on something you issue, and treat the number as a verified attribute that
can change hands — because it will, and the next holder should not inherit an
account.

**An indefinite spinner on a government API.** The database is slow today and
down tomorrow, and neither has a resolution time you can promise. Deadline,
decide, and tell the user which happened.

**Hiding upstream outages.** Your integrators experience it as your product
failing for no stated reason. The outage is going to be visible either way; the
only variable is whether you or their support queue explains it.

**One aggregate accuracy number for face matching.** It is a weighted average
over a population you may not be serving. Stratify or you are not measuring.

**Fitzpatrick for computer-vision evaluation.** It was built to predict sunburn
risk, and it compresses exactly the range you most need resolved. MST exists
because of this.

**Uploading frames to find out whether they were usable.** A round trip on a bad
connection to learn something the device could have determined instantly. Users
do not retry three times; they leave.

**Requiring a document your users do not have.** A required proof-of-address
field in a market of descriptive addresses is a wall in front of a legitimate
customer. Tier access by what has been verified instead.

**Persisting the whole cache because offline was the requirement.** The feature
asked for jobs and messages to survive a dead network. What shipped also wrote
the user's KYC status, bank details and OAuth tokens into unencrypted storage on
a phone that gets lent out. Nothing in the requirement asked for that, and no
reviewer sees it unless the allowlist is a file they can read.

## Verification

```bash
python3 skills/identity-and-onboarding/scripts/audit_identity.py <repo-path>
```

Flags phone-as-primary-key schemas, authority calls with no deadline, capture
upload paths with no on-device gate, and single-channel recovery.

Then measure the things static analysis cannot see:

- **Segment onboarding drop-off by MST band** where you can, and by device model
  and connection type always. A funnel pooled across all of them reports an
  average user who does not exist.
- **Track per-authority latency and error rate separately**, and alert on
  degradation rather than only on hard failure. Degraded is the state that
  produces the spinner.
- **Measure capture retries, not just capture success.** Three attempts and a
  success is a flow that is failing; the success rate will not show it.
- **Test capture in the real conditions**: a two-year-old handset, a doorway at
  dusk, backlit against a window, across the full MST range. Office lighting on
  a flagship validates nothing about this flow.

## Sources

- IDN-001 — field, Juvo Mobile (6 markets, Central & South America, 2015–2020).
- IDN-002, IDN-003, IDN-004, IDN-005, IDN-006 — field, Smile Identity
  (pan-African, 2017–2021).
- IDN-004 — published, Gender Shades (Buolamwini and Gebru, 2018); Google Monk
  Skin Tone Scale.
- IDN-005 — vendor, ML Kit face detection.
- IDN-006 — vendor, Android CameraX.
- IDN-011 — field, Wowzi (Kenya, 2026).

Full citations in [`docs/SOURCES.md`](../../docs/SOURCES.md).
