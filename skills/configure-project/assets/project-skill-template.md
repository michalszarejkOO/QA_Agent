---
name: {{PRODUCT}}
description: Project map for {{PRODUCT_TITLE}} (Jira prefix {{TICKET_PREFIXES}}) — where its code, API collection, environment config, Jira/Confluence and tools live, which environment to test on, and the project's known gotchas. Load it first whenever a task touches {{PRODUCT_TITLE}}, then hand off to the generic skills (testing-api, qa-tester, testing-apps, writing-test-cases, reporting-bugs) with the right paths and context.
when_to_use: "Trigger on any mention of {{PRODUCT_TITLE}}, a {{TICKET_PREFIX_EXAMPLE}}-<number> ticket or a {{JIRA_SITE}}/browse/{{TICKET_PREFIX_EXAMPLE}}-… link, or the {{PRODUCT_TITLE}} environment URLs ({{URL_HOSTS}}). Load before testing-api / qa-tester / writing-test-cases for a {{PRODUCT_TITLE}} ticket. Do NOT trigger for other products — they have their own skill."
---

# {{PRODUCT_TITLE}}

{{ONE_PARAGRAPH_WHAT_THE_PRODUCT_DOES}}

**This skill is where everything specific to {{PRODUCT_TITLE}} lives**: gotchas,
test data rules, workflows, links, lessons from earlier runs. When you learn
something new about this project, propose adding it here (after the user
approves), never to the generic QA_Agent skills and never to Claude's memory.
It lives in the project's working directory, so it goes away with the project.

**Every file you create for {{PRODUCT_TITLE}} goes into its working directory,
`{{WORK_DIR}}`, wherever Claude was opened**: test output goes where the testing
skills put it (`qa-evidence/`, `api-runs/`, `worktrees/`, `reports/`), and anything
else (notes, plans, scripts, SQL, exports, data dumps) goes into `notes/` or
`scripts/` there, created as needed. Never into the current folder, the Desktop,
`/tmp` or `~/Downloads`. Give the full path of anything you save.

## Where things are

| What | Where |
| --- | --- |
| Working directory (all QA output: evidence, API runs, worktrees, reports) | `{{WORK_DIR}}` |
| Environment config (URLs, logins, collection, Jira connector) | {{ENV_FILES}} |
{{REPO_ROWS}}
| Jira / Confluence | `{{JIRA_SITE}}`, connector `{{JIRA_CONNECTOR}}` |
| This skill | `{{SKILL_DIR}}` (symlinked to `~/.claude/skills/{{PRODUCT}}`) |

## Environments

{{ENVIRONMENTS_TABLE}}

## Before you start a {{PRODUCT_TITLE}} task

1. Read the ticket and its acceptance criteria.
2. Check "Rules for this project" below before touching test data.

## Rules for this project

- (none recorded yet)
