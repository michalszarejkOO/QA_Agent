# Web adapter (Playwright)

Load this when the target is a URL.

## Which Playwright server

Use the `playwright-video` MCP server (`mcp__playwright-video__browser_*`) for the
whole run. It's the same Playwright MCP started with `--caps=devtools`, so it
also has the video tools. The plugin's `playwright` server
(`mcp__plugin_tsh-product-testing_playwright__*`) is a separate browser with a
separate session. Never mix the two in one run, or the recording, sign-in and
screenshots end up in different browsers. Fall back to the plugin server only
if `playwright-video` isn't connected, and report that videos weren't recorded.

## Fresh session, every run

Always start from a fresh, unauthenticated state and sign in yourself as part of
the run — never assume or rely on a session the browser happens to already be
authenticated with from an earlier run. If `browser_navigate` to the pinned app URL
lands you in an already-logged-in state, sign out first (or clear the session) and
log back in through the real flow, so the credential actually used is the one this
run chose, not leftover state.

## White screen / environment glitches

A blank/white page, a stuck spinner, or a broken/unstyled layout right after
navigating or acting is more often a transient environment hiccup than a real
defect. Before treating it as a bug: reload (`browser_navigate` to the same URL,
or a full refresh) once, re-check with `browser_snapshot`/`browser_take_screenshot`,
and if it's still broken, retry a couple more times. Only after several refreshes
still fail to recover should you stop treating it as a fluke — report it as an
environment blocker (not a product bug) rather than continuing to test around it.

## Procedure

1. `browser_navigate` to the pinned app URL.
2. `browser_snapshot` to see structure and get element refs first — do not assume a
   conventional email+password login. Server-level HTTP Basic Auth and the app's
   own sign-in form are two separate gates; the sign-in form itself may key off
   something other than email (national/company ID, SSO-style single field, magic
   link). Inspect what's actually on the page before typing credentials into a
   guessed field.
3. Before driving the UI toward any particular state, read `browser_network_requests`
   and the underlying API responses first — see "Shared discipline" in the parent
   skill (`../../SKILL.md`).
4. Walk each scenario with `browser_click` / `browser_type` / `browser_select_option`
   / `browser_fill_form` / `browser_press_key`. Use `browser_wait_for` for async
   state instead of guessing timing.
5. At each meaningful checkpoint, `browser_take_screenshot` and actually look at it
   before judging pass/fail.
6. Use `browser_console_messages` and `browser_network_requests` whenever a
   criterion concerns errors, loading states, or API behavior.
7. Record a video of every scenario and save bug folders per "Recording" below.

## Recording

What to record, and where it goes, is set in the parent skill's "Recorded
evidence" section. The web mechanics:

- **Video:** call `browser_start_video` with a `filename` such as
  `qa-video/<scenario-id>-<slug>.webm`, then call `browser_stop_video` when the
  scenario ends. Do this for every scenario, not just the happy path. These
  tools exist only on a server started with `--caps=devtools` (`playwright-video`, above). If they aren't in your tool
  list, no video can be recorded this run. Report that, and keep going with
  screenshots only.
- **Convert to MP4:** Playwright records WebM only, which QuickTime and Jira
  previews play poorly. After moving the video into the run folder, convert it
  and keep the `.mp4` as the evidence file:
  `ffmpeg -hide_banner -loglevel error -y -i <name>.webm -c:v libx264 -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -movflags +faststart -an <name>.mp4 && rm <name>.webm`.
  If `ffmpeg` is missing or the conversion fails, keep the `.webm` and say so
  in the report.
- **Where it goes:** the video's place in the run folder is
  `testing/<category>/<scenario-id>-<slug>.mp4`. If the scenario failed, add `-FAIL` to its
  name and `cp` it to `bugs/<bug-n>-<slug>/video.mp4`.
- **Bug screenshot:** call `browser_take_screenshot` with a `filename`, then `mv`
  it to `bugs/<bug-n>-<slug>/screenshot.png`.
- Playwright MCP resolves a relative `filename` against its workspace root and
  refuses paths outside it. Pass a relative name, read the saved path from the
  tool result, then `mv` that file into the run folder. Don't pass the run
  folder's absolute path directly.
