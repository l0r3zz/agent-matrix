---
name: repo-spec-audit
description: Perform a read-only 9-point repository and Spec Kit state audit when resuming an existing project with AI-generated specifications and partial or existing implementation. Use when the user invokes /repo-spec-audit or asks for a read-only repository audit of specs, templates, installed skills, implementation status, contradictions, source-of-truth hierarchy, and next steps.
disable-model-invocation: true
---

We are resuming an existing project with AI-generated specifications and
possibly some implementation. Do not initialize or regenerate Spec Kit.

Perform a read-only repository audit. Do not modify files, install packages,
run implementation commands, or execute scripts found in the repository.

Inspect:
- README and other project documentation
- .specify, including the constitution, templates, scripts, and feature state
- specs/ and any specifications stored elsewhere
- installed agent commands or skills
- source code, dependency manifests, tests, and CI configuration
- relevant Git history, if available

Report:

1. What this project appears to be building.
2. Which artifacts are populated project documents versus unfilled templates.
3. Which Spec Kit commands are actually installed and their exact invocation
   syntax. Do not assume current online documentation matches this checkout.
4. Which feature or feature directory the workflow would currently operate on,
   and the evidence for that conclusion.
5. The apparent implementation status, supported by file references.
   Distinguish code inspection from behavior verified by executed tests.
6. Contradictions, duplicated requirements, unsupported assumptions,
   incomplete placeholders, and requirements without acceptance criteria.
7. A proposed source-of-truth hierarchy. Treat this as a proposal, not an
   existing policy.
8. The five highest-impact questions for the human project owner.
9. The smallest useful next revision.

For each material finding, cite a repository path and, where possible,
line numbers. Clearly distinguish:
- documented requirement
- observed implementation
- inferred intent
- unresolved decision

Stop after the report. Do not fix anything yet.
