# 007: gather each product's files from elsewhere into its working directory

## What changed

Since 001 everything about a product lives in its `workDir`, but files made
before that still sit elsewhere: collection exports on the Desktop (the old export
default), staged uploads with live tokens in the QA_Agent repo's `.upload-tmp/`,
quality reports (`*-quality-*.html`), `api-runs/` / `qa-evidence/` / `qa-video/`
folders in whatever folder Claude was opened in, invoices and screenshots in
Downloads. `find_project_files.py` (read-only) finds them and says where each
would go; this migration offers to move them, asking before every move.
`configure-project` runs the same search when it adds a product, and
`checking-qa-agent` reports how many are left. Products can list extra
file-name words in the new optional `legacyFileKeywords`.

## Is it needed

Run `python3 -I <QA_Agent>/skills/updating-qa-agent/scripts/find_project_files.py --summary`.
Needed if it prints anything but `none`. The search can be run again any time;
answering "leave" for everything is a valid way to finish.

## Steps

1. **Keywords (asks; default: none).** For each product, ask for words that
   appear in its file names besides the ticket prefix and the product name (e.g.
   `Assessment Invoice` for invoices). Add them to the product's real config files
   as top-level `"legacyFileKeywords": [...]` and show the diff. Skip when the user
   has none.
2. **Search (runs by itself).** Run `find_project_files.py` without arguments.
   It looks only on the Desktop, in Downloads, Documents (2 levels), the QA_Agent
   repo (files git doesn't track) and `~/Projects` (3 levels, run folders only),
   never inside a product's `workDir`. Each match comes with its product (or
   "unassigned"), size, the reason it matched, a suggested destination in that
   product's `workDir`, and `[SECRETS]` if the secret scan flags it. File contents
   are never printed.
3. **Move (asks before every move; default: leave).** Show the matches per
   product, grouped by suggested destination, and ask per group: move, leave, or
   pick single files. **Never move without that yes, never delete anything.**
   Move with `mv -n` so nothing at the destination is overwritten; give a taken
   name a `-2` suffix. For `.upload-tmp/` in the QA_Agent repo, say it held live
   tokens and is gitignored since Fix nr 1.
4. **Unassigned (asks).** List what matched no product (collection exports,
   reports of a product not configured here). Ask whether any belongs to a
   product; move only those the user names, the rest stays.
5. **Secrets (information).** Point out `[SECRETS]` files left on the Desktop or
   in Downloads; moving them into a `workDir` or deleting them is the user's call.

## Verify

- `python3 -I <QA_Agent>/environments.example/validate_environments.py` passes.
- Every move the user approved happened: the file is at its destination and gone
  from the old place. What the user chose to leave is listed in the summary.
