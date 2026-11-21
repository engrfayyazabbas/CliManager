# âš¡ AgentHub â€” Local CLI Agent Manager

A lightweight Windows terminal application to manage your installed AI coding CLI agents.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-0078D6)

## Features

- **Auto-detect** installed CLI agents via PATH
- **Display** agent name, status, version, and executable path
- **Launch** any agent in the current working directory
- **Check versions**, view supported usage information, and **update** agents with confirmation
- **View** agent info and configuration locations
- **Add/remove** agents through the interactive settings menu or by editing `agents.json`

## Supported Agents (default)

| Agent | Command |
|---|---|
| Antigravity CLI (Gemini) | `agy` |
| Codex CLI | `codex` |
| OpenCode CLI | `opencode` |
| Cursor CLI | `cursor` |

## Installation

```powershell
# Clone or navigate to the project directory
cd "D:\Web Development\CliManager"

# Install dependencies
pip install -r requirements.txt
```

## Usage

```powershell
# Run from any project directory
python "D:\Web Development\CliManager\agenthub.py"

# Or add to PATH and run from anywhere
python agenthub.py
```

### Menu

```
1. Launch Antigravity CLI (Gemini)
2. Launch Codex CLI
3. Launch OpenCode CLI
4. Launch Cursor CLI
5. Refresh agent status
6. Check agent versions
7. Update agents
8. Settings
9. Exit
```

### Usage & limits`r`n`r`nChoose **Show usage & limits** to see the usage information each installed CLI exposes through supported local commands. OpenCode provides historical token and cost statistics via `opencode stats`; Gemini CLI exposes session statistics interactively with `/stats model`; Cursor `agent status` reports account/authentication status, not quota. AgentHub labels unsupported fields unavailable and does not estimate quota, reset times, plan tier, or rate limits. These provider commands are documented in the [Gemini CLI usage docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/index.md), [OpenCode CLI docs](https://opencode.ai/docs/terminal), and [Cursor CLI authentication docs](https://cursor.com/docs/cli/reference/authentication).`r`n`r`n### Settings Sub-menu

- **View agent details** â€” shows description, install/update commands, and config file locations
- **Add a new agent** â€” interactively add a CLI agent entry
- **Remove an agent** â€” remove an agent from the configuration
- **Open agents.json** â€” edit the configuration file directly

## Configuration

Agents are defined in `agents.json`:

```json
{
  "agents": [
    {
      "name": "Gemini CLI",
      "command": "gemini",
      "description": "Google's AI coding assistant CLI",
      "install_method": "npm install -g @google/gemini-cli",
      "update_method": "npm update -g @google/gemini-cli",
      "config_locations": [
        "%USERPROFILE%\\.gemini"
      ]
    }
  ]
}
```

### Adding a custom agent

Either use **Settings â†’ Add a new agent** from the menu, or add an entry to `agents.json`:

```json
{
  "name": "My Agent",
  "command": "myagent",
  "description": "Description here",
  "install_method": "npm install -g myagent",
  "update_method": "npm update -g myagent",
  "config_locations": ["%USERPROFILE%\\.myagent"]
}
```

## Safety

- **No automatic updates** â€” all updates require explicit confirmation
- **No credential exposure** â€” API keys and tokens are never read or displayed
- **No background services** â€” runs only when you launch it
- **No network calls** â€” only executes local CLI commands

## Requirements

- Python 3.10+
- Windows 11 / PowerShell
- [Rich](https://github.com/Textualize/rich) (installed via `requirements.txt`)

