# Kiro IDE: Enterprise Spec-Driven Development Guide

Welcome to the new standard for SAP ABAP and Python MCP development. We have transitioned our Kiro IDE workspace to a **Change-Scoped, Spec-Driven Development (SDD)** workflow based on the GSD (Git. Ship. Done.) framework.

This guide explains how functional consultants and ABAP developers will use Kiro to plan, execute, and iterate on Change Requests (CHGs) without AI hallucinations or context bloat.

---

## The Core Philosophy

- **No "Vibe Coding":** We no longer rely on open-ended chat prompts to generate code. Kiro is now driven entirely by structured markdown files (Specifications).
- **Strict System Limits:** Kiro is permanently anchored to SAP NetWeaver 7.50 (ECC 6.0 EHP8). It is forbidden from using ABAP Cloud, RAP, or Steampunk syntax.
- **Change-Scoped Isolation:** Every Change Request (e.g., CHG0437000) gets its own isolated folder. Kiro only reads the context of the active change, preventing token waste and cross-contamination.

---

## The .kiro Directory Explained

The `.kiro/` folder at the root of our project is Kiro's "brain." Here is how it is structured:

| Folder | Purpose |
|--------|---------|
| `steering/` | Contains `tech.md` (NW 7.50 rules) and `product.md` (Business rules). Do not edit these unless you are changing global enterprise architecture. |
| `skills/` | Contains the `gsd-plan` and `gsd-execute` automations that instruct Kiro on how to behave. |
| `docs/` | Passive knowledge base. Kiro only reads these files if explicitly told to. |
| `specs/` | The active workspace where all daily development happens. |

---

## The Daily Workflow: Step-by-Step

When a new Change Request is approved, follow this exact lifecycle:

### Step 1: Initialize the Change Workspace (Functional/Dev)

Whenever a new CHG is assigned, duplicate the template folder.

1. Copy `.kiro/specs/_template_CHG/`
2. Rename the copy to match your change number (e.g., `.kiro/specs/CHG0437000/`)

### Step 2: Intake the Functional Spec (Functional/Dev)

Fill out the metadata files so Kiro understands the business goal and SAP boundaries.

- **WRICEF.md:** Enter the WRICEF ID, target SAP Package (e.g., `ZSD_I002`), Transport Request, and the objects involved.
- **VISION.md:** Paste the functional specification, business goals, and process flow here.

### Step 3: The Planning Phase (Dev + Kiro)

Instead of manually mapping out the architecture, let Kiro act as the Lead Architect.

1. Open Kiro's chat panel.
2. Type: `Run gsd-plan on .kiro/specs/CHG0437000/`
3. Kiro will read the VISION.md and WRICEF.md, figure out the necessary ABAP objects, and automatically populate your local ROADMAP.md with a step-by-step technical checklist.

### Step 4: Write Micro-Specs (Dev)

Look at the populated ROADMAP.md. For each SAP object Kiro identified, you need a blueprint.

1. Inside your `CHG0437000/micro-specs/` folder, copy `_template-micro-spec.md` for each object (e.g., `zcl_shipping_det.md`).
2. Briefly define the target file, inputs, outputs, and specific logic for that single object.

### Step 5: The Execution Phase (Dev + Kiro)

Now, let Kiro write the actual ABAP or Python code.

1. Open Kiro's chat panel.
2. Type: `Run gsd-execute on .kiro/specs/CHG0437000/micro-specs/zcl_shipping_det.md`
3. Kiro will generate the exact code for that object, ensuring it complies with NetWeaver 7.50 syntax and belongs to the correct WRICEF package.
4. Verify the code, activate the object in SAP, and check the item off in ROADMAP.md.

### Step 6: Testing & Iterations (Functional/Dev)

If unit tests or functional tests fail, **do not create a new CHG folder**.

1. Append the bug details or test failures to the bottom of the existing VISION.md.
2. Ask Kiro to update the plan: `Run gsd-plan on .kiro/specs/CHG0437000/` (Kiro will add the bug fix to the roadmap).
3. Update the relevant micro-spec and re-run `gsd-execute`.

---

## Best Practices for the Team

- **Never mix changes:** Do not put specs for CHG0001 and CHG0002 in the same folder. Kiro relies on directory isolation to stay focused.
- **Keep Micro-Specs Micro:** A single micro-spec should cover exactly one class, one table, or one function module. If a spec is getting too long, break it into two.
- **If Kiro Hallucinates:** If Kiro accidentally writes RAP or ABAP Cloud syntax, check your `.kiro/steering/tech.md` file to ensure the NW 7.50 guardrails are intact, and ensure you used the `gsd-execute` skill properly.
