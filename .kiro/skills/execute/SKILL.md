---
name: execute
description: |
  Executes a specific task from tasks.md for a given change request.
  Use when implementing ABAP code, creating or updating SAP objects based on an approved design.
---

# Skill: Execute

## Context
- Always read: `.kiro/steering/tech.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, `.kiro/specs/{CHG_ID}/tasks.md`, `.kiro/specs/{CHG_ID}/design.md`
- Never read: micro-specs/ (deprecated), ROADMAP.md (deprecated)

## Input
- **CHG ID**: The folder name (e.g., `CHG0440001_PRICING_FIX`)
- **Task number**: Which task to execute (e.g., `2`)

## Objective
Act as a Senior ABAP Developer. Read the specified task from tasks.md and implement the exact ABAP objects specified.

1. Verify design.md Approval Status is not PENDING.
2. Verify all task dependencies are complete (subtask checkboxes checked).
3. Read the task's Specification section for implementation details.
4. Use design.md for architectural context (how this object fits with others).
5. Implement the ABAP code per specification.
6. After successful implementation, mark the task's subtask checkboxes as complete in tasks.md.

## Constraints
- Ensure all objects align with the package in WRICEF.md.
- Strict compliance with ECC 7.5 EHP8 / NetWeaver 7.50 / ABAP 7.50 (see tech.md).
- NEVER use: CDS views, AMDP, RAP/EML, ABAP Cloud syntax, WITH (CTE), HIERARCHY SQL, XCO library, FINAL(x).
- Use only Open SQL, classic BAdIs/enhancements, SE11 DDIC, and classic OO ABAP.
- Ask no clarifying questions unless the spec is logically impossible.

## Completion
On completion, mark subtask checkboxes in tasks.md and inform the user:
"Task N implemented. Run #verify to validate before releasing the transport."

Do not self-certify. Hand off to verify.
