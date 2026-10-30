# 005: ticket mode confirms the environment instead of a fixed `demo`

## What changed

`testing-api`'s ticket mode used to test every backend ticket on an environment
called `demo`, whatever the product config said. Products without a `demo`
environment couldn't run ticket mode, and products whose `demo` is kept for client
demos ran tickets in the wrong place. Now ticket mode tests only on an environment
the user named or confirmed for the run: it uses the one the message names, else
proposes the new optional `api.ticketEnvironment` and asks to confirm (a change may
be deployed elsewhere), else asks which environment to use. A config without the
field keeps working; its runs just ask. Each product with an `api` block needs one
decision: which environment to propose, or none.

## Is it needed

Needed if any product config in `~/.claude/environments/` has an `api` block
without `api.ticketEnvironment`. A product whose answer was "none, ask every time"
stays without the field; the applied-migrations record keeps this from asking again.

## Steps

1. **List (runs by itself).** For each product config with an `api` block and no
   `ticketEnvironment`, show its `api.defaultEnvironment` and the collection's
   environment names (the files in `<api.repo>/<api.collectionPath>/environments/`,
   without their extensions; for an Insomnia export, the environments inside it).
   Configs of one product that share a collection can be asked about together.
2. **Ask (asks; no default).** Ask which environment backend tickets are usually
   tested on, to be proposed for confirmation on every ticket run. Offer the
   collection's environment names plus "none, ask every time" (for products whose
   tickets land on different environments). Mention that until now ticket mode used
   `demo`, so a team that relied on that should pick `demo` if it's in the list.
3. **Write (runs by itself after the answer).** For an environment name, add
   `"ticketEnvironment": "<answer>"` to the `api` block of each of that product's
   real config files (`readlink` the link in `~/.claude/environments/`), right
   after `defaultEnvironment`, and show the diff. For "none", leave the configs as
   they are.

## Verify

- `python3 -I <QA_Agent>/environments.example/validate_environments.py` passes.
- `check_setup.py --full` reports no WARN "api.ticketEnvironment is ..., but the
  collection's environments are ...".
