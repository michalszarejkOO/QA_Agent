# Web adapter (Playwright)

Load this when the target is a URL.

## Fresh session, every run

Always start from a fresh, unauthenticated state and sign in yourself as part of
the run — never assume or rely on a session the browser happens to already be
authenticated with from an earlier run. If `browser_navigate` to the pinned app URL
lands you in an already-logged-in state, sign out first (or clear the session) and
log back in through the real flow, so the credential actually used is the one this
run chose, not leftover state.

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
