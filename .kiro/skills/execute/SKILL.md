---
name: execute
description: |
  Executes a specific micro-spec for a given change request.
  Use when implementing ABAP code, creating or updating SAP objects based on an approved roadmap step.
---

# Skill: Execute

## Context
- Always read: `.kiro/steering/tech.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, and the targeted Micro-Spec file.

## Objective
Act as a Senior ABAP Developer. Read the provided micro-spec and implement the exact ABAP or Python syntax requested.

- Ensure all custom objects align structurally with the package specified in WRICEF.md.
- Ensure strict compliance with the ECC 7.5 EHP8 / NetWeaver 7.50 / ABAP 7.50 limits outlined in tech.md.
- NEVER use: CDS views, AMDP, RAP/EML, ABAP Cloud syntax, WITH (CTE), HIERARCHY SQL, XCO library, FINAL(x).
- Use only Open SQL, classic BAdIs/enhancements, SE11 DDIC, and classic OO ABAP.
- Ask no clarifying questions unless the spec is logically impossible to complete.
- On completion, hand off to the `verify` skill. Do not self-certify the implementation as correct.
