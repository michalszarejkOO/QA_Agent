# Maestro e2e flows

Black-box UI flows run with [Maestro](https://maestro.dev) against an app already installed on a
simulator or emulator. No test target, no rebuild when a flow changes.

## Project specifics

| | |
|---|---|
| App id (debug build) | `com.example.app.debug` |
| How to install the build | _fill in_ |
| Launch arguments the app reads | _fill in (where they are handled in the app code)_ |
| Start subflow | `subflows/launch-app.yaml` |

## Running

```bash
maestro test .maestro                                         # every flow from config.yaml
maestro test --include-tags smoke .maestro                    # by tag
maestro test .maestro/flows/smoke/app-starts.yaml

.maestro/run-flows.sh -d <device-id> -r 5 -o <output-dir> <flow-name>   # rounds, summary.txt + junit.xml
.maestro/run-flows.sh -d <device-id> -t smoke
```

- **`maestro test`** while writing or fixing a flow, and for a quick run of the suite or a tag. It
  runs everything in one Maestro session, so a driver crash can fail the flows after it.
- **`run-flows.sh`** for the 5 runs a test needs before merge, stability series and CI. Each flow
  gets its own session, a driver crash is rerun once and reported as `INFRA_RETRY` instead of a
  failure, and `summary.txt` lists PASS / FAIL and the time of every flow.

Start long runs on a freshly booted simulator or emulator.

## Layout

| Path | Contents |
|------|----------|
| `config.yaml` | Runs `flows/**` only, skips `wip` |
| `flows/<feature>/` | Tests, one user scenario per file |
| `subflows/` | Reusable steps (`launch-app`, ...) |
| `scripts/` | JavaScript for data computed at run time (dates, URLs) |
| `run-flows.sh` | Runs flows in rounds, one Maestro session per flow, reports driver crashes separately |

## Standard

1. **Layout:** a test lives in `flows/<feature>/` and covers one user scenario. Reusable steps live
   in `subflows/`, JavaScript in `scripts/`. Only `flows/**` is run as tests.
2. **Start:** every test starts from a clean install through the shared start subflow.
3. **Selectors:** `id` first. Finding an element by `text` only where it has no id, with a comment
   saying why; asserting a displayed value by its text is fine. Never coordinates. `index` only
   together with `id` or `text`.
4. **Waiting:** always on screen state (`extendedWaitUntil`, `enabled: true`), never `sleep`.
5. **Reuse:** a step used by two or more tests moves to a subflow; a step used once stays in its test.
6. **`retry`:** only around a named external cause (e.g. a backend error on start), with a comment.
   Never around a whole test: it hides real problems.
7. **Tags:** a feature tag on every test, `wip` for unfinished ones, `smoke` for the PR subset. A
   `smoke` test covers a critical path, has passed 5 runs in a row and keeps the whole subset short.
   There is no tag for the full suite: it is every test not tagged `wip`.
8. **Before merge** a new or changed test passes 5 runs in a row
   (`run-flows.sh -d <device-id> -r 5 <flow>`): failures in 1-5% of runs do not show up in one or two.
9. **Test data:** no real credentials in flows. Test accounts come from `env` / CI secrets
   (`maestro test -e USER_PASSWORD=...`).

`run-flows.sh` refuses to start when a flow or subflow uses `sleep` or `point`.
