# Agent Zero Plugin Architecture & Repository Research Report

**Date:** 2026-04-03
**Researcher:** Agent Zero Deep Research (agent0-2)

---

## Table of Contents

1. [a0-plugins — Plugin Index Repository](#1-a0-plugins--plugin-index-repository)
2. [a0-example-plugin — Plugin Template](#2-a0-example-plugin--plugin-template)
3. [whatsapp-automation — Messaging Integration Plugin](#3-whatsapp-automation--messaging-integration-plugin)
4. [matrix-mcp-server-r2 — Rust Matrix MCP Server](#4-matrix-mcp-server-r2--rust-matrix-mcp-server)
5. [GHCR Container Package](#5-ghcr-container-package)
6. [matrix-bot Template — Dual-Runtime Matrix Bot](#6-matrix-bot-template--dual-runtime-matrix-bot)
7. [Cross-Cutting Analysis](#7-cross-cutting-analysis)

---

## 1. a0-plugins — Plugin Index Repository

**URL:** https://github.com/agent0ai/a0-plugins
**Purpose:** Community-maintained INDEX of plugins visible in Agent Zero. Contains NO plugin code.

### File Structure

~~~
a0-plugins/
├── .github/workflows/       # CI validation automation
├── authors/agent0ai/        # Author metadata
├── generated/thumbnails/    # Auto-generated fallback thumbnails
├── plugins/                 # One subfolder per registered plugin
│   └── <plugin_name>/
│       ├── index.yaml        # REQUIRED — plugin metadata pointing to GitHub repo
│       └── thumbnail.png     # OPTIONAL — square, ≤20KB
├── scripts/                 # Utility scripts
├── .gitignore
├── LICENSE
├── README.md
└── TAGS.md                  # Recommended tag vocabulary
~~~

### Key Configuration: index.yaml

This is the ONLY required file per plugin entry. It is a pointer to the actual plugin repo.

~~~yaml
# REQUIRED fields:
title: Example Plugin           # max 50 chars
description: One-sentence desc   # max 500 chars
github: https://github.com/owner/repo  # Must contain plugin.yaml at root

# OPTIONAL fields:
tags:                            # up to 5 tags from TAGS.md
  - example
  - template
screenshots:                     # up to 5 image URLs, each ≤2MB
  - https://raw.githubusercontent.com/.../main/docs/main.png
~~~

### Registration Process

1. Submit a PR adding exactly ONE new subfolder under `plugins/`
2. Folder name: lowercase letters, numbers, underscores only (`^[a-z0-9_]+$`)
3. Folders starting with `_` are reserved (internal/project use, hidden from Agent Zero)
4. CI automatically validates: file format, character limits, GitHub URL accessibility, plugin.yaml existence at target repo root, name match between folder and remote plugin.yaml `name` field
5. Human maintainer reviews and merges

### Constraints

- Total `index.yaml` file: ≤2000 characters
- `github` URL must point to a repo with `plugin.yaml` at root
- Remote `plugin.yaml` `name` field MUST exactly match the index folder name
- Thumbnail must be square aspect ratio

---

## 2. a0-example-plugin — Plugin Template

**URL:** https://github.com/agent0ai/a0-example-plugin
**Purpose:** Canonical example demonstrating Agent Zero plugin file structure and conventions.

### File Structure

~~~
a0-example-plugin/
├── screenshots/              # Plugin screenshots for index listing
├── webui/                    # Web UI components loaded into Agent Zero interface
├── .gitignore
├── LICENSE                   # MIT
├── README.md
├── default_config.yaml       # Default configuration values
├── hooks.py                  # Lifecycle hook functions
└── plugin.yaml               # Plugin manifest (REQUIRED)
~~~

### plugin.yaml — The Plugin Manifest

This is the core metadata file that Agent Zero reads to discover, register, and manage the plugin.

~~~yaml
name: te_st1                    # Internal identifier — MUST match index folder name
title: Example Plugin 1         # Human-readable display name
description: Just an example to demonstrate plugin structure
version: 1.0.1                  # Semantic version
settings_sections: example, test, template   # UI settings panel sections
per_project_config: true        # Can be configured differently per project
per_agent_config: true          # Can be configured differently per agent profile
always_enabled: false           # If true, cannot be disabled
~~~

**Required fields:** `name`, `title`, `description`, `version`
**Optional fields:** `settings_sections`, `per_project_config`, `per_agent_config`, `always_enabled`

### hooks.py — Lifecycle Hooks

Defines functions called by Agent Zero at specific lifecycle events:

~~~python
def install():
    """Called when plugin is installed. Use for setup, downloading resources, etc."""
    print("Install hook started")
    sleep(3)  # Placeholder for real setup operations
    print("Install hook completed")

def uninstall():
    """Called when plugin is removed. Use for cleanup."""
    print("Uninstall hook started")
    sleep(3)  # Placeholder for real cleanup operations
    print("Uninstall hook completed")
~~~

**Known hooks:** `install()`, `uninstall()` — both take no arguments.

### default_config.yaml — Default Settings

Provides default configuration values that Agent Zero loads when the plugin is initialized:

~~~yaml
assistant_name: "Example Assistant"
age: 30
voice: "female"
~~~

These values populate the settings UI sections defined in `settings_sections`.

### webui/ Directory

Contains web UI components that are loaded into Agent Zero's web interface (contents not detailed in repo).

---

## 3. whatsapp-automation — Messaging Integration Plugin

**URL:** https://github.com/pachuki87/whatsapp-automation
**Purpose:** Full WhatsApp Web automation via persistent headless Chrome sessions. Demonstrates a complex, real-world Agent Zero plugin.

### File Structure

~~~
whatsapp-automation/
├── .claude/                   # Claude AI configuration
├── scripts/
│   ├── install.sh             # Automatic installation
│   ├── start_whatsapp_persistent.sh  # Launch Chrome with persistent profile
│   ├── check_persistence.sh   # Verify persistence files
│   └── monitor_chrome.sh      # Monitor Chrome process
├── CONTRIBUTING.md
├── PULL_REQUEST_GUIDE.md
├── README.md
├── index.yaml                 # For a0-plugins index submission
├── plugin.yaml                # Agent Zero plugin manifest
└── thumbnail.jpg
~~~

Runtime data directory (created by plugin):
~~~
/a0/usr/workdir/chrome-profile/
├── Default/
│   ├── Cookies, Cookies-journal
│   ├── Session Storage/, Local Storage/, IndexedDB/
│   ├── Sessions/, Web Data, History, Preferences
└── Local State
~~~

### plugin.yaml — Rich Plugin Manifest

This is a significantly more detailed plugin.yaml than the example plugin, showing the full range of possible fields:

~~~yaml
name: whatsapp_automation
version: "1.0.0"
display_name: "WhatsApp Automation"
description: "Full WhatsApp Web automation with persistent Chrome sessions..."
author: "pachuki87"
license: "MIT"
repository: "https://github.com/pachuki87/whatsapp-automation"
homesite: "https://github.com/pachuki87/whatsapp-automation"
category: automation
tags:
  - whatsapp
  - automation
  - chrome
  - headless
  - messaging

dependencies:
  agent_zero:
    min_version: "1.0.0"
  tools_required:
    - code_execution_tool
    - chrome_devtools
  optional:
    - browser_agent

environment:
  os:
    - linux
    - docker
  browser:
    - chrome
    - chromium

installation:
  type: "simple"
  commands:
    - "mkdir -p /a0/usr/workdir/chrome-profile"
    - "chmod 755 /a0/usr/workdir/chrome-profile"

configuration:
  variables:
    - name: "CHROME_PROFILE_DIR"
      description: "Directory for the persistent Chrome profile"
      default: "/a0/usr/workdir/chrome-profile"
      required: true
    - name: "WHATSAPP_URL"
      description: "WhatsApp Web URL"
      default: "https://web.whatsapp.com"
      required: false
    - name: "DEBUG_PORT"
      description: "Chrome DevTools port"
      default: "9222"
      required: false

setup:
  description: "Configures Chrome with persistent profile..."
  steps:
    - "Verify Google Chrome is installed"
    - "Create persistent directory for the Chrome profile"
    - "Start Chrome with persistence flags"
    - "Scan QR code the first time"
    - "Verify that the session remains after reboots"

permissions:
  required:
    - "terminal_access"
    - "file_system_write"
    - "network_access"
  optional:
    - "screen_capture"

features:
  - name: "Persistent Session"
    description: "Keeps WhatsApp Web session active after system reboots"
  - name: "Message Automation"
    description: "Sends and receives messages automatically"
  - name: "Conversation Monitoring"
    description: "Monitors specific chats in real time"
  - name: "Headless Operation"
    description: "Works without graphical interface"
  - name: "Docker Compatible"
    description: "Compatible with Docker containers"
  - name: "Chrome DevTools Integration"
    description: "Integrates with Chrome DevTools MCP"

usage:
  examples:
    - title: "Start Chrome with persistent session"
      code: "google-chrome --headless --user-data-dir=..."
    - title: "Take snapshot of WhatsApp Web"
      code: "chrome_devtools.take_snapshot"
    - title: "Send message"
      code: "chrome_devtools.fill"

troubleshooting:
  common_issues:
    - problem: "Chrome doesn't start"
      solution: "Verify port 9222 is not in use"
    - problem: "Session is lost after reboot"
      solution: "Ensure --user-data-dir points to permanent directory"
    - problem: "QR code appears every time"
      solution: "Verify profile directory permissions and disk space"

changelog:
  - version: "1.0.0"
    date: "2026-03-26"
    changes:
      - "Initial plugin version"
      - "Persistent WhatsApp Web session"
      - "Chrome DevTools MCP integration"

screenshots:
  - "https://raw.githubusercontent.com/.../whatsapp%20agent%20zero.png"
  - "https://raw.githubusercontent.com/.../thumbnail.jpg"
~~~

### Integration Architecture

- Uses Chrome DevTools Protocol (CDP) on port 9222
- Agent Zero interacts via `chrome_devtools` MCP tools: `take_snapshot`, `take_screenshot`, `fill`, `click`, `navigate_page`
- No `hooks.py` — installation handled by shell scripts in `scripts/`
- QR code scanned once; persistent Chrome profile preserves session

---

## 4. matrix-mcp-server-r2 — Rust Matrix MCP Server

**URL:** https://github.com/l0r3zz/matrix-mcp-server-r2
**Purpose:** Drop-in Rust replacement for the TypeScript matrix-mcp-server. Exposes Matrix operations as MCP tools over Streamable HTTP transport.

### File Structure

~~~
matrix-mcp-server-r2/
├── .a0proj/                   # Agent Zero project metadata
├── .cursor/rules/             # Cursor IDE rules
├── .github/workflows/         # CI/CD — GHCR image publishing
├── reference/
│   ├── ts-source/             # Original TypeScript implementation (reference)
│   └── docs/                  # Plans, specs, operational docs
├── spec/
│   └── matrix-mcp-v1-v2.yml   # v1/v2 API specification
├── src/
│   ├── main.rs                # Entry point: axum/rmcp wiring, graceful shutdown
│   ├── lib.rs                 # Library re-exports
│   ├── config.rs              # Env var configuration loading
│   ├── error.rs               # Error types
│   ├── auth.rs                # Per-request auth context (future)
│   ├── matrix/
│   │   ├── client.rs          # matrix-sdk client creation + background sync
│   │   └── cache.rs           # TTL-based client cache
│   └── mcp/
│       └── server.rs          # MatrixMcpServer: 20 MCP tools + ServerHandler
├── tests/
│   ├── config_tests.rs
│   ├── cache_tests.rs
│   └── server_tool_list_tests.rs
├── .dockerignore
├── .env.example
├── .gitignore
├── Cargo.lock
├── Cargo.toml
├── Dockerfile
└── README.md
~~~

**Language breakdown:** TypeScript 55.3% (reference code), Rust 43.1%, Dockerfile 1.6%

### Architecture

~~~
MCP Client (Agent Zero)
  → POST /mcp
    → Axum HTTP (CORS, trace)
      → rmcp StreamableHttpService
        → ServerHandler (20 MCP tools)
          → matrix-sdk Client
            → Matrix Homeserver
~~~

### 20 MCP Tools (v1 API Parity)

| Category | Tools |
|----------|-------|
| Rooms | list-joined-rooms, get-room-info, create-room, join-room, leave-room |
| Messages | get-room-messages, get-messages-by-date, send-message, send-direct-message |
| Members | get-room-members, invite-user, identify-active-users |
| Profiles | get-user-profile, get-my-profile, get-all-users |
| Admin | set-room-name, set-room-topic |
| Discovery | search-public-rooms, get-notification-counts, get-direct-messages |

### Tech Stack

- Rust 2021 edition
- rmcp 1.2 (official Rust MCP SDK)
- axum + tower-http
- matrix-sdk 0.10
- serde + schemars
- tracing for logging
- matrix-sdk-crypto behind `e2ee` feature flag (Phase 3)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MATRIX_HOMESERVER_URL` | Yes | e.g., `https://matrix.example.com` |
| `MATRIX_USER_ID` | Yes | e.g., `@bot:example.com` |
| `MATRIX_ACCESS_TOKEN` | Yes | Matrix access token |
| `PORT` | No | Server port (default: 3000) |
| `SKIP_MATRIX_INIT` | No | `true` for protocol-only testing |

### Build & Run

~~~bash
cp .env.example .env
# Edit .env with credentials
cargo build
cargo run
# MCP endpoint: http://localhost:3000/mcp
# Health check: http://localhost:3000/health
~~~

### Docker Publishing

- Built by GitHub Actions on semver tag push (e.g., `git tag -a v0.1.1`)
- Published to GHCR: `ghcr.io/l0r3zz/matrix-mcp-server-r2`
- `:latest` tag updated on each push

### Project Status

| Phase | Status |
|-------|--------|
| Phase 0: Scaffolding | Done |
| Phase 1: Spec writing | Done |
| Phase 2: v1 Implementation (API parity) | Done |
| Phase 3: E2EE | Not started |
| Phase 4: Integration testing & deployment | Not started |

---

## 5. GHCR Container Package

**URL:** https://github.com/l0r3zz/matrix-mcp-server-r2/pkgs/container/matrix-mcp-server-r2

### Available Tags

| Tag | Status | Published |
|-----|--------|-----------|
| `latest` | Points to 0.1.1 | ~2026-03-31 |
| `0.1.1` | Current release | ~2026-03-31 |
| `0.1.0` | Previous release | ~2026-03-29 |

### Pull Commands

~~~bash
# Latest
docker pull ghcr.io/l0r3zz/matrix-mcp-server-r2:latest

# Specific version
docker pull ghcr.io/l0r3zz/matrix-mcp-server-r2:0.1.1

# Platform-specific (linux/amd64)
docker pull ghcr.io/l0r3zz/matrix-mcp-server-r2:0.1.1@sha256:7667e1ed07177b797ac8642ac75d1be9cc0fbed844112ea1c77affcadb3e2c0b
~~~

### Versioning

- Image tags match the version reported by `GET /health` and `--version` flag
- Automated via GitHub Actions workflow on `v*` tag push
- Manual trigger available: Actions → Publish Docker image → Run workflow

---

## 6. matrix-bot Template — Dual-Runtime Matrix Bot

**URL:** https://github.com/l0r3zz/agent-matrix/tree/main/multi-instance-deploy/templates/matrix-bot
**Purpose:** Matrix protocol bot that bridges Matrix chat with Agent Zero AI backend. Supports both Python and Rust runtimes.

### File Structure

~~~
matrix-bot/
├── rust/
│   ├── src/
│   │   ├── main.rs              # Main bot binary source
│   │   └── bin/
│   │       └── set_display_name.rs  # Display name utility
│   ├── Cargo.lock
│   ├── Cargo.toml
│   └── README.md
├── .bot_runtime                  # Runtime selector: "python" or "rust"
├── .env.template                 # Environment variable template
├── build-rust.sh                 # Compiles Rust binaries
├── matrix-bot-rust               # Compiled Rust binary
├── matrix_bot.py                 # Python bot implementation
├── requirements.txt              # Python dependencies
├── run-matrix-bot.sh             # Launch script (reads .bot_runtime)
├── run-set-display-name.sh       # Display name utility launcher
└── set_display_name.py           # Python display name setter
~~~

### Dual Runtime Architecture

- `.bot_runtime` file contains either `python` or `rust` (default: `python`)
- `switch-matrix-bot.sh` toggles between runtimes
- `run-matrix-bot.sh` reads `.bot_runtime` and launches the appropriate binary
- Both runtimes implement identical functionality

### Rust Dependencies (Cargo.toml)

| Crate | Version | Features |
|-------|---------|----------|
| anyhow | 1 | — |
| dotenvy | 0.15 | — |
| log | 0.4 | — |
| env_logger | 0.11 | — |
| reqwest | 0.12 | json, rustls-tls |
| serde | 1 | derive |
| serde_json | 1 | — |
| tokio | 1 | macros, rt-multi-thread, signal, time, fs |
| urlencoding | 2.1 | — |
| pulldown-cmark | 0.12 | — |

Produces two binaries: `matrix-bot-rust` and `set-display-name-rust`

### Rust Bot Capabilities (main.rs)

| Feature | Implementation |
|---------|----------------|
| Sync | Full-state + incremental long-poll via `/_matrix/client/v3/sync` |
| Join Rooms | Auto-join on invite, 4 retries with backoff, greeting message |
| Send Messages | `m.room.message` with plain text + HTML (Markdown→HTML via pulldown-cmark) |
| Message Chunking | Long responses split into ≤32,000 char segments |
| Display Name | PUT to `/_matrix/client/v3/profile/{user}/displayname` |
| Typing Indicators | Typing on before query, off after response |
| Trigger Detection | Responds to `@agentname:` or `@all-agents:` in groups; all messages in 1:1 |
| Context Persistence | Per-room conversation context IDs saved to `room_contexts.json` |
| Agent Zero API | Forwards messages to A0 API, handles 404 by clearing stale contexts |
| Crash Recovery | Up to 10 restart attempts with exponential backoff |
| Graceful Shutdown | SIGTERM/Ctrl+C handling (Unix-aware) |

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MATRIX_HOMESERVER_URL` | Yes | `http://localhost:8008` | Matrix homeserver |
| `MATRIX_USER_ID` | Yes | — | Bot's Matrix ID |
| `MATRIX_ACCESS_TOKEN` | Yes | — | Auth token |
| `MATRIX_DEVICE_ID` | No | `AgentZeroBot` | Device ID |
| `A0_API_URL` | No | `http://localhost:80/api/api_message` | Agent Zero endpoint |
| `A0_API_KEY` | No | `""` | Agent Zero API key |
| `BOT_DISPLAY_NAME` | No | `Agent Zero` | Display name in rooms |
| `AGENT_IDENTITY` | No | (= BOT_DISPLAY_NAME) | System prompt identity |
| `SYNC_TIMEOUT_MS` | No | `30000` | Sync long-poll timeout |
| `TRIGGER_PREFIX` | Template | (auto-generated) | Override trigger detection |
| `A0_AGENT_PROFILE` | Template | — | Agent profile override |
| `MATRIX_BOT_RUNTIME` | No | — | Override for python/rust |

### Build & Deploy

~~~bash
# Build Rust binaries
./build-rust.sh

# Switch runtime
./switch-matrix-bot.sh     # Toggles .bot_runtime

# Run bot
./run-matrix-bot.sh        # Reads .bot_runtime, launches appropriate binary

# Set display name
./run-set-display-name.sh
~~~

---

## 7. Cross-Cutting Analysis

### Plugin Architecture Summary

Agent Zero's plugin system operates on a two-tier model:

**Tier 1: Plugin Index (a0-plugins repo)**
- Central registry of available plugins
- Each entry is a thin `index.yaml` pointer to a GitHub repo
- CI-validated, human-reviewed PR process
- Folder name must match remote `plugin.yaml` `name` field

**Tier 2: Plugin Repository (individual repos)**
- Contains actual plugin code and configuration
- MUST have `plugin.yaml` at root (manifest)
- MAY have `hooks.py` (lifecycle hooks: install/uninstall)
- MAY have `default_config.yaml` (default settings)
- MAY have `webui/` directory (UI components)
- MAY have `scripts/` directory (setup automation)

### plugin.yaml Field Comparison

| Field | Example Plugin | WhatsApp Plugin | Notes |
|-------|---------------|-----------------|-------|
| `name` | ✅ | ✅ | REQUIRED, must match index folder |
| `title` / `display_name` | ✅ `title` | ✅ `display_name` | Naming varies |
| `description` | ✅ | ✅ | REQUIRED |
| `version` | ✅ | ✅ | REQUIRED |
| `author` | — | ✅ | — |
| `license` | — | ✅ | — |
| `repository` | — | ✅ | — |
| `category` | — | ✅ | — |
| `tags` | — | ✅ | — |
| `settings_sections` | ✅ | — | Controls UI panels |
| `per_project_config` | ✅ | — | — |
| `per_agent_config` | ✅ | — | — |
| `always_enabled` | ✅ | — | — |
| `dependencies` | — | ✅ | min_version, tools_required |
| `environment` | — | ✅ | os, browser requirements |
| `installation` | — | ✅ | type, commands |
| `configuration` | — | ✅ | env variables with defaults |
| `permissions` | — | ✅ | required, optional |
| `features` | — | ✅ | Descriptive feature list |
| `usage` | — | ✅ | Example code snippets |
| `troubleshooting` | — | ✅ | common_issues |
| `changelog` | — | ✅ | Version history |
| `screenshots` | — | ✅ | Image URLs |

### Integration Patterns

| Component | Integration Method | Protocol |
|-----------|-------------------|----------|
| a0-plugins | GitHub PR → CI validation → merge | Git/GitHub |
| Example Plugin | hooks.py lifecycle + default_config.yaml | Python hooks |
| WhatsApp Plugin | Chrome DevTools Protocol (CDP) | MCP (chrome_devtools tools) |
| matrix-mcp-server-r2 | Streamable HTTP MCP transport | MCP over HTTP (POST /mcp) |
| matrix-bot | Direct Matrix Client-Server API | Matrix CS API + Agent Zero REST API |

### Key Architectural Insight

The matrix-mcp-server-r2 and the matrix-bot serve complementary but distinct roles:

- **matrix-mcp-server-r2**: Gives Agent Zero the ABILITY to interact with Matrix (20 MCP tools). Agent Zero initiates all actions.
- **matrix-bot**: Gives Agent Zero PRESENCE in Matrix. It listens for messages, auto-joins rooms, and forwards conversations to Agent Zero's API. External users initiate interactions.

Together they form a complete bidirectional bridge: the bot handles inbound (Matrix → Agent Zero) and the MCP server handles outbound (Agent Zero → Matrix).
