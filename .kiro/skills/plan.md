# Skill: Plan
<!-- description: Scopes a specific CHG folder, reviews the functional spec, and maps out objects inside the WRICEF package -->

## Context
- Always read: `.kiro/steering/product.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, `.kiro/specs/{CHG_ID}/VISION.md`
- Always modify: `.kiro/specs/{CHG_ID}/ROADMAP.md`

## Objective
Act as an ABAP Solution Architect. Review the functional requirements in VISION.md and the WRICEF metadata. Generate a step-by-step technical implementation checklist in ROADMAP.md. Break down the requirements into necessary ABAP objects (Classes, Tables, etc.). Ensure all planned objects belong inside the target WRICEF package. Do not generate code. Stop execution immediately after updating the roadmap.

## Halt gate
Present the roadmap and stop. Do not begin execution until the user replies with the literal string `ROADMAP_APPROVED`.
