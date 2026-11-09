# 014: Everything for a ticket in the ticket's folder

## What changed

Everything made for one ticket now lives in that ticket's folder,
`<workDir>/qa-evidence/<TICKET>/`: its test cases (`test-cases.md`), the runs'
evidence, and a `notes/` subfolder for the SQL, notes, plans, scripts and data
dumps made for it, including API requests made only to prepare data for a
test (`api-runs/` stays for `testing-api` runs). Before, project skills sent
all of that to the product's top-level `notes/` or `scripts/`, so one ticket's
files were spread over several folders, with the ticket key only in the file
name. The top-level `notes/` and `scripts/` now hold only what applies to the
whole product (a shared account setup, a tool, a reusable script). New project
skills get this rule from the template; this migration updates existing ones
and, after asking, gathers the ticket files from anywhere in the working
directory into their ticket folders.

## Is it needed

For each product config in `~/.claude/environments/` (or
`$CLAUDE_CONFIG_DIR/environments/`), needed when either is true:

- it has `projectSkill` and no file in that folder mentions
  `qa-evidence/<TICKET>/notes/` (or `<workDir>/qa-evidence/<TICKET>/notes/`);
- a **ticket file** is outside its ticket folder: a file or folder whose name
  starts with a ticket key (one of the product's `ticketPrefixes` in any case,
  then `-`, `_` or nothing, then a number, e.g. `IP-150-expire-payment.sql`,
  `IP-210/`, `ip329_list.py`, `ip340-vat.png`), found directly in `<workDir>`
  or in a folder right inside it, or one level deeper (such as
  `scripts/fixtures/`). Not searched: `qa-evidence/` (already the ticket
  folders), `api-runs/` (`testing-api` runs stay there), and any folder that
  is a git repository, the project skill, the config folder or the
  collection's local copy (`api.localCopy`, `postman/`).

Otherwise not needed. Once applied it isn't asked again, also for products the
user chose to leave as they are.

## Fresh install

`skip`: new project skills come from the template, which already has the rule,
and a new working directory has no old files to gather.

## Steps

1. **Look (runs by itself).** Per product (one product's configs for several
   environments count as one):
   - in its project skill folder, every line that sends files to the top-level
     `notes/` or `scripts/` (the "Every file you create" rule, and paths such as
     `notes/<TICKET>-<what>.sql` in other skills or references there);
   - every ticket file outside its ticket folder (as in "Is it needed"), with
     the key it belongs to, written as `IP-150`;
   - files in the same folders whose name has no ticket key but whose first 20
     lines name exactly one ticket of this product (e.g. a SQL file headed
     `-- IP-228: free establishment`): these are **maybe** ticket files;
   - in `api-runs/`, run folders named after a ticket that hold no collection
     export, report or CLI result, only requests or scripts that prepared data:
     also **maybe** ticket files.
2. **Explain (runs by itself).** Say in short, in the user's language:
   everything made for one ticket (SQL, notes, plans, scripts, data dumps, API
   calls that only prepared data) now goes to that ticket's folder,
   `qa-evidence/<TICKET>/notes/`, next to its test cases and evidence, so one
   ticket is in one place. The top-level `notes/` and `scripts/` keep only what
   applies to the whole product, and `api-runs/` keeps `testing-api` runs.
   Then show, per product:
   - the project skill lines from step 1 and how they will read;
   - the files to move, grouped by ticket, as one line per file with where it
     is now and where it goes;
   - the **maybe** files separately, with the line that names the ticket.
3. **Ask once per product (asks).** "Gather everything made for tickets into
   the ticket folders for this product?":
   - **Yes: update the rules and move all ticket files** (recommended);
   - yes, and go through the **maybe** files one by one (shown only when step 1
     found any): ask per file "Move to `qa-evidence/<KEY>/notes/`?", default
     **move**;
   - update the rules only, leave the files where they are;
   - leave the product as it is.

   With nothing to move (only the rules are missing), ask "Update the rules for
   this product?" with **Yes** (recommended) and "leave it".
4. **Do it (runs by itself).**
   - Rules: replace the "Every file you create" rule's sentence about notes
     with the template's wording
     (`configure-project/assets/project-skill-template.md`), and change each
     per-ticket path from step 1 to `<workDir>/qa-evidence/<TICKET>/notes/...`.
     Leave paths to the product's own tools in `scripts/` alone.
   - Files: move each one to `<workDir>/qa-evidence/<KEY>/notes/` with its name
     unchanged, creating the folders as needed. A folder named exactly after
     the key moves its contents there; a file from a subfolder such as
     `scripts/fixtures/` goes to `notes/fixtures/`; a data-prep folder from
     `api-runs/` goes to `notes/api-data-prep/`. Drop `__pycache__` folders
     instead of moving them. Never overwrite: if the target exists, leave the
     file and list it. Leave an emptied folder only if it is `notes/` or
     `scripts/`; remove other empty folders the move left.
   - Paths to a moved file inside other files of the working directory (e.g.
     `qa-evidence/<KEY>/test-cases.md`, `known-issues/`, a run log) are
     updated too.
   - Commit in the project skill's repo only the files changed here, and only
     when they had no other uncommitted changes; otherwise leave the commit to
     the user and say so.
5. **Show the result.** Per product: the lines changed, how many files moved
   into which ticket folders (and the list), anything left in place and why,
   or "left as it is".

## Verify

- Every product the user updated mentions `qa-evidence/<TICKET>/notes/` in its
  project skill.
- For products whose files were moved, no ticket file is left outside its
  ticket folder (as in "Is it needed"), except ones listed as left in place.
