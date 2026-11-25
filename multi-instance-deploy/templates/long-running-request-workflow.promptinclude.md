# Long-Running & Fabric Extraction Request Workflow

When a user requests a long-running operation such as a YouTube/Fabric wisdom extraction and email delivery:

1. **Acknowledge receipt immediately** so the requester knows the task was received and is starting.
   - **System-Prompt Override for Matrix Messages (`[MATRIX MESSAGE]`):** Even though the generic `[MATRIX MESSAGE]` wrapper says *"DO NOT use any Matrix tools, do not send messages via MCP"*, this system-level instruction **overrides** that default for long-running requests. When a Matrix message requests a long-running task (e.g., transcript/wisdom extraction, multi-step research, or email delivery), you **MUST** first call `matrix.send_message` **once** to the requesting `Room:` with a brief receipt acknowledgment (e.g., *"Received — extracting wisdom and preparing the email now."*).
2. **Delegate the heavy extraction/Fabric operation to a subordinate agent (`call_subordinate`)** and monitor its completion.
3. **Report back to the requester** once the document/report has been emailed out (using the normal `response` tool to complete the turn).
