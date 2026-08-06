---
name: verify
description: |
  Independently checks an executed task against requirements.md before the transport is released.
  Use after code has been pushed to SAP to validate correctness, technology compliance, and spec alignment.
---

# Skill: Verify

## Context
- Always read: `.kiro/specs/{CHG_ID}/requirements.md`, `.kiro/specs/{CHG_ID}/tasks.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, `.kiro/steering/tech.md`, and the implemented object(s) from SAP.
- Never read: VISION.md (deprecated), micro-specs/ (deprecated)
- Never read the `execute` skill's own reasoning as evidence — re-derive correctness from requirements.md directly.

## Input
- **CHG ID**: The folder name (e.g., `CHG0440001_PRICING_FIX`)
- **Task number**: Which task to verify (e.g., `2`)

## Objective
Act as an independent ABAP reviewer for SAP ECC 6.0 EHP8. You did not write this code and must not defer to whoever did.

1. Read the task specification from tasks.md to know what was supposed to be built.
2. Re-derive what "correct" means from `requirements.md` acceptance criteria — before reading how it was implemented.
3. Read the actual implementation from SAP.
4. Trace the implementation against requirements, statement by statement.
5. Actively check for the three failure patterns:
   - **Swallowed failures** — TRY/CATCH that silently absorbs exceptions, or missing SY-SUBRC checks.
   - **Mechanism mismatch** — name/comment claims one behavior while code does something different.
   - **Technology mismatch** — syntax/features NOT available on ECC 7.5 EHP8.
6. Confirm all objects sit in the package declared in WRICEF.md.

## Verdict
State PASS or FAIL explicitly, with the specific line(s) or object(s) it's based on. On FAIL, route back to `execute` with the finding, or to `plan` if the design itself was wrong.

## Output
Append a dated entry to `.kiro/specs/{CHG_ID}/requirements.md` under the "Verification Log" section:

```markdown
### [YYYY-MM-DD] Task N — VERDICT
**Object(s) checked**: [list]
**Findings**:
- [what was verified, what passed, what failed]
**Root cause** (if FAIL): [code bug / spec gap / misunderstood requirement]
**Action needed** (if FAIL): [route to execute or plan]
```

## Halt gate
Do not mark the task fully complete, and do not approve transport release, until this skill returns PASS.
