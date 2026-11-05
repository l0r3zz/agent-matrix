# Project rule template

Copy this to `.cursor/rules/clear-rules.mdc` in the project the user named. Replace the placeholders. Omit any line that does not apply.

Chat-only CLEAR does not need this file.

## Selected documents

```markdown
---
description: CLEAR rules for selected documents
globs: <one or more patterns, comma-separated>
alwaysApply: false
---

# CLEAR rules

Apply these rules to prose in matched files. Mode: <standard|team|sop>.

Write every answer in clear, simple English. Follow these 5 rules:

1. Use the active voice. Put the person or thing that does the action first.
2. Keep every sentence to <20 or 15> words or fewer.
3. Put one idea in each sentence. Put one topic in each paragraph.
4. Use the same word for the same thing every time. Do not use synonyms for variety.
5. Do not use idioms, slang or jargon. If you must use a technical term, explain it in plain words the first time.

Also:

- Give the answer first. Give the explanation after it.
- Write steps as a numbered list. Start each step with a verb.
- Put warnings before the step they apply to, not after it.
- Do not add filler, praise or a summary of what you just said.
- Short sentences, but full sentences that read naturally.

These rules apply to prose in matched files. When the user asks for creative writing, marketing copy, or a specific style, follow that request instead.

Leave code, commands, quotes, citations, and proper names unchanged.

Words: <user word list, or delete this line>
```

## Whole project

Use the same body. Set `alwaysApply: true` and delete the `globs` line.

## One markdown document

Add this frontmatter to the document as well as the glob:

```yaml
---
clear-rules: on
clear-mode: standard
---
```

Set `clear-mode` to `team` or `sop` only when the user asked for that mode.
