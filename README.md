# ✳ AgentHub — The Unified AI Developer CLI Manager

> A beautiful, fast, and lightweight CLI agent mission control. Manage, switch, inspect, and launch all your AI coding agents in one tap.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![CLI](https://img.shields.io/badge/Command-agenthub-ff6b35)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)](https://github.com/)

---

```text
┌──────────────────────────────────────────┐
│  ✳ AgentHub  v1.2.0  ·  3/3 ready        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ Agents                                   │
│ ❯ 1  Claude Code (claude)   ● 2.0.1      │
│   2  Codex CLI   (codex)    ● 1.0.0      │
│   3  OpenCode    (opencode) ● 2.3.0      │
│                                          │
│ Actions                                  │
│   r  Sync & refresh                      │
│   d  Doctor                              │
│   q  Quit                                │
│                                          │
│ ↑↓ move · Enter open · 1-9 launch · q   │
└──────────────────────────────────────────┘
```

---

## ✨ Features

- **Simple Terminal UI**: Slim header, clear selection highlight, and short action labels — no clutter.
- **Installable System CLI**: Install once and run `agenthub` from any directory or terminal, just like `agy`, `codex`, or `gh`.
- **True Auto-Sync (no manual adding)**: Every launch scans PATH and common install dirs (npm global, pipx/uv, bun, cargo, Volta, Homebrew) for the built-in catalog of 17 AI coding agents. Anything installed is registered and shown automatically — no config editing required.
- **Interactive Keyboard Controls**: Navigate with **↑ / ↓** or **j / k**, press **1-9** to quick-launch, or use single-letter hotkeys (`r`, `d`, `u`, `a`, `s`, `q`).
- **Direct CLI Subcommands**: Run `agenthub list`, `agenthub launch agy`, or `agenthub doctor` directly from scripts or shell shortcuts without entering the TUI.
- **AgentHub Doctor**: Comprehensive diagnostic suite inspecting Python paths, PATH resolution, environment variables, and config locations — plus install suggestions for catalog agents you don't have yet.
- **Zero Lock-in & Portable Config**: Automatically creates and persists user configuration in `~/.agenthub/agents.json`, with optional project-level `./agents.json` override. User edits are never overwritten by auto-sync.

---

## 🚀 Installation

Install AgentHub as a global command on your machine:

### Option 1: Standard Pip Install (Recommended)

From the project directory:

```bash
# Install as an editable CLI tool
pip install -e .

# Or install as a regular package
pip install .
```

Now the `agenthub` starter command is available everywhere in your shell:

```bash
agenthub --version
```

### Option 2: Using pipx (Isolated CLI Environment)

If you prefer isolated Python CLI tools:

```bash
pipx install .
```

---

## 🎯 Quick Start

### 1. Interactive Workspace (Default)

Simply type `agenthub` anywhere in any project directory:

```bash
agenthub
```

This launches the interactive mission control. On startup AgentHub **auto-syncs**: it scans for installed AI CLIs, adds any new ones to your config, and shows them in the list. From here you can:
- Press **1 - 9** (or use **↑ / ↓** and **Enter**) to launch any installed AI agent directly in the current directory.
- Press **r** to sync and refresh (re-scan for newly installed agents).
- Press **d** to run AgentHub Doctor.
- Press **u** to check for and apply updates.
- Press **a** to register a new custom CLI tool that isn't in the catalog.
- Press **s** to view settings, configuration paths, and the catalog of installable agents.
- Press **q** to exit.

### 2. Direct CLI Subcommands

AgentHub works as a scriptable command-line tool just like git or agy:

```bash
# Print clean status table and exit
agenthub list

# Scan for installed agents and register new ones
agenthub sync

# Directly launch Antigravity CLI (agy)
agenthub launch agy

# Directly launch Claude Code
agenthub launch claude

# Launch by agent index number
agenthub launch 1

# Run system & environment health diagnostics (+ install suggestions)
agenthub doctor

# Interactive update wizard for installed agents
agenthub update

# Add a new custom agent (not in the catalog)
agenthub add

# Skip auto-discovery for a single run
agenthub --no-sync list

# View or open configuration
agenthub config --path
agenthub config --open
```

---

## ⌨️ Keyboard Shortcuts (Interactive Mode)

| Key | Action |
|---|---|
| **↑ / ↓** or **k / j** | Move selection cursor up / down |
| **Enter** | Launch highlighted agent or execute selected action |
| **1 – 9** | **Quick Launch**: immediately launch agent #1 through #9 |
| **r** | **Sync & refresh**: re-scan PATH and common install dirs, register newly installed agents |
| **d** | **Doctor**: run environment, PATH, and config diagnostics |
| **u** | **Update**: check and run update commands with confirmation |
| **a** | **Add**: register a new CLI agent interactively |
| **s** | **Settings**: open configuration details and file editor |
| **q** or **Esc** | **Quit**: exit AgentHub cleanly |

---

## 📋 Built-in Agent Catalog

AgentHub ships a catalog of known AI coding agents. On every run it probes each one and **only installed agents are added to your config and shown** — missing ones stay out of the way (view them in `agenthub doctor` or Settings → 6).

| Agent | Command | Typical install |
|---|---|---|
| Claude Code | `claude` | `npm install -g @anthropic-ai/claude-code` |
| Codex CLI | `codex` | `npm install -g @openai/codex` |
| Gemini CLI | `gemini` | `npm install -g @google/gemini-cli` |
| Antigravity CLI | `agy` | Antigravity installer |
| OpenCode CLI | `opencode` | `npm install -g opencode-ai` |
| Cursor CLI | `agent` / `cursor-agent` | Cursor installer |
| Aider | `aider` | `pip install aider-chat` |
| Goose | `goose` | Goose installer |
| Qwen Code | `qwen` | `npm install -g @qwen-code/qwen-code` |
| Crush | `crush` | `npm install -g @charmland/crush` |
| Amp | `amp` | `npm install -g @sourcegraph/amp` |
| Factory Droid | `droid` | Factory installer |
| OpenHands | `openhands` | `uv tool install openhands` |
| GitHub Copilot CLI | `copilot` | `npm install -g @github/copilot` |
| Continue CLI | `cn` | `npm install -g @continuedev/cli` |
| Codebuff | `codebuff` | `npm install -g codebuff` |
| Kimi CLI | `kimi` | `uv tool install kimi-cli` |

Install any of them and run `agenthub sync` (or just launch `agenthub`) — it appears automatically. Anything not in the catalog can still be added in 5 seconds via `agenthub add` or by editing `agents.json`; auto-sync never deletes or overwrites your manual entries.

---

## ⚙️ Configuration

AgentHub stores your configuration in:
- **Global User Config (Default)**: `~/.agenthub/agents.json` (`%USERPROFILE%\.agenthub\agents.json` on Windows)
- **Project Override (Optional)**: `./agents.json` (if present in current directory)
- **Environment Variable**: set `AGENTHUB_CONFIG=/path/to/custom.json`

### How auto-sync behaves

On startup (and on `agenthub sync` / pressing **r**) AgentHub:

1. Adds common CLI install dirs to `PATH` for the current process — `%APPDATA%\npm`, `~/.local/bin` (pipx/uv), `~/.bun/bin`, `~/.cargo/bin`, Volta, `/opt/homebrew/bin`, `/usr/local/bin`, and any `NPM_CONFIG_PREFIX`.
2. Probes every command in the built-in catalog (plus aliases such as `cursor-agent`).
3. Appends newly found agents to your config, tagged `"source": "catalog"`.
4. Fills in missing metadata on existing entries — **never overwrites a non-empty field**, and never deletes entries you added or removed.

Use `agenthub --no-sync <command>` to skip discovery for a single run.

Example `agents.json` (auto-sync output plus a manual entry):

```json
{
  "agents": [
    {
      "name": "Claude Code",
      "command": "claude",
      "description": "Anthropic's agentic coding assistant for the terminal",
      "install_method": "npm install -g @anthropic-ai/claude-code",
      "update_method": "npm update -g @anthropic-ai/claude-code",
      "config_locations": ["~/.claude", "~/.claude/settings.json"],
      "source": "catalog"
    },
    {
      "name": "Aider",
      "command": "aider",
      "description": "AI pair programming in your terminal",
      "install_method": "pip install aider-chat",
      "update_method": "pip install --upgrade aider-chat",
      "config_locations": ["~/.aider.conf.yml"],
      "source": "user"
    }
  ]
}
```

---

## 🛡️ Safety & Privacy

- **No background daemons** — AgentHub runs on-demand and consumes 0 resources when closed.
- **No telemetry or network tracking** — Only interacts with your local environment and CLI executables.
- **Explicit confirmation for updates** — No package or tool is updated without your manual confirmation.
- **Zero credential tampering** — API keys and configuration secrets are never altered or exposed.

---

## 📄 License

MIT © AgentHub Contributors
