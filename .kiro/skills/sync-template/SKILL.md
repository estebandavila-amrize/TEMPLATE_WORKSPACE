---
name: sync-template
description: |
  Extracts template-worthy improvements from the current workspace and syncs them
  to the shared template repo. Use after refining skills, steering, hooks, or specs
  structure during real project work.
---

# Skill: Sync Template

## Context
- Always read: `.kiro/steering/`, `.kiro/skills/`, `.kiro/hooks/`, `.kiro/specs/_template_CHG/`
- Target: `https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE`

## Objective
Extract generic, reusable improvements from the current workspace and push them to the shared GitHub template repo. This keeps the template evolving with real-world learnings without polluting it with project-specific data.

## What TO sync (template-worthy)
- `.kiro/skills/*/SKILL.md` — skill definitions (all of them)
- `.kiro/skills/ABAP/SKILL.md` and `references/` — ABAP knowledge base
- `.kiro/steering/*.md` — all steering rules
- `.kiro/hooks/*.kiro.hook` — all hook definitions
- `.kiro/specs/_template_CHG/` — the CHG template structure
- `.kiro/settings/mcp.json` — workspace-level MCP config (server definitions)
- Root config files: `config-systems.example.json`, `requirements.txt`, `install.bat`, `docs/`
- `server.py`, `sap_client.py` — MCP server source

## What NOT to sync (project-specific)
- Any `.kiro/specs/` folder other than `_template_CHG`
- `.abap` files in spec folders (deployed source snapshots)
- `ROADMAP.md` with filled execution status entries
- `VISION.md` with Bug Tracking entries from real incidents
- `config-systems.json` (contains real credentials/endpoints)
- Any transport numbers, order numbers, or CHG-specific data
- `__pycache__/`, `.git/`

## Procedure

1. **Verify remote** — Ensure the workspace has `origin` pointing to the template repo:
   ```
   git remote get-url origin
   ```
   Expected: `https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE.git`
   If missing or different, set it:
   ```
   git remote set-url origin https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE.git
   ```

2. **Fetch latest** — Ensure local default branch is up to date:
   ```
   git fetch origin master
   ```
   Note: the default branch is `master`. If this fails, try `main` instead.

3. **Create feature branch** — Branch off `origin/master` with a timestamped name:
   ```
   git checkout -b sync/update-YYYYMMDD-HHMM origin/master
   ```
   Use the current date/time for the branch name (e.g., `sync/update-20260805-1430`).

4. **Stage syncable files** — Add only template-worthy files:
   ```
   git add .kiro/skills/ .kiro/steering/ .kiro/hooks/ .kiro/specs/_template_CHG/ .kiro/settings/mcp.json config-systems.example.json requirements.txt install.bat docs/ server.py sap_client.py
   ```

5. **Diff staged** — Show what will be committed:
   ```
   git diff --cached --stat
   ```

6. **Halt gate** — Present the summary and STOP. Wait for user confirmation with `SYNC_APPROVED`.

7. **Commit** — After approval:
   ```
   git commit -m "sync: update workspace definitions from project"
   ```

8. **Push branch** — Push the feature branch to the remote:
   ```
   git push -u origin sync/update-YYYYMMDD-HHMM
   ```

9. **Create Pull Request** — Open a PR against `master` using the GitHub CLI:
   ```
   gh pr create --base master --head sync/update-YYYYMMDD-HHMM --title "sync: update workspace definitions" --body "Automated sync of workspace definitions (hooks, skills, steering, specs template, settings, root configs) from project workspace."
   ```
   If `gh` is not installed, provide the user with the GitHub URL to create the PR manually:
   `https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE/pull/new/sync/update-YYYYMMDD-HHMM`

10. **Return to previous branch** — Switch back to the branch the user was on:
    ```
    git checkout -
    ```

11. **Confirm** — Report success, the PR URL, and the list of files included.

## Safety rules
- NEVER commit files containing real SAP credentials, transport numbers, or customer data.
- NEVER commit spec folders with real CHG IDs (only `_template_CHG`).
- NEVER push directly to `master` (or `main`). Always use a feature branch + Pull Request.
- NEVER force-push. If push is rejected, inform the user and suggest pulling first.
- If unsure whether something is project-specific, ASK the user before staging.
- Always show a dry-run summary (staged diff) before committing.
- Requires `gh` CLI to be installed and authenticated for PR creation.

## Halt gate
Present the list of staged changes and STOP. Do not commit or push until the user confirms with `SYNC_APPROVED`.
