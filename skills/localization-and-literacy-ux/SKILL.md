---
name: localization-and-literacy-ux
description: Use when building or reviewing any interface that will be translated, or used by people with limited literacy or limited prior exposure to software. Covers text expansion and flexible layout, ICU message formatting and plurals, locale-aware numbers and dates, right-to-left support, icon and label pairing, name and address and phone input, language selection, and error copy. Invoke on new UI, component libraries, forms, i18n setup, and copy review.
license: MIT
---

# Localization and literacy UX

## The constraint

The interface will be read in a language whose words are longer than English's,
by someone who may be literate in a different language than the one on screen,
on a small display, in sunlight, on a phone that was set up by a relative. Some
of them are using a smartphone for the first time, and have not learned that a
magnifying glass means search or that three horizontal lines mean menu.

None of this is an accessibility afterthought. It is the mainline case, and
almost every failure it produces is a layout or a data-formatting bug that could
have been caught by a machine.

## Hard rules

| ID | Rule | Severity |
|---|---|---|
| LOC-001 | Text containers stretch; never fix the height or width of a box holding a string. | critical |
| LOC-002 | Build sentences with a message formatter, never string concatenation. | critical |
| LOC-003 | Format numbers, dates, currency, and names with locale data, never by hand. | warning |
| LOC-004 | Run pseudo-localization in CI at the expansion factor of your longest language. | warning |
| LOC-005 | Never let an icon carry meaning on its own. | warning |
| LOC-006 | Use logical layout properties so right-to-left works without a second layout. | warning |
| LOC-007 | Every critical flow is completable without reading a paragraph. | warning |
| LOC-008 | Language is an explicit, persisted user choice, not an inference. | warning |
| LOC-009 | Do not hardcode the shape of names, addresses, or phone numbers. | warning |
| LOC-010 | Error messages name the cause and the next action, in plain translated language. | advisory |
| LOC-011 | Render an unknown value as a placeholder, never as zero. | warning |

Full detection criteria and remedies in [`rules.yml`](rules.yml).

## Judgment

**Expansion hits hardest where you have least room.** Long strings expand by a
modest percentage; short ones can double. Interface labels — "Save", "Next",
"Done" — are the shortest strings you have and they sit in the tightest boxes,
usually a button someone sized to fit the English word. This is why LOC-001 is
critical while most of this skill is a warning: a clipped label is not a
cosmetic issue, it is a control whose function is now unknown.

**Truncation is a decision about content, not a layout strategy.** Ellipsis on a
user's message title is fine. Ellipsis on your own button is a bug wearing a
design system's clothes. If a label does not fit, the container is wrong.

**Icon literacy is learned, and you learned it somewhere they may not have.** A
floppy disk means save to people who used floppy disks or used software written
by people who did. A first-time smartphone user reads it as a shape. Labels cost
you a few pixels of a layout that LOC-001 already made flexible, and they remove
an entire class of "the user could not find the feature" that no amount of
analytics will explain to you.

**Language and locale are different questions, and both are usually guessed
wrong.** Device locale tells you who configured the phone. IP tells you where
the SIM is roaming. Neither tells you what the person in front of the screen
reads comfortably. Ask once, early, in the language names themselves — 
"Kiswahili", not "Swahili" — and persist it to the account so a reinstall or a
new device does not throw it away. Shared devices make this more common than
your numbers will suggest.

**Voice and imagery are throughput, not accessibility features.** For users who
read slowly in the interface language, a spoken prompt or a photograph carries
the same information faster and with less error. Treat them as legitimate
primary affordances where the flow is critical, rather than as accommodations
bolted on at the end.

**A number on screen is a sentence, and zero is the wrong one.** The default
that turns a missing value into `0` is written in the data layer, by someone
thinking about types, and it is read on the home screen by someone thinking
about their money. "0" says the balance is empty, the jobs are gone, the rating
is bottom. "—" says the app does not know yet, and it says it without a word to
translate or read. Keep the value nullable all the way to the view; the cost is
a type parameter, and the alternative is the app accusing itself.

## Worked patterns

### Layout that cannot clip

Satisfies LOC-001, LOC-006. The fix is nearly always to stop specifying a height
and to use logical properties throughout.

```css
.button {
  /* No height. Padding and line-height define the box; content defines the rest. */
  padding-block: 0.75rem;
  padding-inline: 1.25rem;
  min-block-size: 44px;         /* touch target floor, not a text ceiling */
  inline-size: fit-content;
  text-wrap: balance;
}

.card__title {
  /* Truncation is allowed here because the content is the user's, not ours. */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

`padding-inline` rather than `padding-left` and `padding-right` is the whole of
RTL support for most components. Doing it from the start costs nothing; adding
it later is a sweep of every stylesheet you own.

### Sentences a translator can actually translate

Satisfies LOC-002, LOC-003. Concatenation bakes English word order into the code
and makes correct translation impossible rather than merely difficult.

```ts
// Wrong: word order fixed, plural rules assumed, gender unavailable.
const msg = "You have " + count + " new " + (count === 1 ? "message" : "messages");

// Right: the translator controls order and plural categories.
const msg = t("inbox.unread", { count });
```

```json
{
  "inbox.unread": "{count, plural, =0 {No new messages} one {# new message} other {# new messages}}"
}
```

The `=0` case is worth writing every time. "0 messages" is grammatical and
lifeless; an empty state is a place to tell someone what to do next.

### Pseudo-localization that fails the build

Satisfies LOC-004. This finds clipping before a translator or a user does, and
it costs one CI job.

```js
// tools/pseudo-locale.mjs
const ACCENTS = { a: "á", e: "é", i: "í", o: "ó", u: "ú", n: "ñ" };

export function pseudo(str) {
  const accented = [...str].map((c) => ACCENTS[c.toLowerCase()] ?? c).join("");
  const padding = "·".repeat(Math.ceil(str.length * 0.4));   // +40% expansion
  return `⟦${accented}${padding}⟧`;                          // brackets reveal clipping
}
```

Build with the pseudo-locale, screenshot the primary flows, and fail on visual
diff. The brackets are the mechanism: if either one is missing from a
screenshot, the string is being clipped, and no human needs to judge it.

### Input that accepts real people

Satisfies LOC-009. Every field here has a default that excludes users.

```tsx
<label htmlFor="name">Full name</label>
<input id="name" name="name" autoComplete="name" />
{/* One field. Given/family order is not universal and many people have one name. */}

<label htmlFor="phone">Phone number</label>
<input id="phone" type="tel" inputMode="tel" autoComplete="tel" />
{/* Normalise to E.164 on the server. Do not validate national length client-side. */}
```

Ask for a postcode only where one exists and is used. In many markets an address
is a description — a road, a landmark, a building — and a required postal field
is a wall in front of a real customer.

## Anti-patterns

**Fixed-height buttons.** The single most common cause of clipped interface
text. The English string fits, the German and Kiswahili ones do not, and the
control now reads as something else.

**Separate first and last name fields, both required.** Excludes mononymous
users, mis-sorts names where the family name comes first, and produces greetings
that address people incorrectly. One field.

**Translating the interface and leaving the errors.** The interface is
translated because it was in the string file; the errors leak through from a
backend or vendor SDK in English, at the exact moment the user is stuck.

**Language inferred from IP.** A Kenyan user roaming, or behind a CDN edge in
another country, gets an interface in a language they do not read, with no
obvious way back. Infer a default at most; always let it be set.

**Icon-only navigation.** It tests fine with the team, who built the icons. It
fails with users who have not learned the vocabulary, and the failure mode is
silence — they simply never use the feature.

**Right-to-left added in a later release.** It is not a translation task, it is a
layout rewrite. Logical properties on day one are free.

**`?? 0` on the way to a label.** It silences a type error at the boundary and
tells the user their earnings are zero. The value was never zero; it was never
loaded. Absence and emptiness need different glyphs.

## Verification

```bash
python3 skills/localization-and-literacy-ux/scripts/audit_i18n.py <repo-path>
```

Flags fixed-height text containers, string concatenation around interpolated
values, directional CSS properties, hand-rolled date and number formatting, and
icon-only interactive elements with no accessible label.

Then look at it:

- **Screenshot every key flow in the pseudo-locale**, in CI, on a 360px viewport.
  Clipping is visible in a diff and invisible in a code review.
- **Render the longest real translation**, not the average. Ask a translator for
  the worst case in each target language and hold the layout against it.
- **Test one flow end-to-end in a language nobody on the team reads.** What
  remains navigable is what is carried by structure, sequence, and imagery — 
  which is what LOC-007 is asking for.
- **Watch drop-off at the language-selection step.** A spike there usually means
  the languages are listed in English rather than in their own names.

## Sources

- LOC-001, LOC-004 — vendor, W3C Internationalization on text size in translation.
- LOC-002 — vendor, ICU MessageFormat.
- LOC-003 — vendor, Unicode CLDR.
- LOC-005 — published, Google Next Billion Users.
- LOC-011 — field, Wowzi (Kenya, 2026).

Full citations in [`docs/SOURCES.md`](../../docs/SOURCES.md).
