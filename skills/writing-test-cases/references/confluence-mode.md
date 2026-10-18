# Confluence mode

Load this when the request explicitly asks to create, publish, or update a Confluence
page of test cases for a Jira ticket (or to condense an existing granular suite into a
regression layer).

Given a Jira ticket, produce a Confluence page of end-to-end test cases: each one
written as a sequence of taps/actions a real user would perform, in the exact language
of the live UI (button labels, screen titles), not abstract system-level assertions.
Every test case links to the specific design frame it was written from, and the suite
as a whole is something a tester could actually pick up and run — not just
individually-accurate cases with structural gaps between them. A condensed layer sits
above the granular suite so a routine regression pass doesn't require running 20-30
isolated cases every cycle, while the granular table stays underneath for precise bug
reporting.

## Why this shape matters

Requirements text (acceptance criteria) describes *what* the system must do. The
design shows *how* the user actually does it — the literal button labels, whether a
toggle is a Yes/No pair or a slider, what the screen is titled. Test cases written
only from the ticket text tend to invent plausible-sounding UI ("tap the toggle") that
doesn't match what's actually on screen. Grounding every step in the real design file
avoids that, and the design link on each case lets a reviewer instantly check the two
against each other.

But accurate individual cases aren't the same as a usable suite, and a usable granular
suite isn't the same as one a tester can run every cycle without dreading it. A tester
handed a pile of only-happy-path cases, in prose with no way to mark pass/fail, and no
coverage of what ships by default or what an accessibility checklist requires, will
not be satisfied even if every case they can see is well-written (Step C, Step F
exist to prevent that). And a tester handed 30 isolated one-assertion cases for a
routine cycle won't run them the way they're written either — nobody resets to a
fresh precondition for every single field (Step E exists to prevent that).

## Step A — Fetch and read the ticket

Get the ticket by key (extract it from the URL if given one, e.g. `MWA-394` from
`.../browse/MWA-394`). Pull the full field set — summary, description, acceptance
criteria, and any linked design field — not just the summary line.

As you read, explicitly list out every distinct **requirement source**, because Step C
needs one planned case category per source and it's easy to silently drop one while
focused on the main flow:
- Each acceptance-criteria bullet.
- Any content table in the description — these usually document **default values**,
  which become their own test cases (see Step C).
- Any linked Confluence page referenced from the description (a checklist, a
  glossary, a compliance doc). Read it in full. A linked accessibility, security, or
  legal checklist is not background reading — it is itself a set of requirements that
  need test-case coverage in Step C, on the same footing as the acceptance criteria.

## Step B — Get the design, or ask for it

Look for a design link in these places, in order:
1. A dedicated design/Figma field on the ticket (shows up as a URL or an object with
   `displayName`/`url` when you fetch all fields).
2. A Figma or design-tool URL embedded in the description text.
3. Attachments.

**If you find one, use it.** If you find none, stop and ask the user for a design
link before writing any test cases — do not invent UI copy from the ticket text
alone. A short, direct question is enough: name the ticket and say you need a Figma
(or equivalent) link to write accurate steps. If the ticket genuinely has no UI (a
content/API/backend delivery task), that's a distinct situation from a missing link —
say so and ask how the user wants coverage framed instead (e.g. against the API
contract) rather than treating it as the same blocker.

Once you have a design URL, extract the file key and node ID from it. Fetch the design:
- Use `get_metadata` on the file (or the specific node) to find the frame(s) relevant
  to this ticket — search by name for something matching the ticket's feature area.
  Linked node IDs from the ticket can go stale (the design gets iterated after the
  link was pasted in); if the exact node ID 404s, don't give up — pull the metadata
  for the containing page/section and search by frame name instead. The frame is very
  likely still there under a new ID.
- Read the actual text nodes inside the matched frame(s): screen titles, button
  labels, option labels, **and defaults**. This is the vocabulary the test steps must
  use verbatim (e.g. if the design says a control shows "Yes"/"No", the step says
  "tap Yes", not "enable the toggle") — and the defaults are what the fresh-install
  cases in Step C verify against.
- Note the node ID of each frame you use — you'll link back to it per test case.

**Reconcile design against requirements as you go.** If the ticket's acceptance
criteria mention something the design doesn't show (a setting, a state, a screen),
don't silently drop it or silently invent it in the design's voice. Flag the gap in a
callout on the resulting page and leave it out of the step-by-step cases (there's
nothing real to click), rather than fabricating UI that doesn't exist yet.

## Step C — Plan coverage before writing any cases

Before writing a single test case, check off which of these categories apply to this
ticket. Writing straight into cases, one control at a time, is exactly how
default-state checks and checklist coverage get lost — plan the shape of the suite
first.

1. **Fresh-install / default state.** If Step A or Step B turned up documented
   default values, write a case (or one combined case covering several controls at
   once) that verifies the feature starts in that state. This is usually the first
   thing a real smoke test checks — skip it and the suite is already incomplete.
2. **Core entry & happy path.** How the user reaches the feature, and the primary
   success path for each control or option.
3. **Persistence & cross-navigation.** Settings surviving app restart, screen
   navigation, pre-/post-login, or anything else the ticket says should carry over.
4. **Cross-cutting / compliance requirements.** Everything from a linked checklist
   (accessibility, security, legal, …) and any AC bullet that isn't itself a single
   control. Write one case per checklist item, or group tightly related items into
   one case if running them together is genuinely how a tester would check them — but
   never skip the checklist just because it doesn't map to a single button.
5. **Edge & negative cases.** Interruption (backgrounding mid-action), rapid or
   repeated input, a device-level setting conflicting with the in-app one,
   offline/no-network access, and any boundary the design or AC explicitly calls out
   (min/max values, a control that's hidden on unsupported devices).

Not every ticket needs every category in depth — a single-toggle ticket may only need
one or two edge cases — but decide that deliberately for each category rather than
defaulting to writing only category 2.

## Step D — Write the granular test cases

Each case:

```
ID: TC-01
Type: Smoke | Regression
Priority: High | Medium | Low
Title: <short scenario title, in plain user language>
Preconditions: <starting state — screen, prior settings, logged-in state, etc.>
Steps:
1. <action, using the literal control/button label from the design>
2. <next action>
Expected result: <what the user sees/experiences — also in plain, observable terms, not implementation detail>
Ref: <which AC bullet or checklist item this covers>
Design: <link to the specific frame this was written from>
```

Guidelines:
- **One coherent user journey per case**, not one assertion per case. "Enable High
  Contrast Mode" is a case; "verify the API returns 200" is not — that's not
  something a user does.
- **Real UI language only.** If the design shows "Close" not "Back", write "Close".
  If a toggle reads "no" lowercase, keep the case.
- **Every step must name a concrete action.** Never write a placeholder like "trigger
  an event that has audio feedback" — a tester can't execute that. If the ticket or
  design names a specific event, use it. If it doesn't, pick the most obviously
  relevant concrete action already present elsewhere in the flow (a real button, a
  real screen transition) and use that instead of a vague generality.
- **Keep the assumption tag short in the step itself; put the reasoning in one
  callout, once.** If you're guessing which concrete action applies, mark the step
  with a brief tag like "(assumption — see note above)" and write the *actual*
  reasoning — what you assumed and why — a single time in a panel-note callout on the
  page, referencing every case that uses it. Don't paste the full rationale into
  every affected step; a step that reads "Tap Yes to change a control (assumption:
  since neither the ticket nor the design names a specific event for this setting,
  and X, and Y — confirm with design/dev)" makes a tester parse a footnote to find the
  actual instruction. Say what to do, tersely; say why once, elsewhere.
- **Tag Type and Priority honestly.** *Smoke* = the minimum set that proves the
  feature isn't broken: entry points, one happy path per control, defaults.
  *Regression* = everything else (every option value, persistence, edge cases,
  checklist items). Priority tracks how bad it is if this specific case fails, not
  how interesting the case is to write.
- **Fill in Ref for every case.** If a case doesn't trace back to an AC bullet or
  checklist item, that's a signal it may not be worth including — or that the
  requirement it covers should be added to Step A's list.
- **Link every case to a design frame**, even when several cases share the same
  screen — repeat the link rather than leaving it off.
- **Don't invent test cases for UI that isn't in the design.** If the requirements ask
  for something the design doesn't yet show, put it in the flagged callout from Step
  B instead.

**Assign the ID once, in whatever order you write the cases (grouped by Step C's
categories is fine) — IDs are stable identifiers and don't need to change later.** The
*order cases appear on the page* is a separate decision, made in Step F: sort for
reading/execution order, not authoring order.

## Step E — Condense into a regression layer

Add a second, independent layer above the granular suite: a small number of realistic,
continuous test cases that each chain several granular cases into one session, for
teams that need a fast routine regression pass rather than executing every isolated
case every cycle. This does not replace the granular table — it adds a layer on top of
it, so precise bug reporting against an individual granular case is still possible.

**Get the source cases.** If continuing directly from Step D, use those cases as-is.
If instead given an existing Confluence page that already has a granular `## Test
Cases` table (no fresh Step A–D run in this pass), read every row: ID, Type, Priority,
Preconditions, Steps, Expected Result, Reference.

**Naming: this is a second, independent test suite.** The condensed cases get their
own `TC-01, TC-02, ...` numbering, starting fresh, in the condensed section's own
table — not an extension of the granular one. This is deliberate even though it means
the same page has two different things both called "TC-01": the granular suite's
TC-01 and the condensed suite's TC-01 answer different questions (one isolated
assertion vs. one full session), so treating them as the same numbering line would be
misleading, not economical. State this explicitly in the section's intro paragraph so
nobody mistakes one TC-01 for the other. Do not call these "journeys," "RJ-," or
anything else that marks them as a different kind of artifact — to whoever runs them,
they are just test cases, only bigger and consolidated. Every one still needs its own
short **Title**, exactly like the granular table's cases do, not just a numbered id.

**Find natural chains first — mechanical, not a design choice.** For each case, note
its starting precondition and its ending state (what's true after the Expected
Result). Case B is a chain candidate onto case A when B's precondition is exactly what
A's expected result leaves true — same screen, same state, nothing missing in
between. Build these chains before applying any judgment calls below.

**Then decide what actually merges — a design choice, made deliberately per case:**

Merge into one condensed case when:
- Cases chain per the mechanical step above.
- It's a mistake-then-correction pair on the same field or control — an
  invalid-input case immediately followed by the valid-input case for that same
  field. This isn't a coverage loss; it's closer to how a real user actually behaves
  than testing the valid input in isolation.
- All accessibility-checklist cases for one screen **in one language state** collapse
  into a single accessibility pass of that screen (contrast + touch targets + labels
  + reading order together). Never merge LTR and RTL checks together — they are
  different application states, not variations of the same check.
- A case testing a wider version of the same input (e.g. "select 2 options") makes a
  case testing a narrower version of the same input (e.g. "select 1 option")
  redundant for a regression run. The narrower case stays in the granular table for
  completeness but doesn't need its own condensed case.
- Alternate methods of performing the identical single step (e.g. entering the same
  field by typing vs. dictation vs. autofill) can chain into one short condensed case
  — try method 1, clear, try method 2, clear, try method 3 — since none of them need
  to be carried all the way to completion to prove the method itself works.

Never merge — keep as separate condensed cases:
- Cases with mutually exclusive starting states (existing completed account /
  existing incomplete account / brand-new account, etc.). These are different
  branches of the system, not different points on one path, no matter how tempting it
  is to shorten the list.
- Destructive or slow cases — rate limits, lockouts, timers, anything requiring a
  wait or that deliberately breaks the normal flow. Keep these isolated so a failure
  there doesn't contaminate the "does the core flow still work" signal from the main
  case. (Cases that are both slow/destructive AND thematically identical, like a
  failed-attempt lockout and its related cooldown, may still combine with each other
  — just never with the main happy-path case.)
- Anything requiring a state reset partway through to continue (fresh install, log
  out and back in as a different account). Split at that point instead of forcing it
  through.

**Never silently drop a granular case.** Every original case must end up in exactly
one condensed case's "Covers" list. If a granular case genuinely doesn't fit anywhere
else and isn't worth expanding into its own multi-step case, give it its own
single-step condensed case rather than omitting it — the condensed table must be a
complete regression checklist on its own, with nothing requiring a cross-reference
back to the granular table just to know it needs running.

**Write each condensed test case.** Steps and Expected Result are two **parallel
numbered lists**, not one list with inline arrows — step *n* in Steps corresponds to
checkpoint *n* in Expected Result. A condensed case just has as many expected results
as it has steps, instead of one:

```
TC-01: <short title — what the user is realistically doing, end-to-end>
Preconditions: <starting state — the same kind of thing the granular table's Preconditions column holds, including any test data or pre-existing account state the tester must set up before starting>
Covers: TC-01, TC-02, TC-15, ... (original granular ids, for at-a-glance audit that nothing was dropped)

Steps:
1. <action>
2. <action>
...

Expected Result:
1. <what should be true right after step 1> (TC-XX)
2. <what should be true right after step 2>
...
```

- **Every condensed case needs its own Title and Preconditions**, same as the
  granular suite. Don't bury required setup inside step 1's action text — if the case
  needs a pre-existing account in a specific state, a specific test data value, or
  anything else true before the tester starts the clock, it goes in Preconditions.
- Every step gets its own numbered expected-result entry at the same position. Never
  batch several steps under one expected result at the end — if step 4 fails, the
  tester needs to know it failed at step 4, not have to guess which of eight actions
  caused a wrong final state three screens later. Don't fold the checkpoint back into
  the step text either (no inline "→") — the two lists stay visually and structurally
  separate.
- **Tag each expected-result entry with the original granular id it corresponds to**,
  e.g. `(TC-16)`, right in that list item — not just once in a summary Covers line at
  the top. The row-level Covers list is for auditing that nothing was dropped across
  the whole condensed table; the inline per-step tag is what actually lets a tester
  who hits a failure at step 6 report "TC-16 failed" without manually
  cross-referencing anything. A step that exists purely to move state along (opening
  a menu, navigating back) and doesn't itself assert anything from the granular suite
  gets no tag — leave it untagged rather than force a tag onto a connector step.
- **Never bundle two distinct actions into one step just because they happen on the
  same screen.** "Fill Name; select two Disability Type options" is two steps, not
  one — if only the disability-type selection actually gets checked in the expected
  result, the Name entry silently goes unverified. One step, one action, one
  checkpoint.
- **When a chain revisits a screen or a control the tester was already on** (e.g.
  Back to a previous screen, then forward again), the underlying mechanism is often
  genuinely unknown from the granular suite alone (does it re-trigger a fresh
  request, or resume exactly where it left off?). **Do not resolve this by picking
  the more plausible answer and stating it as fact** — that fabricates a requirement
  the source material never asserted, which is worse than leaving it ambiguous,
  because a tester or reviewer will treat it as verified when it isn't. Instead: (a)
  flag the ambiguity explicitly as unverified, in the same style as an assumption
  callout elsewhere on the page, and (b) where possible, rewrite the downstream steps
  to be robust to either resolution.
- **Never invent an unverified shortcut, feature, or mechanism to make a step more
  convenient.** If a step involves a real wait (an OTP expiring, a cooldown timer),
  say so plainly and let it be a real wait — don't suggest "a test/QA shortcut to
  force expiry" or similar unless the source material actually attests one exists.
- **Flag the real time cost on every case that has one, not only cases dedicated to
  that theme.** A case built primarily around something else can still have one step
  buried in the middle that requires a multi-minute wait — that case needs the same
  cadence note as a case that's entirely about rate-limiting (e.g. "Periodic — ~20+
  min, skip in fast cycles" under Priority).
- Use the literal UI language from the source cases — don't reparaphrase what the
  granular suite already got right.
- List every original granular id the case actually exercises in the row-level
  "Covers," including ones it passes through as a side effect.
- **Carry Design references into the condensed table too**, in whatever form the
  granular table used them, stacked under Covers the same way the granular table's
  own Reference column pairs a reference with its Design link.
- **When a case's steps reference "the same flow" as another case, name the exact
  underlying granular ids that flow consists of** — not another condensed-suite id,
  and not a vague gesture like "the full flow." Both suites share the numbering
  `TC-XX`, so an unqualified reference is genuinely ambiguous about which suite it
  points into.
- A condensed case's Priority is the highest Priority among the granular cases it
  covers.
- Condensed cases don't carry a Smoke/Regression Type tag — the condensed layer *is*
  the regression layer; Smoke stays a property of the granular table underneath.
- Assign the `TC-` id after sorting by Priority (High → Medium → Low) — ids follow
  display order in this suite, unlike the granular suite where ids are assigned at
  authoring time and only display order changes.

## Step F — Create the Confluence page

- Title: exactly `<TICKET-KEY> - <ticket summary>` (e.g. `MWA-394 - User can
  configure Language and Accessibility`) — match the ticket's summary text verbatim,
  don't paraphrase it.
- Location: create it as a child of the Confluence folder the user specified (or ask
  which folder/space if this is the first time and none was given — don't guess a
  location for a new user).

**Row order (granular table): highest priority first.** Sort Smoke-before-Regression,
then High-before-Medium-before-Low within each group, and leave ties in their Step D
authoring order. The ID label stays whatever was assigned in Step D; it will no
longer match row position, and that's fine — IDs are for referring back to a case,
row position is for "what do I run first."

**Column layout — granular table, six columns, and let the long ones breathe.** A
ten-column table where every column gets equal width is unreadable the moment a cell
holds more than one sentence — Preconditions, Steps, and Expected Result all do,
every time.

| Column | Contents |
|---|---|
| Case | `<ID>` in bold, then the title on the line below |
| Type / Priority | the Type lozenge, then the Priority lozenge, stacked |
| Preconditions | prose |
| Steps | ordered list |
| Expected Result | prose |
| Reference | the Ref text (paraphrase to the key term, e.g. "Meaningful a11y labels" not the whole checklist sentence), then the Design smart link, stacked |

**Column layout — condensed table**, same conventions: `Test Case` (bold id + title,
stacked) | `Priority` (+ cadence note where relevant) | `Preconditions` | `Covers`
(granular ids + Design smart link, stacked) | `Steps` (ordered list) | `Expected
Result` (parallel ordered list per Step E, inline `(TC-XX)` tags). No Smoke/Regression
split to sort by — sort rows by Priority (High → Medium → Low). Any granular case that
didn't fit a multi-step condensed case gets its own single-row, single-step entry, so
this table is a complete regression checklist without needing the granular table as a
companion. Neither table carries a Status column — tracking pass/fail per cycle is
left to wherever the team already tracks test execution, not to this page.

**HTML formatting — applies to both tables identically.** Set
`data-display-mode="fixed"` on each `<table>` with explicit `data-colwidth` on every
header and data cell, weighted toward the prose/list columns (Preconditions, Steps,
Expected Result) — the short lozenge/ID columns only need enough width for that. Set
`data-layout="full-width"` on both `<table>` tags too, so they aren't squeezed into
the narrower default content column — easy to drop since it doesn't show up when
reading the page's stored HTML back through the API, only in the live render, so
verify it in a browser if in doubt rather than trusting a re-fetch. For the Design
smart link, leave the anchor's inner content empty: `<a href="URL"
data-card-appearance="inline"></a>` — writing the raw URL as visible link text is an
easy copy-paste mistake that defeats the compact card Confluence would otherwise
render.

- Body, in order — **no Status column and no `## Run Log` section**, on either table,
  ever; this skill used to include both and they were deliberately removed. Pass/fail
  tracking across cycles belongs in whatever tool the team already runs test
  execution through, not as upkeep on this page:
  1. One short intro paragraph naming the ticket and what the page covers, plus a
     one-line size summary (e.g. "18 cases — 6 smoke, 12 regression").
  2. A warning-style callout for any design/requirements gaps found in Step B (omit
     this block entirely if there were none).
  3. `## Regression Test Cases (condensed)` — intro paragraph, then the condensed
     table from Step E.
  4. `## Test Cases` — then **one table**, one row per case in the sorted order
     above, from Step D.
  5. A one-line note telling the tester how to do a fast pass: "For a smoke pass, run
     only the rows tagged Type: Smoke" (these will already be at the top of the
     granular table).
- Use `getContentFormatGuide` for `createConfluencePage` before authoring the HTML
  body if you haven't recently — the page body format has real nesting rules (e.g.
  callouts can't contain tables, but table cells can contain lists and status
  lozenges) that are easy to get wrong from memory.
- After creating the page, share the resulting Confluence link back to the user —
  don't just say it's done.

## Worked examples

**MWA-394** ("User can configure Language and Accessibility") was fetched; its linked
Figma field pointed at a stale node ID, so the containing Figma section was searched
by name and the frame "2. Accessibility settings" was found under a new ID. The frame
showed four Yes/No-style controls (High Contrast, Sound, Haptic) plus a three-way Font
Size control (Smaller / Larger / Default), with a "Close" button — but the ticket's
acceptance criteria also called for a Theme (Light/Dark) setting the design didn't
show, which went into a callout rather than a fabricated case.

A first pass wrote 16 happy-path cases and stopped there — no default-state case, no
coverage of the linked accessibility checklist, no edge cases, and one step ("trigger
an in-app event that has audio feedback") that named no concrete action. Re-planned
against Step C's categories, the suite grew to 32: a combined default-state case, the
original happy-path cases now naming a concrete triggering action per case,
persistence and RTL cases, one case per relevant item from the linked accessibility
checklist, and edge cases for rapid tapping and backgrounding mid-change.

That second pass published as a ten-column table, sorted in writing order, with the
raw URL written out as the Design link text — dense and hard to scan, and a tester
still had to hunt across all 32 rows to find the 8 marked Smoke. A third pass sorted
rows Smoke-then-Priority and collapsed the table to six columns with fixed, weighted
widths and empty smart-link anchors. One problem remained even then: the Reference
column was too narrow for its longest entries (a checklist Ref ran 115+ characters in
a 170px column) and one step had the full assumption rationale pasted inline, burying
the instruction in a footnote — both fixed by paraphrasing Ref text down to short key
phrases and moving the assumption reasoning to a single callout.

Applied to the same page's suite in **Step E**: the happy-path cases chained almost
entirely into one condensed case covering 14 of the 32 granular cases in a single
11-step session (enable/disable each control in turn, triggering sound/haptic
feedback along the way). The accessibility checklist collapsed into one English-
language pass plus a separate RTL layout check — never merged together, since LTR and
RTL are different application states. Result: 32 granular cases condensed to 12 rows
numbered TC-01 through TC-12 in the condensed section's own sequence — a separate
namespace from the granular table's own TC-01 through TC-32 below it.

**MWA-367** (a registration flow, 30 granular cases: 9 smoke, 21 regression) condensed
further still: the happy-path cases chained into one 16-step case ("Complete PwD
registration end-to-end, correcting mistakes along the way") — start registration, get
an invalid mobile number rejected, correct it, test Back-preserves-the-field, fail OTP
twice (wrong, then expired) before succeeding, hit a missing-field error, fill a
multi-select and a conditional field, check the Terms and Conditions aren't hardcoded,
get blocked once for not accepting them, then finally submit — covering 14 of the
original granular cases, each mapped case tagged inline. The two existing-account
alternative flows stayed as their own condensed cases since they're mutually exclusive
starting states. OTP lockout and resend-limit cases combined with each other (both
slow, both about OTP abuse limits) but stayed isolated from the main case, picking up a
"Periodic — ~20+ min" cadence note. Alternate mobile-number entry methods (dictation,
autofill) chained into one short case trying each in turn. The international-number
case stayed standalone since merging it into anything else would have diluted the one
thing it specifically checks. Result: 30 granular cases condensed to 10 rows.

A first pass at the main case revisited the OTP screen (Back, then Continue again) and
asserted, as fact, that the second Continue re-requested a fresh OTP — but nothing in
the granular suite verified that; a guess dressed up as a stated requirement, worse
than leaving the ambiguity visible. The correction flagged the revisit as genuinely
unverified and rewrote the following step to work either way: "enter an OTP that
doesn't match the currently expected one" rather than "the one just sent." The same
pass had also suggested "a test/QA shortcut to force expiry" for the OTP wait — no
such shortcut was ever attested in the source material, so it was removed rather than
left in as an invented convenience, and the case picked up its own cadence note since
the wait is a genuine multi-minute cost buried inside an otherwise fast-looking case.
