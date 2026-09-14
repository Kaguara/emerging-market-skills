---
name: low-end-device-performance
description: Use when building or reviewing anything that runs on entry-level hardware — 1–2GB RAM, ageing multi-core SoCs, degraded batteries, small and full storage. Covers memory ceilings, main-thread budgets, process death and state restoration, list virtualisation, background work and battery, animation cost, and server-versus-client computation. Invoke on new screens, list and feed implementations, client-side computation, background jobs, and any performance review.
license: MIT
---

# Low-end device performance

## The constraint

The reference device has 1–2GB of RAM shared with the operating system, a CPU
roughly a quarter as fast as the phone in your pocket, storage that is almost
full, and a four-year-old battery holding perhaps 60% of its original charge.
It is running a browser with eleven tabs and three chat apps that all hold wake
locks. Your process is a candidate for termination from the moment it is
backgrounded.

Performance work here is not about being fast. It is about **surviving**: not
being killed, not running out of memory, not freezing the one thread that
handles touch.

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| PERF-001 | Name a reference device at tier C and make it the definition of "works". | critical |
| PERF-002 | Assume the process will be killed at any moment and restore state on return. | critical |
| PERF-003 | Bound every in-memory cache, especially image caches. | critical |
| PERF-004 | Keep long tasks off the main thread; never block input for more than 200ms. | warning |
| PERF-005 | Recycle or virtualise any list that can exceed one screen. | warning |
| PERF-006 | Precompute on the server what the device would otherwise compute. | warning |
| PERF-007 | Cap background work, wake locks, and polling. | warning |
| PERF-008 | Animate only compositor-friendly properties, and honour reduced motion. | advisory |
| PERF-009 | Give any on-device inference or heavy computation a server or static fallback. | advisory |
| PERF-010 | Test every bottom-anchored control with three-button navigation and the OEM skin of the reference device. | warning |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Judgment

**Your test device is the problem.** Every other rule here follows from
PERF-001. A team whose acceptance criteria run on flagship hardware will ship
something that works, by their own honest measurement, and is unusable for the
people they built it for. The fix is unglamorous and cheap: buy the entry-level
device, put it on the desk, and make it the gate. No profiling technique
substitutes for the moment someone feels the app stutter in their own hand.

**Moving work to the server is the strongest lever and it has a cost.** PERF-006
trades CPU for bytes. Sending a ranked list of ten items instead of two hundred
unranked ones wins twice. Server-rendering a screen so heavy that the HTML
outweighs the JSON it replaced loses. Every instance of this trade needs the
byte number and the CPU number in the same sentence — check `payload-budgets`
before committing to either direction.

**Memory failures do not look like memory failures.** They look like the app
closing itself, or a photograph that never appears, or a form that empties. The
user cannot distinguish an out-of-memory kill from a crash from a bug, and they
do not report it — they stop using the feature. Assume any unexplained retention
complaint is memory until you have ruled it out, because your crash reporter
probably will not show it.

**Process death is a normal event, not an error case.** On Android at tier C,
backgrounding your app while the user checks the SMS code you just asked them
for is often enough to have your process reclaimed. If your multi-step flow
lives in memory, you have built a form that punishes people for following your
own instructions. PERF-002 is not defensive programming; it is the mainline path.

**Battery is a trust surface.** Users on ageing batteries watch the per-app
battery screen and act on it. Being listed there is a category of uninstall that
never shows up in your funnel, because the funnel cannot see the reason.

## Worked patterns

### State that survives the process

Satisfies PERF-002. The rule of thumb: if losing it would make the user redo
typing, it goes to durable storage at the moment it changes, not at submit.

```kotlin
class VerificationViewModel(
    private val handle: SavedStateHandle,
    private val drafts: DraftStore,
) : ViewModel() {

    // Survives configuration change and process death, for small values.
    var step: Int
        get() = handle["step"] ?: 0
        set(value) { handle["step"] = value }

    // Larger user-authored content goes to disk as it is typed, debounced.
    fun onFieldChanged(field: String, value: String) {
        viewModelScope.launch { drafts.put(sessionId, field, value) }
    }
}
```

Verify it rather than assuming it. `adb shell am kill <package>` while the flow
is backgrounded, then reopen: everything the user typed must still be there.
This is a two-minute test that almost nobody runs.

### An image cache with a ceiling

Satisfies PERF-003, PERF-005. The default configuration of most image libraries
is tuned for devices with headroom.

```kotlin
ImageLoader.Builder(context)
    .memoryCache {
        MemoryCache.Builder(context)
            .maxSizePercent(0.15)          // not the 0.25 default; heap here is small
            .build()
    }
    .diskCache {
        DiskCache.Builder()
            .maxSizeBytes(50L * 1024 * 1024)   // full storage is the norm, not the edge
            .build()
    }
    .build()
```

Pair it with requesting images at the size they are drawn. A grid of 120dp
thumbnails decoding 1200px source bitmaps will exhaust the heap regardless of
how the cache is configured — the cache ceiling limits what you retain, not what
you allocate to decode.

### Keeping the main thread free

Satisfies PERF-004. The pattern that matters is chunking work that cannot move
off-thread, so input is never starved.

```ts
async function processInChunks<T>(items: T[], fn: (item: T) => void) {
  for (let i = 0; i < items.length; i++) {
    fn(items[i]);
    if (i % 50 === 0) {
      // Yield so a queued tap is handled before the next chunk.
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }
}
```

Genuinely heavy work belongs in a worker. Chunking is for the middle case — work
too small to justify a worker and too large to run in one go on a slow CPU,
which on tier C is a much wider band than it is on your machine.

## Anti-patterns

**Profiling on a flagship and extrapolating.** Low-end devices are not
proportionally slower. They thermally throttle, have less cache, and fall off
cliffs — a workload that fits in memory on your device and swaps on theirs is
not 4× slower, it is 40× slower. Measure on the device; do not scale a number.

**Unbounded lists behind a paginated API.** The API pages, the client appends to
one array forever, and by page nine the app is holding two thousand rendered
rows. Memory should track the viewport, not the session.

**A spinner that is actually a frozen main thread.** The spinner is a GIF or a
CSS animation, so it keeps moving while the thread is blocked, and the app looks
busy rather than stuck. This is the failure that survives QA longest because it
looks exactly like a slow network.

**Polling for freshness.** A thirty-second poll is a wake every thirty seconds,
a radio activation, and a battery line item, for data the user is not looking at.
Push, or sync when the app comes to the foreground.

**Shipping a client-side model because it demos well.** On-device inference on a
tier C SoC blocks, heats, drains, and often fails to load at all in the memory
available. If it is worth having, it is worth a server fallback — see
`integration-cost-modeling` for what that call costs per user.

**Assuming the framework's inset handling covers your custom control.** The
default tab bar pads for the system navigation bar; the one you wrote to match
the design does not, and nothing tells you. From Android 15 the app is
edge-to-edge whether you asked for it or not, so a fixed-height bar at the
bottom of the screen is now *under* the navigation bar. On gesture navigation
that is a pill over the labels. On three-button navigation — the factory
default on OPPO, Tecno, Infinix and most of the tier C fleet — it is a 48dp
strip of Back / Home / Recents covering the tabs, and every tap goes to the OS.
It passes on the team's phones because the team's phones use gestures.

**Treating jank as cosmetic.** Dropped frames during scroll are read as
brokenness, not slowness, and brokenness is what gets uninstalled. A consistent
30fps beats a variable 60.

## Verification

```bash
python3 skills/low-end-device-performance/scripts/audit_perf.py <repo-path>
```

Flags unbounded caches, non-virtualised list rendering, main-thread work in
known-heavy APIs, and multi-step flows with no persisted state.

Static checks find structure; the device finds the truth:

- **Kill the process mid-flow.** `adb shell am kill <package>`. Anything the user
  typed must survive. Run it on every multi-step flow before release.
- **Trace on the reference device, not an emulator.** Emulators use host CPU and
  host memory, so they reproduce the layout and hide the performance. Use
  Android Studio's profiler or a Chrome trace over USB against real hardware.
- **Watch memory across a long session.** Scroll a feed for five minutes. Flat is
  correct; a staircase means something is retained per item.
- **Switch the emulator and the reference device to three-button navigation**
  and walk every screen. `adb shell cmd overlay enable
  com.android.internal.systemui.navbar.threebutton` on an API 35+ image. Any
  edge-anchored control you built yourself — tab bar, composer, sticky CTA —
  must clear the bar with the inset the platform reports, not a number you
  chose. Rotate to landscape too: the three-button bar moves to a side, and a
  fix that only reads the bottom inset fails there. A modal that is not
  edge-to-edge is already clear of the bar; do not "fix" it.
- **Segment your field metrics by device tier.** A p50 that pools tier A and
  tier C users reports a device population that does not exist. See
  `field-testing-and-telemetry`.

## Sources

- PERF-001, PERF-002 — field, gethomespace (Kenya/US, 2020–2022); vendor,
  Android (Go edition).
- PERF-010 — field, Wowzi (Kenya, 2026).
- PERF-004 — vendor, web.dev Core Web Vitals.

Full citations in [`docs/SOURCES.md`](../../docs/SOURCES.md).
