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
- `server.py`, `sap_client.py` — SAP MCP server source
- `servicenow_server.py`, `servicenow_client.py` — ServiceNow MCP server source

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
   git add .kiro/skills/ .kiro/steering/ .kiro/hooks/ .kiro/specs/_template_CHG/ .kiro/settings/mcp.json config-systems.example.json requirements.txt install.bat docs/ server.py sap_client.py servicenow_server.py servicenow_client.py
   ```
   Note: `.kiro/settings/mcp.json` contains real credentials — stage it ONLY if it holds no secrets, otherwise omit it.

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

9. **Ensure the GitHub CLI is available** — PR creation needs `gh`. Detect it; if missing, install it portably under the user's local app context (no admin / UAC required), matching `install.bat`.
   - Detect:
     ```
     gh --version
     ```
   - If **not found**, install portably (downloads the latest `windows_amd64` release into `%LOCALAPPDATA%\Programs\gh` and adds `bin` to the user PATH):
     ```
     powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $dst=\"$env:LOCALAPPDATA\Programs\gh\"; $rel=Invoke-RestMethod -Uri 'https://api.github.com/repos/cli/cli/releases/latest' -Headers @{'User-Agent'='kiro'} -UseBasicParsing; $asset=$rel.assets | Where-Object { $_.name -match 'windows_amd64\.zip$' } | Select-Object -First 1; $zip=Join-Path $env:TEMP $asset.name; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing; if(Test-Path $dst){Remove-Item -Recurse -Force $dst}; New-Item -ItemType Directory -Force -Path $dst | Out-Null; Expand-Archive -Path $zip -DestinationPath $dst -Force; Remove-Item $zip -Force; $bin=Join-Path $dst 'bin'; $u=[Environment]::GetEnvironmentVariable('Path','User'); if($u -notlike ('*'+$bin+'*')){[Environment]::SetEnvironmentVariable('Path', ($u.TrimEnd(';')+';'+$bin), 'User')}; & (Join-Path $bin 'gh.exe') --version"
     ```
   - Confirm authentication with `gh auth status`. If not authenticated, the user must run `gh auth login` once (interactive — do not attempt to automate it or handle their credentials).

10. **Create Pull Request** — Open a PR against `master` using the GitHub CLI:
   ```
   gh pr create --base master --head sync/update-YYYYMMDD-HHMM --title "sync: update workspace definitions" --body "Automated sync of workspace definitions (hooks, skills, steering, specs template, settings, root configs) from project workspace."
   ```
   If `gh` is unavailable or not authenticated, provide the user with the GitHub URL to create the PR manually:
   `https://github.com/estebandavila-amrize/TEMPLATE_WORKSPACE/pull/new/sync/update-YYYYMMDD-HHMM`

11. **Return to previous branch** — Switch back to the branch the user was on:
    ```
    git checkout -
    ```

12. **Confirm** — Report success, the PR URL, and the list of files included.

## Safety rules
- NEVER commit files containing real SAP credentials, transport numbers, or customer data.
- NEVER commit spec folders with real CHG IDs (only `_template_CHG`).
- NEVER push directly to `master` (or `main`). Always use a feature branch + Pull Request.
- NEVER force-push. If push is rejected, inform the user and suggest pulling first.
- If unsure whether something is project-specific, ASK the user before staging.
- Always show a dry-run summary (staged diff) before committing.
- `gh` is auto-installed portably if missing (step 9), but authentication (`gh auth login`) is interactive and must be done by the user — never automate it or handle their credentials. If `gh` is unavailable or unauthenticated, fall back to the manual PR URL.
- `.kiro/settings/mcp.json` holds real SAP/ServiceNow credentials — do NOT stage it unless you have confirmed it contains no secrets.

## Halt gate
Present the list of staged changes and STOP. Do not commit or push until the user confirms with `SYNC_APPROVED`.
