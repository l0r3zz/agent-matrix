---
name: "clear-rules"
description: "Writes and edits prose with the CLEAR rules: active voice, 20 words or fewer, one idea per sentence, the same word for the same thing, and no idioms or jargon. Use when the user says CLEAR, turn on CLEAR, turn off CLEAR, simplified technical English, STE, or aircraft manual style, or asks for a CLEAR rewrite, check, or SOP. Also use when a file sets clear-rules: on. Do not apply the rules unless a switch is on."
version: "1.0.0"
author: "Agent Matrix"
tags: ["writing", "clear", "style"]
trigger_patterns:
  - "CLEAR"
  - "CLEAR rules"
  - "turn on CLEAR"
  - "turn off CLEAR"
  - "CLEAR this"
  - "simplified technical English"
  - "aircraft manual"
---

# CLEAR rules

CLEAR is off until a switch below turns it on. Loading this skill is not a switch.

## Agent Zero

This skill is `clear-rules`. Read `reference.md` in this skill folder before team mode, SOP mode, or check mode. Read `rule-template.md` only when the user asks you to turn CLEAR on for a Cursor project.

## Switches

Apply CLEAR only when one of these is true. Later instructions in the same user message win.

1. **This chat.** The user loaded this skill and asked you to use it, or said "CLEAR on", "turn on CLEAR", or "use CLEAR rules". Stay on until they say "CLEAR off" or "turn off CLEAR".
2. **This project.** `.cursor/rules/clear-rules.mdc` exists and `alwaysApply: true`.
3. **These documents.** The target file matches `globs` in `.cursor/rules/clear-rules.mdc`, or the file's frontmatter or first 30 lines say `clear-rules: on`.
4. **This answer only.** The user says "CLEAR this", "apply CLEAR to this", or "check this with CLEAR". Apply it to that answer, then stop.

Turn a switch off when the user asks:

- **This chat.** Stop. Do not edit project files.
- **This project.** Set `alwaysApply: false` in `.cursor/rules/clear-rules.mdc`. If no `globs` remain, delete that rule file only after the user confirms.
- **One document.** Remove that path from `globs`. Remove `clear-rules: on` from that file.

When the user names files or a project and asks to turn CLEAR on, write the rule file. Use `rule-template.md` in this skill folder. One pattern per document or glob. Set `alwaysApply: true` only when they want the whole project. On a markdown file, also set frontmatter `clear-rules: on` so the opt-in is visible in the file.

Leave code, commands, quotes, citations, identifiers, and proper names unchanged. CLEAR applies to prose you write for the user and to prose in opted-in documents.

## Escape

These rules apply to normal answers and to opted-in documents. When the user asks for creative writing, marketing copy, or a specific style, follow that request instead.

Use this order when more than one instruction applies:

1. The user's latest explicit request.
2. `clear-rules: off` on the file you are writing.
3. An on switch for that target (this chat, this project, or this document).
4. A project voice guide, when no CLEAR switch is on for that target.

When CLEAR is on and a voice guide also applies, follow CLEAR for that target. Say so in one sentence.

## Rules

Follow this block when a switch is on. It is the standard mode (20 words).

Write every answer in clear, simple English. Follow these 5 rules:

1. Use the active voice. Put the person or thing that does the action first.
2. Keep every sentence to 20 words or fewer.
3. Put one idea in each sentence. Put one topic in each paragraph.
4. Use the same word for the same thing every time. Do not use synonyms for variety.
5. Do not use idioms, slang or jargon. If you must use a technical term, explain it in plain words the first time.

Also:

- Give the answer first. Give the explanation after it.
- Write steps as a numbered list. Start each step with a verb.
- Put warnings before the step they apply to, not after it.
- Do not add filler, praise or a summary of what you just said.
- Short sentences, but full sentences that read naturally.

Use the plain words in `reference.md`. If the user, the file, or the project rule gives a word list, use those words. Do not invent a business glossary.

CLEAR makes text easier to read. It does not make a claim true. Do not drop a caveat, a number, or a condition to hit the word limit. If a sentence is long because of a precise term, split the sentence. Keep the term.

## Modes

Read `reference.md` and follow that mode when the user, frontmatter `clear-mode`, or the project rule asks for it.

| Mode | When |
|------|------|
| `standard` | Default. 20 words. The block above. |
| `team` | The user says "team version", sets `clear-mode: team`, or says readers use English as a second language. 15 words. |
| `sop` | The user asks for an SOP, a checklist, or a procedure. |
| `check` | The user asks to check, audit, or score existing text. List each break, then give the full rewrite. |

`clear-mode` lives in the document frontmatter or in the project rule. Allowed values: `standard`, `team`, `sop`. A check request is always `check`, even if the file says `standard`.

## Document marker

```yaml
---
clear-rules: on
clear-mode: standard
---
```

`clear-rules: off` on a file beats a project rule and a chat switch for that file.

## Conflict

If another instruction says "be detailed", "write long", or "use a warm voice", and a CLEAR switch is on for this target, follow CLEAR. Tell the user about the conflict in one sentence.
