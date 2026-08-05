---
name: plan
description: |
  Scopes a specific CHG folder, reviews the functional spec, and maps out objects inside the WRICEF package.
  Use when starting a new change request, creating a ROADMAP.md, or planning ABAP objects for implementation.
---

# Skill: Plan

## Context
- Always read: `.kiro/steering/product.md`, `.kiro/steering/tech.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, `.kiro/specs/{CHG_ID}/VISION.md`
- Always modify: `.kiro/specs/{CHG_ID}/ROADMAP.md`

## Objective
Act as an ABAP Solution Architect for SAP ECC 6.0 EHP8 (NetWeaver 7.50). Review the functional requirements in VISION.md and the WRICEF metadata. Generate a step-by-step technical implementation checklist in ROADMAP.md.

Break down the requirements into necessary ABAP objects - only objects available on ECC 7.5 EHP8:
- Programs/Reports, Includes
- Classes (ZCL_*), Interfaces (ZIF_*)
- Function Modules / Function Groups
- SE11 Tables, Structures, Data Elements, Domains, Table Types, Search Helps, Lock Objects
- Classic BAdI implementations, User-Exits, Enhancement Implementations
- SAPscript / Smartforms / Adobe Forms
- Transactions (SE93)

Do NOT plan objects that require HANA/S4: CDS views, AMDP, RAP behavior definitions, service bindings, Fiori annotation-driven UIs.

Ensure all planned objects belong inside the target WRICEF package. Do not generate code. Stop execution immediately after updating the roadmap.

## Halt gate
Present the roadmap and stop. Do not begin execution until the user replies with the literal string `ROADMAP_APPROVED`.
