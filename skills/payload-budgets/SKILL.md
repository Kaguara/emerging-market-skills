---
name: payload-budgets
description: Use when deciding what to ship over the wire, or reviewing anything that adds bytes — bundle size, APK and app-bundle size, images, fonts, third-party scripts, SDK footprint, and install-time versus on-demand delivery. Invoke on dependency additions, new screens, asset pipelines, build config, and any PR that grows the artifact. Covers Android, iOS, and web, with CI enforcement patterns.
license: MIT
---

# Payload budgets

## The constraint

Bytes cost money that the user paid in advance, arrive over a link that drops,
and land on a device that is already full. A download that fails at 80% is
retried on a prepaid bundle, which means the second attempt costs real money for
nothing. Storage is the other half: on a 16GB device sitting permanently near
full, your app is competing for space with photographs of the user's family, and
it will lose.

The number that matters is the **cold, uncached, first-attempt download on a
congested cell**. Every other number flatters you.

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| SIZE-001 | Declare a byte budget per platform before writing the feature. | critical |
| SIZE-002 | Keep the Android initial download at or below 15MB. | critical |
| SIZE-003 | Budgets are enforced by CI and fail the build when exceeded. | critical |
| SIZE-004 | Measure the cold-cache first visit on a tier C device, not a warm reload. | warning |
| SIZE-005 | Serve images sized to the rendered box, in a modern format, responsively. | warning |
| SIZE-006 | Cap first-load JavaScript on the critical path at 200KB compressed. | warning |
| SIZE-007 | Every third-party script has a named owner and counts against the budget. | warning |
| SIZE-008 | Load secondary features on demand rather than at install or first paint. | warning |
| SIZE-009 | Never block first paint on a web font. | warning |
| SIZE-010 | Budget the installed storage footprint, not only the download. | advisory |
| SIZE-011 | Upload media when the user commits, not when they pick, and cancel a superseded upload. | warning |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Judgment

**The budget is a product decision wearing engineering clothes.** "We have 15MB"
forces the question of which features a first-time user actually needs, and that
question has a better answer than "all of them". Teams that treat size as an
optimisation phase arrive at the end of the project with 40MB and no way to get
back. Teams that treat it as a constraint arrive with a smaller, clearer
product. Set the number first; it does more design work than it looks like.

**Size fights offline-first, and the tiebreak is per feature.** `network-resilience`
argues for local persistence and cached assets; this skill argues for fewer
bytes. Both are right. Resolve it by asking what a *first session* needs: cache
the data for flows the user will repeat, ship nothing at install for flows they
may never open. A sync engine for a feature reached by 3% of users is the worst
of both — it costs install size and delivers offline capability nobody uses.

**Third-party bytes are where budgets die.** Nobody adds 2MB of first-party code
without discussion. Everybody adds a tag manager. The asymmetry is that
first-party code is reviewed by someone who owns the budget and third-party code
arrives through a marketing request, a vendor integration, or a growth
experiment that was never unshipped. SIZE-007 exists because ownership, not
technique, is the actual fix.

**Compression ratios flatter JavaScript and lie about the cost.** 200KB
compressed is 200KB of transfer but roughly a megabyte to parse, compile, and
execute — on a tier C CPU, that is seconds of a locked main thread. Transfer
size is the budget; execution cost is the reason the budget is low. See
`low-end-device-performance` for the other side of it.

**Know what a megabyte costs your user in their currency.** It is a real number,
it varies by an order of magnitude between markets, and quoting it in a design
review changes the conversation from aesthetics to arithmetic. Work it out with
`integration-cost-modeling` and put it in the repo next to the budget.

**Uploads are the budget too, and they are the part you did not measure.** A
download budget is enforced in CI and argued over in review; the bytes a user
sends leave no artifact to weigh, so nobody weighs them. In any flow where
people pick media, they pick more than they send — a take they look at and
redo, a photo they swap. Uploading at pick time charges every discarded attempt
to a prepaid bundle. Upload at submit, and the bytes match the intent.

## Worked patterns

### A budget CI actually enforces

Satisfies SIZE-001, SIZE-003. The budget lives in version control next to the
code, so changing it is a reviewable act rather than a quiet decision.

```json
// budgets.json
{
  "android": { "initialDownloadMB": 15,  "note": "largest device split, tier C config" },
  "web":     { "firstLoadJsKB": 200, "totalFirstViewKB": 900, "largestImageKB": 120 }
}
```

```js
// tools/check-budget.mjs — run in CI after the build
import { readFileSync, statSync } from "node:fs";
import { gzipSync } from "node:zlib";

const budgets = JSON.parse(readFileSync("budgets.json", "utf8")).web;
const failures = [];

const firstLoadKB = Math.round(
  gzipSync(readFileSync(".next/static/chunks/main.js")).length / 1024
);
if (firstLoadKB > budgets.firstLoadJsKB) {
  failures.push(`first-load JS ${firstLoadKB}KB exceeds ${budgets.firstLoadJsKB}KB`);
}

// Always print the number, pass or fail, so the trend is visible in every build log.
console.log(`first-load JS: ${firstLoadKB}KB / ${budgets.firstLoadJsKB}KB`);

if (failures.length) {
  console.error("\nBudget exceeded:\n  " + failures.join("\n  "));
  process.exit(1);
}
```

Printing the number on passing builds matters as much as failing on regressions.
It turns size into something the team sees daily rather than a tripwire that
fires once a quarter and gets raised because the release is due.

### Splitting an Android artifact honestly

Satisfies SIZE-002, SIZE-008. The universal APK is a debugging convenience and
should never be what you measure.

```groovy
android {
    bundle {
        density  { enableSplit = true }
        abi      { enableSplit = true }
        language { enableSplit = true }
    }
}
```

Then measure the split a real device would receive, not the bundle:

```bash
bundletool build-apks --bundle=app.aab --output=app.apks \
  --device-spec=tier-c-device.json
bundletool get-size total --apks=app.apks   # this is the number in the budget
```

Keep `tier-c-device.json` in the repo — an `arm64-v8a`, `mdpi`, single-locale
spec. A budget checked against a flagship's split is a budget checked against
the smallest download you will ever ship.

### Charging images to the budget

Satisfies SIZE-005. The common failure is not the format, it is serving a
1600px-wide asset into a 320px box on the device least able to afford it.

```tsx
<Image
  src={poster}
  alt={title}
  width={160}
  height={240}                       // explicit box; no layout shift
  sizes="(max-width: 640px) 33vw, 160px"
  quality={70}                       // 70 is visually indistinguishable at this size
  loading="lazy"
/>
```

Set `quality` deliberately. Framework defaults are tuned for retina displays on
broadband, and the difference between quality 70 and 90 is invisible in a 160px
box and roughly double the bytes.

## Anti-patterns

**Measuring the universal APK.** It is not what any user downloads, so it is
either alarmingly large or reassuringly irrelevant, and both readings are wrong.
Measure the device split.

**A budget in a design doc.** It will be exceeded within two months and nobody
will know which change did it. If a machine does not check the number, the
number does not exist.

**Lazy-loading the thing everyone needs.** Code splitting applied without data
moves the cost rather than removing it — the user now waits for a second request
on a link where round trips are the expensive part. Split on what a first
session actually touches, which requires knowing, which requires
`field-testing-and-telemetry`.

**Treating "it's only 200KB" as free.** On a saturated 3G cell, 200KB is several
seconds of transfer plus a second of parse and compile on a tier C CPU. The unit
is not bytes, it is seconds of a user's life, and they are being spent by
someone who cannot see them.

**Adding a dependency for one function.** A date library imported whole for
`formatRelative`, a lodash import for `groupBy`. Check the tree-shaken cost
before merging, and prefer twelve lines of your own code over a transitive
dependency graph you now maintain.

**Optimising images while shipping four font weights.** Effort should follow the
byte histogram. Build the histogram first, then cut the largest line.

**Starting the upload in the picker's callback.** It feels responsive: by the
time they hit send, it is done. In practice the user swaps the attachment twice,
you have paid for three videos to send one, and on a slow link a response from
the attachment they replaced can still arrive and be applied.

## Verification

```bash
python3 skills/payload-budgets/scripts/audit_budget.py <repo-path>
```

Flags a missing `budgets.json`, budgets with no CI enforcement, images checked
into the repo above the largest-image budget, and render-blocking font loads.

Then measure rather than trust:

- **Cold cache, throttled, tier C.** Chrome DevTools at 400kbps / 400ms RTT with
  the cache disabled, or a real device on a real network at 6pm when the cell is
  busy. See `field-testing-and-telemetry`.
- **Track the histogram, not the total.** Which line is largest — JavaScript,
  images, fonts, third-party? Totals tell you there is a problem; histograms tell
  you which meeting to have.
- **Watch the trend across releases.** A single build's number is much less
  useful than the slope. Size regressions are cumulative and individually
  defensible, which is exactly why they need a machine watching.

## Sources

- SIZE-001 — field, Smile Identity (pan-African, 2017–2020).
- SIZE-002, SIZE-008 — vendor, Android App Bundles; published, Google Next
  Billion Users.
- SIZE-003 — field, Juvo Mobile (6 markets, Central & South America, 2015–2020).
- SIZE-010 — vendor, Android (Go edition).
- SIZE-011 — field, Wowzi (Kenya, 2026).

Full citations in [`docs/SOURCES.md`](../../docs/SOURCES.md).
