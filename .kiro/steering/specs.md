# Spec Workflow Rules

- Every new spec folder under `.kiro/specs/` MUST include a `.config.kiro` file at creation time. No exceptions.
- Format: `{"specId": "<uuid>", "workflowType": "<type>", "specType": "<feature|bugfix>"}` where workflowType is one of: requirements-first, design-first, fast-task.
- Every spec MUST have at least a `requirements.md` file for Kiro to recognize it in the Specs view.
- CHG specs use workflowType `design-first`. The workflow is: design.md → requirements.md → tasks.md.
- `new-change` ingests the functional document and produces `design.md` as the first substantive output.
- `plan` refines design.md, derives requirements.md from it, and generates tasks.md.
- SAP metadata (WRICEF ID, package, transport) lives in `design.md` under "SAP Context" — no separate WRICEF.md.
- `requirements.md` MUST include a "Verification Log" section for append-only audit trail.
- `design.md` MUST include an "Approval" section with status tracking.
- `tasks.md` entries MUST have checkbox subtasks for tracking completion.
- The `_template_CHG` folder is deleted — `new-change` scaffolds directly without templates.
