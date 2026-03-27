# matrix-bot Rust runtime

This folder contains the optional Rust implementation of the matrix-bot template.

## Build

From `multi-instance-deploy/templates/matrix-bot/`:

```bash
./build-rust.sh
```

This produces:

- `matrix-bot-rust`
- `set-display-name-rust`

## Switch runtime

Use `switch-matrix-bot.sh` to toggle between Python and Rust runtimes.

- Python (default): `.bot_runtime=python`
- Rust (optional): `.bot_runtime=rust`
