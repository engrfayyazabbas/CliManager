# ✳ AgentHub — The Unified AI Developer CLI Manager

> A beautiful, fast, and lightweight CLI agent mission control. Manage, switch, inspect, and launch all your AI coding agents in one tap.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![CLI](https://img.shields.io/badge/Command-agenthub-ff6b35)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)](https://github.com/)

---

```text
┌──────────────────────────────────────────┐
│  ✳ AgentHub  v1.3.0  ·  3/3 ready        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ Agents                                   │
│ ❯ 1  Claude Code (claude)   ● 2.0.1      │
│   2  Codex CLI   (codex)    ● 1.0.0      │
│   3  OpenCode    (opencode) ● 2.3.0      │
│                                          │
│ Actions                                  │
│   r  Sync & refresh                      │
│   u  Update agents                       │
│   m  Manage                              │
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
- **Interactive Keyboard Controls**: Navigate with **↑ / ↓** or **j / k**, press **1-9** to quick-launch, or use single-letter hotkeys (`r`, `u`, `m`, `q`).
- **Direct CLI Subcommands**: Run `agenthub list`, `agenthub launch agy`, or `agenthub doctor` directly from scripts or shell shortcuts without entering the TUI.
- **AgentHub Doctor**: Comprehensive diagnostic suite inspecting Python paths, PATH resolution, environment variables, and config locations — plus install suggestions for catalog agents you don't have yet.
- **Zero Lock-in & Portable Config**: Automatically creates and persists user configuration in `~/.agenthub/agents.json`, with optional project-level `./agents.json` override. User edits are never overwritten by auto-sync.

---

## 🚀 Installation

Requires **Python 3.10+**. After install, `agenthub` is available from any directory in your shell.

### Option 1: One-line install from GitHub (Recommended for others)

Install directly from the repo without cloning first:

```bash
pip install git+https://github.com/engrfayyazabbas/CliManager.git
```

Isolated install with **pipx** (keeps AgentHub in its own environment):

```bash
pipx install git+https://github.com/engrfayyazabbas/CliManager.git
```

Or with **uv**:

```bash
uv tool install git+https://github.com/engrfayyazabbas/CliManager.git
```

Verify:

```bash
agenthub --version
```

### Option 2: Clone then install

```bash
git clone https://github.com/engrfayyazabbas/CliManager.git
cd CliManager
pip install .
```

Editable install (for local development — changes to the repo apply immediately):

```bash
pip install -e .
```

### Option 3: Run without installing

From the project directory:

```bash
pip install -r requirements.txt
python agenthub.py
```

On Windows you can also use the helpers in the repo root:

```bash
.\agenthub.cmd
# or
.\agenthub.ps1
```

### Update

```bash
pip install --upgrade git+https://github.com/engrfayyazabbas/CliManager.git
# or, if you used pipx:
pipx upgrade agenthub
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
- Press **u** to update all installed agents in one batch (one confirmation).
- Press **m** for Manage: install/uninstall, remove, show/hide, details, doctor, config, reset.
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

# Install an agent from the catalog or config (interactive picker if omitted)
agenthub install claude
agenthub install claude --yes

# Uninstall an installed agent from your system and remove from config
agenthub uninstall claude
agenthub uninstall claude --yes

# Run every installed agent's update command in one batch
agenthub update

# Update a single agent (still one confirmation)
agenthub update codex

# Add a custom agent that isn't in the catalog (CLI-only escape hatch)
agenthub add

# Remove an agent from configuration (interactive picker if omitted)
agenthub remove codex
agenthub remove codex --yes

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
| **u** | **Update agents**: one preview + one confirmation, then sequential batch update with live progress |
| **m** | **Manage**: install/uninstall, remove, show/hide, details, doctor, config, reset |
| **q** or **Esc** | **Quit**: exit AgentHub cleanly |

Sub-screens use the same `↑ / ↓` (or `j / k`), `Enter`, number-jump and `q` controls as the main menu — no more numbered text prompts.

---

## 🛠️ Actions

**Sync & refresh (`r`)** — scans PATH plus common install dirs and registers newly installed agents.

**Update agents (`u`)** — shows one preview table of every installed agent that has an update command, asks **one** confirmation, then runs all updates sequentially with a live progress table and a final success/failure summary. No per-agent questions. Use `agenthub update <agent>` to target a single agent.

**Manage (`m`)** — setup and rarer maintenance (kept off the home screen to keep the launcher slim):
1. **Install agent** — install a missing catalog or configured agent.
2. **Uninstall agent** — runs the agent's package-manager uninstall command (`npm`, `uv tool`, `pip`, etc.) and removes it from `agents.json` (leaving user config directories untouched).
3. **Remove from AgentHub** — removes an agent from `agents.json` only (installed catalog agents are added to `ignored` so auto-sync won't re-add them).
4. **Show / hide agents** — `Enter` toggles visibility. Hidden agents are skipped by auto-sync (stored in the `ignored` list).
5. **Agent details** — versions, binary paths, config locations.
6. **Doctor** — environment/PATH diagnostics and catalog install suggestions. Still available as `agenthub doctor` from the CLI.
7. **Open config file** — opens `agents.json` in your editor.
8. **Reset & re-detect** — clears agents and the hidden list, then re-scans installed CLIs.

---

## 📋 Built-in Agent Catalog

AgentHub ships a catalog of known AI coding agents. On every run it probes each one and **only installed agents are added to your config and shown** — missing ones stay out of the way (see `agenthub doctor`).

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
3. Appends newly found agents to your config, tagged `"source": "catalog"` — commands in the `ignored` list are skipped.
4. Fills in missing metadata on existing entries — **never overwrites a non-empty field**, and never deletes entries you added or hid.

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
  ],
  "ignored": ["copilot"]
}
```

---

## 🛡️ Safety & Privacy

- **No background daemons** — AgentHub runs on-demand and consumes 0 resources when closed.
- **No telemetry or network tracking** — Only interacts with your local environment and CLI executables.
- **One confirmation for the whole update batch** — no package or tool is updated without your manual confirmation.
- **Hidden agents stay hidden** — the `ignored` list survives auto-sync; nothing is deleted from your config.
- **Zero credential tampering** — API keys and configuration secrets are never altered or exposed.

---

## 📄 License

MIT © AgentHub Contributors
