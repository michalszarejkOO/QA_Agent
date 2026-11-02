# 012: Test cases in a separate Postman tests collection

## What changed

`testing-api` can keep test cases in a second Postman collection,
`api.testsCollection`, next to the main one and sharing its environments.
Ticket mode puts every generated case there, in the main collection's domain
folders with one folder per endpoint, and adds only one happy-path request per
new endpoint to the main collection, without a ticket key in its name. Every
run executes the tests collection. Before, a ticket run added all its cases to
the main collection, in a folder named after the ticket, so the collection
people use in the Postman app filled up with dozens of cases per endpoint. The
tests collection is published as a third part, `tests`, in its own 1Password
item (`api.publish.tests`, `onePassword.testsItem`). A product that doesn't
set it works as before. Also new: a collection folder may hold several main
collection files; they are published and downloaded together in the
collection item.

## Is it needed

Needed when a product config in `~/.claude/environments/` (or
`$CLAUDE_CONFIG_DIR/environments/`) has `api.client: "postman"` and no
`api.testsCollection`. Otherwise not needed. Once applied it isn't asked
again, also for products the user chose to keep as they are.

## Fresh install

`skip`: configure-project asks about the tests collection for every new
Postman product (product-config.md step 5).

## Steps

1. **Explain and ask once per product (asks).** List the products that need
   it (one product's configs for several environments count as one). Say in
   short: test cases the agent generates can go into a separate collection
   that runs execute, so the main collection keeps one request per endpoint in
   its own folders and stays readable in Postman; the tests collection is
   published to its own 1Password item next to the other two. Ask per product
   "Keep test cases in a separate tests collection?":
   - **Yes** (recommended), then its name, suggesting the main
     collection's name with `_TESTS` (e.g. `ACME_TESTS` next to `ACME`), so the
     two are easy to tell apart after an import into Postman, and, when the collection goes to 1Password,
     the item title, suggesting `<Product> Postman Tests`;
   - no: the configs stay as they are.
2. **Update the configs (runs by itself).** In every config of each product
   with a yes, add `api.testsCollection` with the name, and
   `api.publish.tests` (`"1password"` when `api.publish.collection` is
   `1password`, otherwise `"none"`) with `api.publish.onePassword.testsItem`
   for 1Password. Show the diff and run the validator. Don't create the
   1Password item: the first run starts the tests collection and the first
   publish creates the item, after the user's yes.
3. **The project skill (asks only if something is found).** Search each
   affected `<projectSkill>` for rules on where test cases go in the
   collection (saved examples, a folder per ticket, assertion-heavy requests).
   None: say so and go on. Found: show each line with a replacement (cases go
   into the tests collection; the main collection gets one happy-path request
   per endpoint in its domain folder) and apply on a yes. Commit in the project
   skill's repo only if the changed files had no other uncommitted changes;
   otherwise leave the commit to the user and say so.
4. **Show the result.** Products changed, the new fields, project skill lines
   changed, and that the first run per product starts the tests collection
   and offers to publish it. Cases already in the main collection stay where
   they are; moving them is a separate change the user can ask for.

## Verify

- `validate_environments.py` prints ok for every changed config.
- Each changed config has `api.testsCollection`, and `api.publish.tests` with
  `onePassword.testsItem` when it is `1password`.
