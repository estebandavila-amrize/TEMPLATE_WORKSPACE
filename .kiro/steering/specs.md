# Spec Workflow Rules

- Every new spec folder under `.kiro/specs/` MUST include a `.config.kiro` file at creation time. No exceptions.
- Format: `{"specId": "<uuid>", "workflowType": "<type>", "specType": "<feature|bugfix>"}` where workflowType is one of: requirements-first, design-first, fast-task.
- Every spec MUST have at least a `requirements.md` file for Kiro to recognize it in the Specs view.
- The `_template_CHG` folder is excluded - it is a template, not a spec.
