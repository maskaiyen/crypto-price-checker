# Development Process

This document explains how `crypto-price-checker` was built — the tools, workflow, division of labour, and lessons learned from an AI-assisted development process.

## Overview

The project was built entirely using **Claude Code (web version)** as the coding assistant, with **GitHub** handling version control, issue tracking, and pull request review. No code was written by hand. Every file — Python modules, tests, Dockerfile, and documentation — was produced by Claude Code in response to natural-language task descriptions.

## Tools Used

| Tool | Purpose |
|---|---|
| Claude Code (web) | Writing all code, tests, and docs; running git operations |
| GitHub Issues | Defining features as discrete, trackable units of work |
| GitHub Branches | One branch per issue, always created from latest `main` |
| GitHub Pull Requests | Code review gate before merging to `main` |
| Branch Protection | Prevented direct pushes to `main`; enforced PR workflow |

## Development Workflow

Each feature followed this cycle:

```
GitHub Issue
    ↓
Claude Code creates branch from latest main
    ↓
Claude Code writes code + tests
    ↓
Claude Code commits and pushes
    ↓
Claude Code opens PR
    ↓
Human reviews PR
    ↓
Merge to main (or request changes)
```

Branches were always created from the latest `main` and never used cherry-pick, keeping history clean and conflicts localised to the branch under review.

## Claude Code's Role

Claude Code handled all implementation work:

- Writing every Python module (`main.py`, `validator.py`, `database.py`, `dashboard.py`, `scheduler.py`, `alerter.py`)
- Writing all tests across five test files (74 tests total)
- Writing infrastructure files (`Dockerfile`, `docker-compose.yml`, `.dockerignore`)
- Writing and updating all documentation (`README.md`, `DEVELOPMENT.md`)
- Running all git operations: branching, committing, pushing, and opening PRs
- Rebasing and resolving merge conflicts when branches diverged from `main`

## My Role

The human role in this workflow was to:

- Define requirements for each feature as a GitHub Issue or direct prompt
- Review pull requests and decide whether to merge or request changes
- Catch mid-task direction changes (e.g. switching from multiple output formats to JSON-only mid-implementation)
- Steer architectural decisions (e.g. replacing CSV with SQLite)
- Resolve situations where Claude Code needed explicit guidance (conflicting branch history, force-push confirmation)
- Write this document's requirements

No code was written, edited, or debugged by hand.

## Key Learnings

### What worked well

- **Issue-driven development** — giving Claude Code a well-scoped issue with explicit acceptance criteria produced clean, focused PRs with minimal back-and-forth.
- **Test-first thinking** — asking for tests alongside implementation kept quality high and made refactors (CSV → SQLite, text output → JSON) safe.
- **One branch per concern** — keeping README updates on separate branches from code changes made conflicts easier to understand and resolve.
- **Explicit constraints** — instructions like "always branch from latest main" and "do not use cherry-pick" eliminated an entire class of workflow mistakes once added.

### What needed human intervention

- **Merge conflicts** — when multiple branches modified the same file (`README.md`) and were merged to `main` in sequence, later branches needed to be rebased. Claude Code could perform the rebase once instructed, but did not proactively detect the need.
- **Mid-task direction changes** — when requirements changed mid-implementation (e.g. "only JSON output, not multiple formats"), Claude Code needed an explicit interrupt and re-statement. It did not infer the change from context.
- **Force-push confirmation** — Claude Code correctly paused before `--force-with-lease` and waited for explicit approval, which was the right behaviour but required the human to be in the loop.
- **Permission prompts** — the first time each tool category was used (git push, file write, bash commands) required manual approval in the web interface.

## How to Replicate

If you want to use this workflow on your own project:

1. **Create a GitHub repo** with branch protection on `main` (require PR before merge).
2. **Write issues** with clear, scoped requirements. Include exact function signatures, file names, and acceptance criteria. Vague issues produce vague code.
3. **Open Claude Code** (web at [claude.ai/code](https://claude.ai/code)) and paste the issue content as your first message.
4. **Add standing instructions** at the start of each session or in `CLAUDE.md`:
   - Always branch from latest `main`
   - Do not cherry-pick
   - Run existing tests before pushing
   - Open a PR after pushing
5. **Review each PR** before merging. Claude Code is good at implementing what you describe, but it cannot know what you forgot to describe.
6. **Keep branches short-lived.** The longer a branch lives without merging, the more likely it is to conflict with `main`. Merge or close branches promptly.
7. **Iterate with explicit corrections.** If the output is wrong, say exactly what to change rather than asking Claude to "fix it". Specific instructions produce specific fixes.
