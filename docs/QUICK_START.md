# Quick Start — SAP MCP Workspace

## One-Command Install

Double-click `install.bat` or run from any terminal:

```cmd
install.bat
```

The installer will:
1. Check Python is installed (3.10+ required)
2. Ask for your SAP system(s) — host, port, client, credentials — and optionally a second (e.g. sandbox)
3. Ask for your business domain and NetWeaver version, to fill the steering files
4. Create the workspace at `%USERPROFILE%\<your chosen folder name>`
5. Set up the full `.kiro` structure (steering, skills, specs, hooks)
6. Configure the MCP server in `~/.kiro/settings/mcp.json` and generate `config-systems.json` locally
7. Install Python dependencies (mcp, requests)

## After Install

1. Open Kiro
2. File > Open Folder > the workspace path printed at the end of the installer
3. Restart Kiro
4. In chat: `Verify connection with SAP <your system ID>`

## Daily Workflow (Spec-Driven Development)

### Starting a new Change Request

```
1. Copy  .kiro/specs/_template_CHG/  →  .kiro/specs/CHG04XXXXX/
2. Fill  WRICEF.md   (package, TR, object inventory)
3. Fill  VISION.md   (functional requirements from consultant)
4. Chat: "Plan CHG04XXXXX"  →  activates #plan  →  populates ROADMAP.md
5. Reply `ROADMAP_APPROVED` to confirm the roadmap
6. Create micro-specs in  micro-specs/  (one per object)
7. Chat: "Execute micro-spec X for CHG04XXXXX"  →  activates #execute
8. Chat: "Verify micro-spec X for CHG04XXXXX"  →  activates #verify  →  PASS required before transport release
```

### SAP Deploy (after code is ready)

```
1. Provide TR number
2. Kiro reads baseline from SAP
3. Review diff
4. Kiro uploads → activates → syntax checks → verifies
```

## Workspace Structure

```
<your-workspace>/
├── install.bat              ← Distribution installer (share this)
├── server.py                ← MCP Server
├── sap_client.py            ← SAP ADT HTTP client
├── requirements.txt         ← Python deps
├── config-systems.example.json  ← Template — install.bat generates the real
│                                  config-systems.json locally (gitignored)
├── .kiro/
│   ├── steering/            ← Always-on rules (2 files)
│   │   ├── tech.md          ← NetWeaver version + ABAP constraints
│   │   └── product.md       ← Business domain context
│   ├── skills/              ← Executable procedures
│   │   ├── plan.md          ← Vision → Roadmap
│   │   ├── execute.md       ← Micro-spec → Code
│   │   ├── verify.md        ← Independent audit → PASS/FAIL before transport release
│   │   └── ABAP/            ← Language reference (28 files)
│   ├── specs/               ← Active change requests
│   │   └── _template_CHG/   ← Copy for each new CHG
│   └── docs/                ← On-demand reference
└── scripts/                 ← Utility scripts
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python not recognized` | Install Python 3.10+, check "Add to PATH" |
| MCP server won't connect | Check VPN is active, verify with `Test-NetConnection <your-sap-host> -Port <your-port>` |
| Password expired | Update in SAP GUI first, then re-run `install.bat` |
