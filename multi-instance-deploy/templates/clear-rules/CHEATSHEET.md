# CLEAR skill cheat sheet

CLEAR is off until you say so. Use one phrase below.

| You want | Say this |
| --- | --- |
| This chat | `turn on CLEAR` |
| This chat, stop | `turn off CLEAR` |
| One answer | `CLEAR this` and paste the text |
| Check a draft | `check this with CLEAR` |
| One file | `Turn on CLEAR for path/to/file.md` |
| A whole project | `Turn on CLEAR for this project` |
| Shorter, for a team | `turn on CLEAR, team version` |
| A procedure | `Rewrite this as an SOP with CLEAR` |

## What each scope does

**This chat.** CLEAR applies to your answers until you say `turn off CLEAR`.

**One answer.** `CLEAR this` applies to that reply only.

**One file.** The agent writes `clear-rules: on` at the top of that markdown file. It also adds the path to `.cursor/rules/clear-rules.mdc`.

**One project.** The same rule file is set to `alwaysApply: true`.

**Stop a file.** Say `Turn off CLEAR for path/to/file.md`. You can also set `clear-rules: off` in that file.

## Modes

| Mode | Limit | What you get |
| --- | --- | --- |
| Standard | 20 words | The default. Active voice. One idea per sentence. |
| Team | 15 words | Say `team version`, or set `clear-mode: team`. |
| SOP | 20 words per step | A procedure. Each step starts with a verb. Warnings come before the step. |
| Check | Same as the mode you are in | Each broken sentence, the rule it breaks, a fix, then the full rewrite. |

## Skip CLEAR for one answer

Ask for creative writing, marketing copy, or name the style you want. CLEAR stays off for that answer.

## Load it into an Agent Matrix agent

The import file is `multi-instance-deploy/templates/clear-rules.zip`.

1. Open the agent UI.
2. Open Settings, then Skills, then Import Skills.
3. Choose `clear-rules.zip`.
4. Leave Namespace empty. The zip name sets it to `clear-rules`.
5. Choose Overwrite existing if you import this pack again.
6. Click Preview. It should list one skill folder.
7. Click Import.

The skill lands at `/a0/usr/skills/clear-rules/`. Import does not turn CLEAR on. Use the phrases in the table above in that agent's chat.

## The five rules

1. Use the active voice. Put the person or thing that does the action first.
2. Keep every sentence to 20 words or fewer. Team mode uses 15.
3. Put one idea in each sentence. Put one topic in each paragraph.
4. Use the same word for the same thing every time.
5. Do not use idioms, slang, or jargon. Explain a technical term in plain words the first time.

Give the answer first. Write steps as a numbered list. Start each step with a verb. Put a warning before the step it applies to.
