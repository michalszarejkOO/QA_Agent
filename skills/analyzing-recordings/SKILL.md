---
name: analyzing-recordings
description: Analyzes a screen recording or screenshot file the user points to (a path to .mov, .mp4, .webm, .png, .jpg) in the context it belongs to (product, ticket, environment) inside a subagent, so frames never enter the main conversation. Extracts only the frames where the screen changes, describes what happens and when, judges it against the ticket, and hands back text plus a few key frames saved in the product's working directory. Feeds reporting-bugs when it shows a defect.
when_to_use: "Trigger on: 'przeanalizuj filmik', 'zobacz to nagranie', 'co jest na tym screenie', 'analyze this recording', a path to a video or image file with a question about it, a screen recording attached as evidence for a bug. Do NOT trigger for evidence the QA run records itself (testing-apps) or for a Figma comparison (qa-tester)."
---

# Analyzing recordings and screenshots

Every image read in a conversation stays in its context and is sent again with
every later turn: a 20-frame look at a recording is about 30,000 tokens on
each prompt until `/compact` or `/clear`. So the frames are read in a
subagent, and the main conversation keeps only its text answer.

## Where it happens

1. **Main conversation: never open the file.** No Read on the image, no frames
   extracted here. Check only that the path exists (`ls -la <path>`).
2. **Collect the context** from what the user said, asking only what is
   missing and needed:
   - the question: what to look for ("is this a bug", "what went wrong",
     "does it match the ticket", "what happens after the click");
   - the product: match a ticket key or URL against `~/.claude/environments/*.json`
     (or `$CLAUDE_CONFIG_DIR/environments/`) for its `workDir` and project skill;
   - the ticket key, environment, account or role, when the user gave them.
     Don't read the ticket here; the subagent does.
3. **Output folder:** `<workDir>/qa-evidence/<ticket key, or YYYY-MM-DD-short-name>/recordings/<file name without extension>/`.
   No product matched: a new folder from `mktemp -d`, said to be temporary.
   Never the Desktop or the folder the recording is in.
4. **Say in one line what will happen** (file, ticket, question, model), then
   **start a subagent** (`general-purpose`, model `sonnet`; `opus` for this run
   only when the user asks) with the brief and this instruction: "Load the
   analyzing-recordings skill and follow 'The analysis' inside a subagent. You
   can't ask the user: if something blocks the analysis, stop and report what
   is needed."
5. **Relay its answer** as it comes. It stopped with a question: ask the user
   and continue the same subagent. A defect → offer `reporting-bugs` with the
   answer's observations and the key frames and recording as attachments
   (`find-duplicates` runs first there).

**A screenshot pasted into the conversation** (not a path) is already in the
main context and a subagent can't see it. Answer it there. In a long thread,
add one line at the end: next time give the file path instead of pasting, or
run `/compact` once the screenshot is no longer needed.

**If you are that subagent:** the brief is done; start at "The analysis".

## The analysis

1. **Context first,** before looking at frames, so you know what correct looks
   like: the ticket with the `reading-jira-tickets` skill (acceptance criteria,
   comments, the steps of a bug), and the product's project skill when the
   brief names one (its gotchas often explain what's on screen).
2. **Frames.**
   - An image file: read it as it is.
   - A recording: run
     `python3 -I ~/.claude/skills/analyzing-recordings/scripts/extract_frames.py <recording> <output folder>/frames`.
     It keeps the frames where the screen changes (16 at most, 1280 px wide)
     and prints each one with its second. Read them in order.
   - Too few to see what happens (a typed value, a fast toast): run again on
     the stretch that matters with `--threshold 0.03`, or more frames with
     `--max 24`. The cap spreads frames evenly over the recording, so for a
     long one with many changes, raise `--threshold` (0.15) to keep the real
     screen changes. Over 40 frames in total: stop and say what you have.
   - `ffmpeg` missing: stop and report `brew install ffmpeg`.
3. **What to read in each frame:** the screen and its URL or title, what
   changed from the previous frame, messages, toasts, error codes, values in
   fields, loading states, the language and direction (RTL), anything cut off
   or overlapping. A value you can't read clearly is "unreadable", never a
   guess.
4. **Judge it** against the question and the ticket: where it differs from the
   acceptance criteria or the expected result, and from which second. Whether
   it is a bug, expected behaviour, or can't be told from the recording alone
   (what would settle it: a network log, the account's data, a database read).
5. **Key frames:** copy two or three frames that prove the answer into
   `<output folder>/key/`, named for what they show
   (`03-error-toast-t12.4s.png`). Leave the rest in `frames/`.

## What to hand back

Text only, never the images:

1. **Answer** to the question, in one or two sentences.
2. **Timeline:** one line per step, the second and what happens
   (`0:12 clicking Submit shows "Something went wrong"`).
3. **Against the ticket:** what matches and what doesn't, naming the
   acceptance criterion; or "no ticket given".
4. **Bug or not,** with the reason. For a bug: steps to reproduce as far as the
   recording shows them, expected, actual, and what the recording doesn't show
   (environment, account, data) that the report still needs.
5. **Files:** the key frames and the frames folder, as full paths, one per
   line.
