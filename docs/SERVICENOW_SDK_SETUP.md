# ServiceNow SDK Setup Guide for Kiro

Step-by-step guide to get the **ServiceNow SDK** (`@servicenow/sdk`, `now-sdk` CLI) working inside Kiro / VS Code on Windows, authenticate against the Amrize instances (QUAL and PRD), and query live data (incidents, changes, RITM, problems, etc.).

> Validated on Windows with PowerShell. All commands run in a PowerShell terminal.

---

## 1. Context: what it is and what it is NOT

- ServiceNow here works through the **`servicenow-sdk` power**, which wraps the `@servicenow/sdk` CLI (`now-sdk`). **It is not an MCP server.**
- The CLI is operated from the command line; Kiro can run those commands for you.
- Main capabilities:
  - **`now-sdk query`** — live data queries (READ ONLY) against any table.
  - **`now-sdk explain`** — built-in documentation (hundreds of topics).
  - **`now-sdk auth`** — authentication management per instance.
  - Fluent app development commands (`init`, `build`, `install`, etc.) — not needed just to query.

### Important limitations (confirmed)

| Capability | Available with the SDK? |
|-----------|-------------------------|
| Query records (incident, change, RITM, problem...) | ✅ Yes (`query`, read only) |
| List attachments of a record | ✅ Yes (`query` against `sys_attachment`) |
| **Create** a change request or other business record | ❌ Not with `now-sdk`. Requires the Table API REST (`POST`). |
| **Modify / advance states** of a record | ❌ Not with `now-sdk`. Requires the Table API REST (`PATCH`). |
| Download an attachment's binary | ❌ Not with `now-sdk`. Requires the Attachment API REST (`GET .../file`). |
| Read `sys_dictionary` / `sys_choice` metadata | ⚠️ Depends on the user's permissions (often restricted). |

> To create/modify records or download attachments, use the **ServiceNow REST API** with the same basic authentication (see section 8).

---

## 2. Prerequisite: Node.js

The CLI runs on Node.js. If `node`/`npm`/`npx` are not installed:

### Recommended option (no administrator privileges)

Portable Node installation in the user profile:

```powershell
$ver = 'v24.19.0'
$dir = "$env:USERPROFILE\nodejs"
$zip = "$env:TEMP\node-$ver-win-x64.zip"
$url = "https://nodejs.org/dist/$ver/node-$ver-win-x64.zip"
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
Expand-Archive -Path $zip -DestinationPath $env:USERPROFILE -Force
Rename-Item "$env:USERPROFILE\node-$ver-win-x64" $dir
```

Add Node to the user PATH (persistent):

```powershell
$dir = "$env:USERPROFILE\nodejs"
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if ($userPath -notlike "*$dir*") {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$dir", 'User')
}
```

> Note: the official MSI installer (`winget install OpenJS.NodeJS.LTS`) requires administrator elevation (UAC) and may fail with code 1603 in corporate environments. The portable installation above avoids this.

### Verify

Open a **new terminal** (so it picks up the updated PATH) and check:

```powershell
node --version   # -> v24.19.0
npm --version    # -> 11.17.0
```

---

## 3. Load the PATH in each terminal

The user PATH only applies to **new** terminals. If `now-sdk` is not recognized, load the PATH manually at the start of the session:

```powershell
$env:Path = "$env:USERPROFILE\nodejs;$env:USERPROFILE\nodejs\node_modules\npm\bin;$env:Path"
```

> Tip: keep this line handy; you need to run it once per new terminal (or add it to your PowerShell profile).

---

## 4. Install the ServiceNow SDK

Global installation (one time only; leaves the `now-sdk` command available and cached):

```powershell
$env:Path = "$env:USERPROFILE\nodejs;$env:Path"
npm install -g @servicenow/sdk@latest
```

The installation downloads ~500 packages and takes a couple of minutes. Verify:

```powershell
now-sdk --version   # -> 4.11.2 (or higher)
now-sdk --help
```

> Version requirements: `explain` needs >= 4.6.0; `query` needs >= 4.8.0.

---

## 5. Authentication

### Available methods

- **basic** — username + password. Simple. Ideal for service / integration users.
- **oauth** — browser flow (code grant). Required for SSO, but needs the instance to have an **OAuth API endpoint for external clients** registered (Client ID/Secret/Redirect URL).

### Note on corporate SSO

If your instance uses **pure SSO**:
- `basic` with your personal user usually **fails** (your password lives in the identity provider, not in ServiceNow).
- `oauth` is the correct path, but if there is no registered OAuth client, the browser shows **"Security constraints prevent access to requested page"**.
- **Practical solution:** use an **integration/service user** with a local login in ServiceNow (its own password, not SSO) and API read permissions → authenticate with `basic`.

### Login command (basic)

```powershell
now-sdk auth --add https://YOUR-INSTANCE.service-now.com --type basic --alias YOUR-ALIAS
```

The command prompts for alias, username, and password (the password is entered at the prompt, not stored in the history). Credentials are stored encrypted in `.now-sdk/` (gitignored).

### Real examples (Amrize)

```powershell
# QUAL (testing)
now-sdk auth --add https://oneservicequalna.service-now.com --type basic --alias oneservicequalna

# PRD (production) — use an integration user
now-sdk auth --add https://oneservicena.service-now.com --type basic --alias oneservicena-prd
```

> **Alias convention:** use clear, distinct aliases per environment (`oneservicequalna`, `oneservicena-prd`) so you don't confuse QUAL with PRD.

### Credential management

```powershell
now-sdk auth --list                 # list stored credentials (* = default)
now-sdk auth --use YOUR-ALIAS       # set which one is the default
now-sdk auth --delete YOUR-ALIAS    # delete a set of credentials
```

---

## 6. Query data (`now-sdk query`)

### Base syntax

```powershell
now-sdk query <table> -q '<encoded_query>' -o json
```

### Useful flags

| Flag | Description |
|------|-------------|
| `-q, --query` | Filter (encoded query). **Required.** e.g. `active=true^priority<=2` |
| `-f, --fields` | Fields to return (comma-separated) |
| `--limit` | Max records per page (default 100) |
| `--display-value all` | Returns raw value + label (useful for states) |
| `-a, --auth` | **Credential alias to use (selects the environment).** e.g. `-a oneservicena-prd` |
| `-o, --output` | `json` for structured output |
| `-s, --select` | Extract a specific field (e.g. `records[0].sys_id`) |

> **Best practice:** in PRD, ALWAYS include an explicit `-a <prd-alias>` so you know which environment you are querying.

### Common tables

| Table | Content |
|-------|---------|
| `incident` | Incidents |
| `change_request` | Changes |
| `sc_req_item` | RITM (Requested Items) |
| `sc_request` | Requests (REQ) |
| `problem` | Problems (PRB) |
| `sys_user` | Users |
| `sys_attachment` | Attachments of any record |

### Examples

```powershell
$env:Path = "$env:USERPROFILE\nodejs;$env:Path"

# High-priority active incidents
now-sdk query incident -q 'active=true^priority<=2' -f 'number,short_description,state' -a oneservicena-prd -o json

# Find a user by name (to get their sys_id)
now-sdk query sys_user -q 'nameLIKEhernandez' -f 'sys_id,user_name,name,email' -a oneservicena-prd -o json

# A user's incidents (by sys_id) across several roles
now-sdk query incident -q 'caller_id=<sys_id>^ORassigned_to=<sys_id>^ORopened_by=<sys_id>' -f 'number,short_description,state' -a oneservicena-prd --display-value all -o json

# Open incidents of an assignment group
now-sdk query incident -q 'assignment_group=<sys_id>^active=true' -f 'number,short_description,state,assigned_to' -a oneservicena-prd --display-value all -o json

# Full detail of a ticket
now-sdk query incident -q 'number=INC08340528' -f 'number,short_description,description,state,priority,caller_id,assigned_to,assignment_group,opened_at,comments,work_notes' -a oneservicena-prd --display-value all -o json

# Attachments of an incident
now-sdk query sys_attachment -q 'table_name=incident^table_sys_id=<incident_sys_id>' -f 'sys_id,file_name,content_type,size_bytes' -a oneservicena-prd --display-value all -o json
```

### Encoded query operators (quick reference)

- `^` = AND · `^OR` = OR
- `=` equals · `!=` not equals · `LIKE` contains · `STARTSWITH` · `IN`
- `<=` `>=` for numbers/priorities
- `ORDERBY<field>` / `ORDERBYDESC<field>`
- Dynamic values: `javascript:gs.getUserID()` (current user), `javascript:gs.beginningOfToday()`

Full documentation:
```powershell
now-sdk explain encoded-query-guide --format=raw
```

---

## 7. Built-in documentation (`now-sdk explain`)

```powershell
now-sdk explain --list --format=raw                 # all topics
now-sdk explain <topic> --list --peek --format=raw  # search and preview
now-sdk explain <topic> --peek --format=raw         # preview a topic
now-sdk explain <topic> --format=raw                # full topic
```

> Tip: always use `--peek` before opening a full topic to avoid burning context.

---

## 8. Write operations and attachments (REST API)

The `now-sdk` SDK does NOT create/modify records or download attachments. For that, use the **ServiceNow REST API** with the same basic authentication.

### Create a record (e.g. change request)

```
POST https://YOUR-INSTANCE.service-now.com/api/now/table/change_request
Body JSON: { "short_description": "...", "type": "Normal Minor", ... }
```

### Modify / advance state

```
PATCH https://YOUR-INSTANCE.service-now.com/api/now/table/change_request/{sys_id}
Body JSON: { "state": "<code>" }
```

> Caution: state models can be customized and governed by business rules / approval flows (CAB). A direct state jump may be rejected or leave the record inconsistent. Validate in QUAL first.

### Download an attachment's binary

```
GET https://YOUR-INSTANCE.service-now.com/api/now/attachment/{sys_id}/file
```

### Included script: read/extract attachments

`tools/snow_read_attachment.py` is included; it lists attachments, downloads them, and extracts the text from `.docx` files (using only the standard library, no external dependencies).

Credentials via environment variables (NEVER in the code):

```powershell
$env:SNOW_INSTANCE = "https://oneservicena.service-now.com"
$env:SNOW_USER     = "your_integration_user"
$env:SNOW_PASS     = "********"

python tools\snow_read_attachment.py --number INC08340528 --list
python tools\snow_read_attachment.py --number INC08340528 --extract-docx
python tools\snow_read_attachment.py --number INC08340528 --download-all
python tools\snow_read_attachment.py --table change_request --number CHG0435576 --extract-docx
```

> The `$env:` variables defined in a terminal only live in that session. For another process to see them, use `[Environment]::SetEnvironmentVariable("SNOW_PASS","...","User")` and **delete them when finished** with the same command passing `$null`.

---

## 8b. "Service Now" MCP Server (native alternative in Kiro)

In addition to the `now-sdk` CLI, the workspace includes its own **MCP server** that exposes ServiceNow as native tools inside Kiro. Advantages over the CLI: it does not depend on npx downloads, it avoids command "cutoffs", and it **supports writes** (create/update records, advance states, work notes) and **attachments** (list and extract text from `.docx`) — things `now-sdk query` (read only) does not cover.

### Server files

| File | Role |
|------|------|
| `servicenow_client.py` | REST client (Table API + Attachment API), basic auth, read and write. |
| `servicenow_server.py` | Data-driven MCP server (stdio), defines the tools. Configured via environment variables. |

Requirements: Python 3.10+ and the `mcp` and `requests` packages (see `requirements.txt`).

### Available tools

**Read:**
- `snow_ping` — verifies the connection.
- `snow_query` — queries any table (encoded query, fields, paging, display value).
- `snow_get_record` — a full record by number (INC/CHG/RITM/PRB).
- `snow_find_user` — searches for a user by name/username/email → returns sys_id.
- `snow_list_attachments` — lists a record's attachments.
- `snow_extract_docx` — downloads and extracts the text of an attached `.docx`.

**Write** (not available via `now-sdk`):
- `snow_create_record` — creates records (e.g. change_request).
- `snow_update_record` — updates fields by number.
- `snow_advance_state` — advances a change's state (state code).
- `snow_add_work_note` — adds a work note / comment.

### Configuration in `.kiro/settings/mcp.json`

The server reads the connection from environment variables: `SNOW_INSTANCE`, `SNOW_USER`, `SNOW_PASSWORD`, `SNOW_ENV`. **Two entries** are registered (one per environment) so you can point to PRD or QUAL in isolation.

**PRD entry:**

```json
"Service Now": {
  "command": "C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": ["C:\\Users\\<user>\\ANDRES-WORKSPACE\\servicenow_server.py"],
  "cwd": "C:\\Users\\<user>\\ANDRES-WORKSPACE",
  "env": {
    "SNOW_INSTANCE": "https://oneservicena.service-now.com",
    "SNOW_USER": "kiro_integration",
    "SNOW_PASSWORD": "PUT_THE_PASSWORD_HERE",
    "SNOW_ENV": "PRD"
  },
  "disabled": false,
  "autoApprove": [
    "snow_ping", "snow_query", "snow_get_record",
    "snow_find_user", "snow_list_attachments", "snow_extract_docx"
  ]
}
```

**QUAL entry:**

```json
"Service Now QUAL": {
  "command": "C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": ["C:\\Users\\<user>\\ANDRES-WORKSPACE\\servicenow_server.py"],
  "cwd": "C:\\Users\\<user>\\ANDRES-WORKSPACE",
  "env": {
    "SNOW_INSTANCE": "https://oneservicequalna.service-now.com",
    "SNOW_USER": "test_kiro",
    "SNOW_PASSWORD": "PUT_THE_PASSWORD_HERE",
    "SNOW_ENV": "QUAL"
  },
  "disabled": false,
  "autoApprove": [
    "snow_ping", "snow_query", "snow_get_record",
    "snow_find_user", "snow_list_attachments", "snow_extract_docx",
    "snow_create_record", "snow_update_record", "snow_advance_state", "snow_add_work_note"
  ]
}
```

### Security and convention notes

- **`autoApprove` per environment, on purpose:**
  - **PRD** → only **read** tools auto-approved. Write tools require manual confirmation (avoids modifying production by accident).
  - **QUAL** → also includes the **write** tools, since it is the test environment where we do want to create/advance changes.
- **`SNOW_PASSWORD` is stored in plain text** in `mcp.json` (same as the SAP credentials). That file **must not be committed to git**.
- The `SNOW_ENV` label appears in the tools' messages, so you always know which environment you are operating against.
- **The `.kiro/settings/mcp.json` file is protected**: Kiro cannot edit it automatically; you must update it by hand.
- After saving `mcp.json`, reconnect the servers from Kiro's MCP view (or restart).

### Quick usage (once connected)

- Test the connection: `snow_ping` tool.
- Query: `snow_query` with `table=incident`, `query=active=true^priority<=2`.
- Create a test change (QUAL only): `snow_create_record` with `table=change_request` and a `fields` object.
- Advance a state (QUAL only): `snow_advance_state` with `number=CHG...` and `state=<code>` (see the state model in section 6 / real data).

---

## 9. Troubleshooting

| Symptom | Cause / Solution |
|---------|------------------|
| `npx`/`node`/`now-sdk` not recognized | The PATH is not loaded in this terminal. Run the line from section 3, or open a new terminal. |
| Node MSI fails with code 1603 | Requires admin (UAC). Use the portable installation from section 2. |
| `auth --list` says "No credentials found" | The login was not saved. In OAuth this is usually due to a missing OAuth client (see "Security constraints"). Use basic with a service user. |
| Browser shows "Security constraints prevent access" | OAuth without a client registered in the instance. Use basic, or request registration of an OAuth endpoint. |
| Basic login fails with an SSO user | Your user is SSO-only. You need an integration user with a local login. |
| A query unexpectedly returns `records: []` | Likely the user is missing a read ACL on that table (e.g. `sc_req_item`, `sys_dictionary`, `sys_choice`). Request the permission or use another user. |
| A command "hangs" with no output | The command is still running (first npx download, etc.). Retry; once cached it responds quickly. |

---

## 10. Quick checklist for a new user

1. [ ] Install Node.js (portable, section 2) and verify `node --version`.
2. [ ] Load the PATH in the terminal (section 3).
3. [ ] `npm install -g @servicenow/sdk@latest` and verify `now-sdk --version`.
4. [ ] Get credentials:
   - QUAL: test user.
   - PRD: **integration user** with local login + API read permissions.
5. [ ] `now-sdk auth --add <url> --type basic --alias <alias>` for each environment.
6. [ ] `now-sdk auth --list` to confirm.
7. [ ] Test: `now-sdk query incident -q 'active=true' --limit 3 -f 'number,short_description,state' -a <alias> -o json`.
8. [ ] (Optional) For attachments/writes: use the REST API / the `tools/snow_read_attachment.py` script.
9. [ ] (Native alternative) Configure the **"Service Now" MCP server** in `mcp.json` (section 8b) — it provides read, write, and attachment tools inside Kiro without using the CLI.

---

## References

- Amrize environments:
  - QUAL: `https://oneservicequalna.service-now.com` (suggested alias: `oneservicequalna`)
  - PRD: `https://oneservicena.service-now.com` (suggested alias: `oneservicena-prd`)
- Official SDK documentation: `now-sdk explain <topic> --format=raw`
- Official landing page: https://docs.servicenow.com/csh?topicname=servicenow-sdk-landing.html
