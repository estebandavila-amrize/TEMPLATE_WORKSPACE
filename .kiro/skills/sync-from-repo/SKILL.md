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
- `server.py`, `sap_client.py` — SAP MCP server source
- `servicenow_server.py`, `servicenow_client.py` — ServiceNow MCP server source

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

2. **Fetch latest** — Determine the remote's default branch, then fetch it without merging. The template repo's default branch is `master` (fall back to `main` if `master` does not exist):
   ```
   git ls-remote --heads origin
   git fetch origin master
   ```

3. **Diff** — Compare local syncable files against `origin/master` using:
   ```
   git diff HEAD origin/master -- .kiro/skills/ .kiro/steering/ .kiro/hooks/ .kiro/specs/_template_CHG/ .kiro/settings/ config-systems.example.json requirements.txt install.bat docs/ server.py sap_client.py servicenow_server.py servicenow_client.py
   ```

4. **Report changes** — Present a summary of files that would be added, modified, or deleted.

5. **Halt gate** — STOP and wait for user confirmation before applying.

6. **Apply** — After user confirms with `PULL_APPROVED`, checkout the updated files from `origin/master`:
   ```
   git checkout origin/master -- <list of changed files>
   ```

7. **Confirm** — Report the final list of files updated.

8. **Ensure the ServiceNow SDK is installed** — After applying, check whether the ServiceNow SDK CLI (`now-sdk`) is available and install it if not. This keeps the ServiceNow MCP server usable alongside the CLI. See `docs/SERVICENOW_SDK_SETUP.md` for full details.
   - Detect it:
     ```
     now-sdk --version
     ```
   - If the command is **not** found, ensure Node.js is available, then install the SDK globally:
     ```
     node --version
     npm install -g @servicenow/sdk@latest
     now-sdk --version
     ```
   - If **Node.js is missing**, install it portably under the user's local app context (no admin / UAC required), matching `install.bat`:
     ```
     powershell -NoProfile -Command "$ver='v24.19.0'; $dst=\"$env:LOCALAPPDATA\Programs\nodejs\"; $zip=Join-Path $env:TEMP ('node-'+$ver+'-win-x64.zip'); $url='https://nodejs.org/dist/'+$ver+'/node-'+$ver+'-win-x64.zip'; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing; $parent=Split-Path $dst -Parent; if(!(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent | Out-Null}; if(Test-Path $dst){Remove-Item -Recurse -Force $dst}; Expand-Archive -Path $zip -DestinationPath $parent -Force; Rename-Item (Join-Path $parent ('node-'+$ver+'-win-x64')) $dst; Remove-Item $zip -Force; $u=[Environment]::GetEnvironmentVariable('Path','User'); if($u -notlike ('*'+$dst+'*')){[Environment]::SetEnvironmentVariable('Path', ($u.TrimEnd(';')+';'+$dst), 'User')}"
     ```
     Then re-run `npm install -g @servicenow/sdk@latest`.
   - This step is **non-fatal**: if the install fails (no network, npm error), report a warning and continue. The SDK is optional; the Python-based ServiceNow MCP server works without it.

## Alternative: No git remote available
If the workspace does not have git initialized or the remote is inaccessible:
1. Clone the repo to a temp directory.
2. Copy syncable files from the clone into the workspace.
3. Remove the temp clone.
4. Report changes applied.

## Safety rules
- NEVER overwrite `config-systems.json` (contains real credentials).
- NEVER overwrite `.kiro/settings/mcp.json` (contains real SAP/ServiceNow credentials); treat it like `config-systems.json`.
- NEVER touch spec folders other than `_template_CHG`.
- NEVER overwrite local files without showing the diff first.
- If a local file has modifications not present in the remote, WARN the user before overwriting.
- Always show a dry-run summary before writing any files.
- The ServiceNow SDK install (step 8) is optional and non-fatal — a failure must not abort the sync.

## Halt gate
Present the list of changes to be applied and STOP. Do not write files until the user confirms with `PULL_APPROVED`.
