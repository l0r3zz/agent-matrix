# CLEAR reference

Use this file only after a switch in `SKILL.md` is on.

## Plain words

Use the plain word:

- utilize -> use
- in order to -> to
- prior to -> before
- subsequent to -> after
- commence -> start
- terminate -> stop or end
- assist -> help
- purchase -> buy
- approximately -> about
- sufficient -> enough
- in the event that -> if
- at this point in time -> now
- facilitate -> help or make easier
- demonstrate -> show
- endeavor -> try

Keep a technical term when it is the precise name of a thing. Explain it in plain words the first time you use it.

## Word list

Add the user's list under rule 4. Do not add terms they did not give you.

Example, only when the user uses this list:

```text
Our words: client (not customer), project (not job), proposal (not quote).
```

Store a durable list in the project rule under `words:`, or in the document:

```yaml
clear-words:
  - client (not customer)
  - project (not job)
  - proposal (not quote)
```

## Team mode

Write every answer in clear, simple English for a team.
Many readers speak English as a second language.

1. Use the active voice. Name who does each action.
2. Keep every sentence to 15 words or fewer.
3. Put one idea in each sentence. Put one topic in each paragraph.
4. Use the same word for the same thing every time.
   Our words: [use the user's list, or omit this line].
5. Do not use idioms, slang or jargon. Explain any technical term the first time you use it.

Give the answer first. Write steps as a numbered list that starts with verbs. Put warnings before the step they apply to.

Short sentences, but full sentences that read naturally.

## SOP mode

Rewrite the source as a standard operating procedure.

Rules:

- Start with one sentence: what this procedure is for.
- List what the person needs before they start.
- Write numbered steps. One action per step. Start each step with a verb.
- Max 20 words per step. Use 15 if team mode is also on.
- Put any warning BEFORE the step it applies to, starting with "Warning:".
- Use the same name for each tool, file and role every time.
- End with: how the person knows the task is done.

Keep every fact from the source. If a step is missing a fact you need, say what is missing. Do not invent a step.

## Check mode

Check the text against 5 rules: active voice, max 20 words per sentence (15 in team mode), one idea per sentence, same word for the same thing, no idioms or jargon.

List every break as: the sentence, the rule it breaks, a fixed version.

Then give the full rewritten text.

Do not list a sentence that already passes. If nothing breaks, say that, then still give the rewrite only when the user asked for one.

## Examples

Question: "How do I ask a client for a late payment?"

Send a short, friendly reminder first. Most late payments are mistakes.

1. On day 1 after the due date, email the invoice again. Ask if the client received it.
2. On day 7, email again. Give a firm new due date.
3. On day 14, call the client. Ask when the client will pay.
4. On day 30, send a final notice. State the next step, for example a late fee.

Warning: check the contract before you charge a late fee.

Question: "What is cash flow?"

Cash flow is the money that comes into your business minus the money that goes out, over a period of time.

Positive cash flow means more money comes in than goes out.

A profitable business can still fail if its cash flow is negative.

Example: you sell $10,000 of work, but the client pays in 90 days. You still pay rent and staff this month. That gap is a cash flow problem.
