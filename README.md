# ✳ AgentHub — The Unified AI Developer CLI Manager

> A beautiful, fast, and lightweight CLI agent mission control. Manage, switch, inspect, and launch all your AI coding agents in one tap.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![CLI](https://img.shields.io/badge/Command-agenthub-ff6b35)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)](https://github.com/)

---

```text
┌─ ✦ AgentHub Workspace ✦ ────────────────────────────────────────────────────┐
│ ┌──────────────────────┐  AgentHub — Unified AI Developer CLI Manager       │
│ │  ✳  A G E N T H U B  │  Your mission control for coding agents: launch,   │
│ │    ▲  ⬡  ◈  ⬢  ▲     │  switch, and inspect.                              │
│ │  [ v1.1.0 • ACTIVE ] │                                                    │
│ └──────────────────────┘  ● 3/4 Agents Ready  •  Platform: Windows 11  •    │
│                           Python 3.13                                       │
│ ────────────────────────────────────────────────────────────────────────    │
│ 📁 Workspace: D:\Projects\MyAwesomeApp      ⚙ Config: ~/.agenthub/agents.json│
└────────────────────────────── Run agenthub --help for command line options ─┘
```

---

## ✨ Features

- **Warm Terminal Interface**: Terracotta/peach aesthetic, sticker badge, clean rounded panels, and status chips.
- **Installable System CLI**: Install once and run `agenthub` from any directory or terminal, just like `agy`, `codex`, or `gh`.
- **Auto-Detect & Health Check**: Automatically scans PATH for your AI agents (`agy`, `codex`, `opencode`, `agent/cursor`, and custom CLIs) and retrieves active versions.
- **Interactive Keyboard Controls**: Navigate with **↑ / ↓** or **j / k**, press **1-9** to quick-launch, or use single-letter hotkeys (`r`, `d`, `u`, `a`, `s`, `q`).
- **Direct CLI Subcommands**: Run `agenthub list`, `agenthub launch agy`, or `agenthub doctor` directly from scripts or shell shortcuts without entering the TUI.
- **AgentHub Doctor**: Comprehensive diagnostic suite inspecting Python paths, PATH resolution, environment variables, and config locations.
- **Zero Lock-in & Portable Config**: Automatically creates and persists user configuration in `~/.agenthub/agents.json`, with optional project-level `./agents.json` override.

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

This launches the interactive mission control. From here you can:
- Press **1 - 4** (or use **↑ / ↓** and **Enter**) to launch any installed AI agent directly in the current directory.
- Press **r** to refresh PATH detection.
- Press **d** to run AgentHub Doctor.
- Press **u** to check for and apply updates.
- Press **a** to register a new custom CLI tool.
- Press **s** to view settings and configuration paths.
- Press **q** to exit.

### 2. Direct CLI Subcommands

AgentHub works as a scriptable command-line tool just like git or agy:

```bash
# Print clean status table and exit
agenthub list

# Directly launch Gemini CLI (agy)
agenthub launch agy

# Directly launch Codex CLI
agenthub launch codex

# Launch by agent index number
agenthub launch 1

# Run system & environment health diagnostics
agenthub doctor

# Interactive update wizard for installed agents
agenthub update

# Add a new custom agent
agenthub add

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
| **r** | **Refresh**: re-scan PATH and update version strings |
| **d** | **Doctor**: run environment, PATH, and config diagnostics |
| **u** | **Update**: check and run update commands with confirmation |
| **a** | **Add**: register a new CLI agent interactively |
| **s** | **Settings**: open configuration details and file editor |
| **q** or **Esc** | **Quit**: exit AgentHub cleanly |

---

## 📋 Default Supported Agents

| Agent | Starter Command | Description |
|---|---|---|
| **Gemini CLI** | `agy` | Google's AI coding assistant CLI (Antigravity) |
| **Codex CLI** | `codex` | OpenAI's Codex CLI coding assistant |
| **OpenCode CLI** | `opencode` | Open-source terminal AI coding tool |
| **Cursor CLI** | `agent` | Cursor AI editor CLI interface |

*Any additional AI or developer CLI (e.g. `aider`, `gh`, `ollama`) can be added in 5 seconds via `agenthub add` or by editing `agents.json`.*

---

## ⚙️ Configuration

AgentHub stores your configuration in:
- **Global User Config (Default)**: `~/.agenthub/agents.json` (`%USERPROFILE%\.agenthub\agents.json` on Windows)
- **Project Override (Optional)**: `./agents.json` (if present in current directory)
- **Environment Variable**: set `AGENTHUB_CONFIG=/path/to/custom.json`

Example `agents.json`:

```json
{
  "agents": [
    {
      "name": "Gemini CLI",
      "command": "agy",
      "description": "Google's AI coding assistant CLI (Antigravity)",
      "install_method": "See documentation for Antigravity / Gemini CLI",
      "update_method": "agy update",
      "config_locations": [
        "%USERPROFILE%\\.gemini",
        "%USERPROFILE%\\.gemini\\settings.json"
      ]
    },
    {
      "name": "Aider CLI",
      "command": "aider",
      "description": "AI pair programming in your terminal",
      "install_method": "pip install aider-chat",
      "update_method": "pip install --upgrade aider-chat",
      "config_locations": [
        "%USERPROFILE%\\.aider.conf.yml"
      ]
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
