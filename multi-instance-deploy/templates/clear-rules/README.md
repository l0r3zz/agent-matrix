# Load CLEAR into an Agent Zero agent

The import file is `multi-instance-deploy/templates/clear-rules.zip`. The phrase list is `CHEATSHEET.md` in this folder.

1. Open the agent UI.
2. Open Settings, then Skills, then Import Skills.
3. Choose `clear-rules.zip`.
4. Leave Namespace empty. The zip name sets the namespace to `clear-rules`.
5. Choose Overwrite existing if you import this pack again.
6. Click Preview. The preview should list one skill folder.
7. Click Import.

The skill lands at `/a0/usr/skills/clear-rules/`.

Say "turn on CLEAR" in a chat with that agent. Say "turn off CLEAR" to stop. Say "CLEAR this" for one answer.

Rebuild the zip after you edit the files in this folder:

```bash
bash multi-instance-deploy/templates/clear-rules/package.sh
```
