---
name: research
description: |
  Investigates the SAP system to validate a specification's feasibility against existing objects,
  workflows, and data structures. Produces an analysis document with findings.
  Use before planning when you need to understand what exists in the system first.
---

# Skill: Research

## Input (from user)
- **Query**: A description of what to investigate (e.g., "How does plant determination work in SD_E_112?", "What tables store pricing conditions for ZB01?", "Where is the Ship-To partner logic in VA01?")
- **CHG context** (optional): If tied to a specific change, provide the CHG ID to store the analysis in that spec folder.

## Output
A single file: `analysis-{identifier}.md` where identifier is either:
- A short kebab-case name derived from the query (e.g., `analysis-plant-determination-flow.md`)
- Or a timestamp if no clear name: `analysis-20260728-153000.md`

**Location:**
- If CHG context provided: `.kiro/specs/{CHG_ID}/analysis-{identifier}.md`
- If no CHG context: `.kiro/specs/_research/analysis-{identifier}.md` (create folder if needed)

## Procedure

1. **Understand the question**: Parse what the user wants to know — is it about a specific object, a workflow, a table structure, an enhancement point, or a business process?

2. **Investigate the system** using available SAP MCP tools:
   - `sap_search_objects` — find relevant Z-objects by pattern
   - `sap_get_program_source` / `sap_get_class_source` / `sap_get_include_source` — read implementations
   - `sap_get_table_definition` / `sap_get_structure` — understand data structures
   - `sap_get_function_module_source` — read FM logic
   - `sap_get_usage_references` — trace where objects are called
   - `sap_get_enhancements` — find enhancement points in standard programs
   - `sap_get_includes_list` — discover include hierarchy
   - `sap_get_package_contents` — list package objects
   - `sap_get_sql_query` — query data for evidence

   **CHG-specific shortcut:** If a CHG number is provided, query E07T to find all transport
   requests associated with that CHG (same logic as report `ZR_BC_R001_CHG_OBJECTS`):
   ```sql
   SELECT TRKORR, AS4TEXT FROM E07T WHERE AS4TEXT LIKE '%CHGxxxxxxx%'
   ```
   Then retrieve objects from E071 for those transports. This gives you the full list of
   objects already touched under that change — useful to understand scope and existing work.

3. **Trace the workflow**: Follow the call chain from transaction → program → includes → user exits → custom code. Document each hop.

4. **Assess feasibility**: Based on what exists, determine:
   - Does the current system support what the spec asks?
   - What objects would need to change?
   - Are there existing patterns to follow?
   - Are there risks or conflicts with existing logic?
   - What remains unclear (needs manual SAP GUI inspection)?

5. **Write the analysis document** with this structure:

```markdown
# Analysis: {Query Title}
**Date:** {YYYY-MM-DD}
**CHG:** {if applicable}
**Query:** {original question}

## Summary
[2-3 sentence executive summary of findings]

## Investigation Trail
[Step-by-step what was checked, with object names and key findings at each hop]

## Existing Objects
| Object | Type | Package | Description | Relevant? |
|--------|------|---------|-------------|-----------|
[Table of discovered objects]

## Key Findings
[Numbered list of important discoveries]

## Feasibility Assessment
[Can the spec be implemented as-is? What needs to change? What's risky?]

## Recommendations
[Concrete suggestions for the developer — where to look, what to modify, what to avoid]

## Open Questions
[Things that couldn't be determined via MCP — need manual SAP GUI investigation]
```

## Rules
- Do NOT modify any SAP objects. This is read-only investigation.
- Do NOT generate code or implementation plans. That's for `plan` and `execute`.
- Do NOT skip the investigation — always query the system, never guess from memory.
- If the system query fails or returns nothing, say so explicitly rather than assuming.
- Keep the analysis focused and actionable — this helps a developer know where to look.
- If the query is too broad, ask the user to narrow it before investigating.
