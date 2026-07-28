# SAP MCP Server

Python MCP server bridging Kiro IDE to an SAP system via the ADT REST API.

## Install

Double-click `install.bat` — it asks for your SAP system(s) and credentials, then handles everything else. Details: [docs/QUICK_START.md](docs/QUICK_START.md)

## Architecture

```
Kiro IDE ──MCP──► server.py ──HTTP──► Your SAP system (ADT REST API)
                      │
                  sap_client.py
```

## Development Workflow (Spec-Driven)

```
_template_CHG/ ──copy──► CHG04XXXXX/
                            ├── WRICEF.md     ← SAP metadata
                            ├── VISION.md     ← Requirements + Bug Tracking log
                            ├── ROADMAP.md    ← Plan (#plan) — needs ROADMAP_APPROVED
                            └── micro-specs/  ← Execute (#execute) → Verify (#verify)
```

## Distribution

Share `install.bat` with any team member. It:
- Asks for their SAP system(s), credentials, and business context
- Creates the workspace folder
- Sets up `.kiro` structure (steering + skills + specs)
- Configures the MCP server and generates `config-systems.json` locally (never committed)
- Installs Python dependencies

No manual setup steps required. Before sharing, set `REPO_URL` at the top of `install.bat` to your repo so teammates clone the right place.
