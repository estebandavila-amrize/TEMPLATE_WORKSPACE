---
name: sync-from-repo
description: |
  Pulls the latest hooks, steering, skills, specs template, and workspace definitions
  from the remote GitHub template repo into the current workspace.
  Use when you want to update your local environment with the latest shared standards.
---

# Skill: Sync From Repo

## Context
- Source: `https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE`
- Target: Current workspace root and `.kiro/` tree

## Objective
Fetch the latest workspace definitions (hooks, steering, skills, specs template, settings, and root config files) from the shared GitHub template repo and apply them to the current workspace. This keeps your local environment aligned with the team's latest standards.

## What TO pull (workspace definitions)
- `.kiro/skills/*/SKILL.md` and `.kiro/skills/ABAP/references/` — skill definitions
- `.kiro/steering/*.md` — steering rules
- `.kiro/hooks/*.kiro.hook` — hook definitions
- `.kiro/specs/_template_CHG/` — the CHG template structure
- `.kiro/settings/mcp.json` — workspace-level MCP config
- Root config files: `config-systems.example.json`, `requirements.txt`, `install.bat`, `docs/`
- `server.py`, `sap_client.py` — MCP server source

## What NOT to pull (preserve local)
- Any `.kiro/specs/` folder other than `_template_CHG` (real specs)
- `config-systems.json` (local credentials)
- `.git/` directory
- `__pycache__/`
- Any file with real SAP transport numbers, order numbers, or customer data

## Procedure

1. **Check git remote** — Verify the workspace has the template repo configured as a remote (typically `origin`). If not, add it:
   ```
   git remote add origin https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE.git
   ```

2. **Fetch latest** — Run `git fetch origin main` to get the latest state without merging.

3. **Diff** — Compare local syncable files against `origin/main` using:
   ```
   git diff HEAD origin/main -- .kiro/skills/ .kiro/steering/ .kiro/hooks/ .kiro/specs/_template_CHG/ .kiro/settings/ config-systems.example.json requirements.txt install.bat docs/ server.py sap_client.py
   ```

4. **Report changes** — Present a summary of files that would be added, modified, or deleted.

5. **Halt gate** — STOP and wait for user confirmation before applying.

6. **Apply** — After user confirms with `PULL_APPROVED`, checkout the updated files from `origin/main`:
   ```
   git checkout origin/main -- <list of changed files>
   ```

7. **Confirm** — Report the final list of files updated.

## Alternative: No git remote available
If the workspace does not have git initialized or the remote is inaccessible:
1. Clone the repo to a temp directory.
2. Copy syncable files from the clone into the workspace.
3. Remove the temp clone.
4. Report changes applied.

## Safety rules
- NEVER overwrite `config-systems.json` (contains real credentials).
- NEVER touch spec folders other than `_template_CHG`.
- NEVER overwrite local files without showing the diff first.
- If a local file has modifications not present in the remote, WARN the user before overwriting.
- Always show a dry-run summary before writing any files.

## Halt gate
Present the list of changes to be applied and STOP. Do not write files until the user confirms with `PULL_APPROVED`.
