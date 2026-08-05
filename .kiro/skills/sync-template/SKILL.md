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
- Target: `%USERPROFILE%\TEMPLATE_WORKSPACE\.kiro\`

## Objective
Extract generic, reusable improvements from the current workspace and push them to the template repo. This keeps the template evolving with real-world learnings without polluting it with project-specific data.

## What TO sync (template-worthy)
- `.kiro/skills/*/SKILL.md` - skill definitions (all of them)
- `.kiro/skills/ABAP/SKILL.md` and `references/` - ABAP knowledge base
- `.kiro/steering/*.md` - all steering rules
- `.kiro/hooks/*.kiro.hook` - all hook definitions
- `.kiro/specs/_template_CHG/` - the CHG template structure
- `.kiro/settings/mcp.json` - workspace-level MCP config (server definitions)
- Root config files: `config-systems.example.json`, `requirements.txt`, `docs/`

## What NOT to sync (project-specific)
- Any `.kiro/specs/` folder other than `_template_CHG`
- `.abap` files in spec folders (deployed source snapshots)
- `ROADMAP.md` with filled execution status entries
- `VISION.md` with Bug Tracking entries from real incidents
- `config-systems.json` (contains real credentials/endpoints)
- Any transport numbers, order numbers, or CHG-specific data

## Procedure
1. List all files in the workspace's `.kiro/` tree.
2. For each syncable category above, compare content with the template repo target.
3. If the workspace version is newer/different, overwrite the template version.
4. If the workspace has NEW files in syncable categories that don't exist in template, add them.
5. If the template has files that were DELETED in workspace (syncable categories only), remove them from template.
6. Report a summary: files added, updated, removed, unchanged.

## Safety rules
- NEVER sync files containing real SAP credentials, transport numbers, or customer data.
- NEVER sync spec folders with real CHG IDs (only `_template_CHG`).
- If unsure whether something is project-specific, ASK the user before syncing.
- Always show a dry-run summary before writing to the template repo.

## Halt gate
Present the list of changes to be applied and STOP. Do not write to the template repo until the user confirms with `SYNC_APPROVED`.
