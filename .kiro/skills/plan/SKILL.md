---
name: plan
description: |
  Reads requirements and WRICEF metadata, generates design.md and tasks.md for a CHG.
  Use when starting technical planning after requirements are defined.
---

# Skill: Plan

## Context
- Always read: `.kiro/steering/product.md`, `.kiro/steering/tech.md`, `.kiro/specs/{CHG_ID}/design.md`
- Always write: `.kiro/specs/{CHG_ID}/requirements.md`, `.kiro/specs/{CHG_ID}/tasks.md`
- Optionally refine: `.kiro/specs/{CHG_ID}/design.md`
- Never write: ROADMAP.md, WRICEF.md, micro-specs/

## Prerequisite
- `design.md` must exist with a populated Overview and Object Breakdown.
- `design.md` Approval Status must NOT be PENDING (user must have replied `DESIGN_APPROVED`).

## Objective
Act as an ABAP Solution Architect for SAP ECC 6.0 EHP8 (NetWeaver 7.50). Starting from the approved design.md, perform three actions:

1. **Refine design.md** — Add any missing details, validate object choices against tech.md constraints, flesh out Design Decisions if incomplete.

2. **Derive requirements.md** — From the design's Overview, Architecture, and Object Breakdown, derive formal requirements with user stories and testable acceptance criteria. Replace the placeholder content.

3. **Generate tasks.md** — Break down the Object Breakdown into numbered implementation tasks with specifications, dependencies, and checkboxes.

## requirements.md Structure

```markdown
# Requirements: {CHG_ID}

## Introduction
### Summary
[1-2 sentence description derived from design.md Overview]

### Business Goal
[Extracted from design.md or the original functional document]

### Process Flow
[Step-by-step business flow]

## Requirements
### Requirement 1: [Name]
**User Story**: As a [role], I want [capability] so that [benefit]
**Acceptance Criteria**:
- [ ] AC 1.1: [testable criterion]
- [ ] AC 1.2: [testable criterion]

## Verification Log
[Append-only audit trail from #verify — do not overwrite prior entries]
```

## tasks.md Structure

```markdown
# Tasks: {CHG_ID}

## Task 1: [Object/Action Name]
- [ ] 1.1 [Implementation step]
- [ ] 1.2 [Implementation step]

**Object**: [Name from design.md Object Breakdown]
**Type**: [PROG/CLAS/INTF/FUGR/TABL/etc.]
**Action**: [Create/Modify]
**Depends on**: [Task N, or "None"]

**Specification**:
- Input: [what the object receives]
- Output: [what the object produces]
- Logic: [step-by-step processing rules]
- Error handling: [how failures are managed]
```

## Object Planning Rules

Only plan objects available on ECC 7.5 EHP8:
- Programs/Reports, Includes
- Classes (ZCL_*), Interfaces (ZIF_*)
- Function Modules / Function Groups
- SE11 Tables, Structures, Data Elements, Domains, Table Types, Search Helps, Lock Objects
- Classic BAdI implementations, User-Exits, Enhancement Implementations
- SAPscript / Smartforms / Adobe Forms
- Transactions (SE93)

Do NOT plan: CDS views, AMDP, RAP behavior definitions, service bindings, Fiori annotation-driven UIs.

Ensure all objects belong in the target package from design.md's SAP Context section.

## Halt gate
Present all three documents and stop. Do not begin execution until the user reviews and confirms the plan is ready.
