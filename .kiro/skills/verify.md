# Skill: Verify
<!-- description: Independently checks an executed micro-spec against VISION.md before the transport is released -->

## Context
- Always read: `.kiro/specs/{CHG_ID}/VISION.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, the targeted Micro-Spec file, and the implemented object(s) it produced.
- Never read the `execute` skill's own reasoning as evidence — re-derive correctness from VISION.md and the micro-spec directly.

## Objective
Act as an independent ABAP reviewer. You did not write this code and must not defer to whoever did.

1. Re-derive what "correct" means from `VISION.md`'s business goal and the micro-spec's stated inputs/outputs — before reading how it was implemented.
2. Trace the actual implementation against that, statement by statement. Does it do what the spec says, or something adjacent that merely compiles?
3. Actively check for the two failure patterns that are cheap to introduce and expensive to catch in ABAP:
   - **Swallowed failures** — a `TRY/CATCH` that silently absorbs an exception, or a missing/ignored `SY-SUBRC` check, letting a failed operation continue as if it succeeded.
   - **Mechanism mismatch** — a class, method, or CDS view whose name or comment claims one behavior (e.g. a real BAPI call) while actually doing something lesser or different (e.g. a hardcoded stub).
4. Confirm all custom objects still sit inside the package declared in `WRICEF.md`, and nothing violates the NetWeaver 7.50 constraints in `tech.md`.

## Verdict
State PASS or FAIL explicitly, with the specific line(s) or object(s) it's based on. On FAIL, do not patch it yourself — route back to `execute` with the finding, or to `plan` if the roadmap step itself was wrong.

## Output
Append a dated entry to `.kiro/specs/{CHG_ID}/VISION.md`'s "Bug Tracking" section: verdict, what was checked, and what (if anything) needs to change — this is the audit trail for why an object was reworked.

## Halt gate
Do not mark the CHG's step complete, and do not run the "Push to GitHub" hook for it, until this skill has returned PASS.
