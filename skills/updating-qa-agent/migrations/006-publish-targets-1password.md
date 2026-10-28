# 006: collections and environments are published to 1Password or Confluence, per part

## What changed

`testing-api` used to zip the whole collection, environments and `.env` files
included, and attach it to a Confluence page, which is how live tokens leaked. Now
the collection zip never holds environments or `.env` files, environments are
exported separately, and each part goes where the product config says
(`api.publish`: `1password`, `confluence` or `none`). Anything going to Confluence
passes a secret scan first. Before any upload the run reads the published version,
warns about a newer one and waits for the user's yes. The 1Password CLI (`op`) is
required once a product publishes to 1Password: `setup.sh` keeps it installed and
`check_setup.py` fails without it. Setups without such a product (UI testing only)
don't need it.
A config without `api.publish` still works: its collection goes to Confluence if it
has `api.confluence`, and its environments go nowhere.

## Is it needed

Needed if any product config in `~/.claude/environments/` has an `api` block
without `api.publish`, or if one sends a part to `1password` while `op` isn't
installed (`command -v op` prints nothing). A setup with no `api` block at all
doesn't need it.

## Steps

1. **Per product (asks).** For each product with an `api` block and no
   `api.publish` (configs of one product that share a collection are asked about
   together), show what it has now (`api.confluence` and its
   `secondaryAttachments`, if any) and ask:
   - where the collection goes: `1password`, `confluence` or `none` (default: what
     it does today, `confluence` with an `api.confluence` block, otherwise
     `1password`);
   - where the environments go: `1password` (default), `confluence` or `none`. For
     `confluence`, say that the page is readable by everyone with access to it and
     that the secret scan will stop on tokens.
   - For a `1password` part: the item names, offering `<Product> <Client>
     Collection` / `<Product> <Client> Environments`. The vault comes in step 4.
2. **Install op, only if a part goes to 1password (runs by itself; asks only if
   Homebrew is missing).** If `op` is missing, run
   `brew install --cask 1password-cli`. Without Homebrew, give the user
   https://developer.1password.com/docs/cli/get-started/ and wait. Then ask the
   user to open the 1Password app > Settings > Developer, turn on "Integrate with
   1Password CLI", then run `op vault list` and have them approve the 1Password
   dialog it opens (`op whoami` reports "not signed in" even when the integration
   works, so don't use it as the check). Never ask for or type their password. If they want to finish later, stop here and leave the
   migration pending.
3. **Postman products (asks).** For a product with `client: "postman"` and a
   target, check the Postman MCP server is signed in (`getAuthenticatedUser`); if
   not, start its `authenticate` and let the user approve in the browser. Explain
   the team rule from `testing-api`'s `adapters/postman.md`: shared variables,
   keys included, as plain variables with a Shared Value. Signing in can wait;
   publishing then asks the user about app changes instead of checking.
4. **Vault (asks).** For each `1password` product, look for items with the chosen
   titles (`op item list --format json`) and take their vault
   if a teammate already created them; otherwise list `op vault list --format
   json` and ask.
5. **Write (runs by itself after the answers).** Add the `publish` block to the
   `api` block of each of that product's real config files (`readlink` the link in
   `~/.claude/environments/`), after `ticketEnvironment` or `defaultEnvironment`,
   and show the diff. Configs can hold secrets: never print anything but the diff
   of this block.
6. **Old attachments (asks, changes nothing by itself).** If a product's
   environments used to go to its Confluence page (`secondaryAttachments`) and now
   go elsewhere, tell the user those files are still attached to the page with
   whatever tokens they held, and that removing them is their call in Confluence.
   Don't delete anything.

## Verify

- When a part goes to 1Password: `command -v op` finds it, and `op vault list`
  works after the user's approval.
- `python3 -I <QA_Agent>/environments.example/validate_environments.py` passes.
- `check_setup.py --full` reports no FAIL about the 1Password CLI (it only checks
  when a product publishes to 1Password).
