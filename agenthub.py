"""
AgentHub — The Unified AI Developer CLI Manager
Detects, displays, inspects, and launches AI coding CLI agents on any platform.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Force UTF-8 encoding for standard streams on Windows to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

# ---------------------------------------------------------------------------
# Metadata & Styling Constants
# ---------------------------------------------------------------------------
VERSION = "1.2.0"
APP_NAME = "AgentHub"
CONSOLE = Console()

# Warm terminal aesthetic palette
COLOR_PRIMARY = "#ff6b35"       # Vibrant terracotta / orange
COLOR_SECONDARY = "#f7a072"     # Warm peach / soft amber
COLOR_ACCENT = "#fbbf24"        # Warm gold
COLOR_MUTED = "#a8a29e"         # Stone gray
COLOR_READY = "#10b981"         # Emerald green
COLOR_MISSING = "#f87171"       # Soft coral red
COLOR_CYAN = "#38bdf8"          # Bright sky cyan

# ---------------------------------------------------------------------------
# Config Management
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Agent Catalog (auto-discovery registry)
# ---------------------------------------------------------------------------
# Every entry is probed on PATH during auto-sync. Agents that are installed are
# merged into the user's config automatically and shown in the UI. Agents that
# are not installed are skipped (and offered as install suggestions by doctor).
AGENT_CATALOG: list[dict[str, Any]] = [
    {
        "name": "Claude Code",
        "command": "claude",
        "description": "Anthropic's agentic coding assistant for the terminal",
        "install_method": "npm install -g @anthropic-ai/claude-code",
        "update_method": "npm update -g @anthropic-ai/claude-code",
        "config_locations": [
            "~/.claude",
            "~/.claude/settings.json",
            "~/.claude.json",
        ],
    },
    {
        "name": "Codex CLI",
        "command": "codex",
        "description": "OpenAI's Codex CLI agent for software engineering",
        "install_method": "npm install -g @openai/codex",
        "update_method": "npm update -g @openai/codex",
        "config_locations": [
            "~/.codex",
            "~/.codex/config.json",
        ],
    },
    {
        "name": "Gemini CLI",
        "command": "gemini",
        "description": "Google's open-source terminal AI agent",
        "install_method": "npm install -g @google/gemini-cli",
        "update_method": "npm update -g @google/gemini-cli",
        "config_locations": [
            "~/.gemini",
            "~/.gemini/settings.json",
        ],
    },
    {
        "name": "Antigravity CLI",
        "command": "agy",
        "description": "Google Antigravity's terminal coding agent",
        "install_method": "Install Antigravity from https://antigravity.google",
        "update_method": "agy update",
        "config_locations": [
            "~/.gemini",
            "~/.gemini/settings.json",
        ],
    },
    {
        "name": "OpenCode CLI",
        "command": "opencode",
        "description": "Open-source AI coding CLI tool",
        "install_method": "npm install -g opencode-ai",
        "update_method": "npm update -g opencode-ai",
        "config_locations": [
            "~/.opencode",
            "~/.config/opencode",
        ],
    },
    {
        "name": "Cursor CLI",
        "command": "agent",
        "aliases": ["cursor-agent"],
        "description": "Cursor AI editor CLI interface",
        "install_method": "Install from https://cursor.com (add to PATH via Cursor settings)",
        "update_method": "Update via Cursor application or reinstall from https://cursor.com",
        "config_locations": [
            "~/.cursor",
        ],
    },
    {
        "name": "Aider",
        "command": "aider",
        "description": "AI pair programming in your terminal",
        "install_method": "pip install aider-chat  (or: uv tool install aider-chat)",
        "update_method": "pip install --upgrade aider-chat  (or: uv tool upgrade aider-chat)",
        "config_locations": [
            "~/.aider.conf.yml",
            "~/.aider",
        ],
    },
    {
        "name": "Goose",
        "command": "goose",
        "description": "Block's open-source, local-first AI agent",
        "install_method": "See https://block.github.io/goose/docs/getting-started/installation",
        "update_method": "goose update",
        "config_locations": [
            "~/.config/goose",
        ],
    },
    {
        "name": "Qwen Code",
        "command": "qwen",
        "description": "Alibaba's Qwen coding agent CLI",
        "install_method": "npm install -g @qwen-code/qwen-code",
        "update_method": "npm update -g @qwen-code/qwen-code",
        "config_locations": [
            "~/.qwen",
        ],
    },
    {
        "name": "Crush",
        "command": "crush",
        "description": "Charm's glamorous terminal AI coding agent",
        "install_method": "npm install -g @charmland/crush",
        "update_method": "npm update -g @charmland/crush",
        "config_locations": [
            "~/.config/crush",
        ],
    },
    {
        "name": "Amp",
        "command": "amp",
        "description": "Sourcegraph Amp coding agent",
        "install_method": "npm install -g @sourcegraph/amp",
        "update_method": "npm update -g @sourcegraph/amp",
        "config_locations": [
            "~/.config/amp",
        ],
    },
    {
        "name": "Factory Droid",
        "command": "droid",
        "description": "Factory's software engineering agent CLI",
        "install_method": "See https://docs.factory.ai",
        "update_method": "droid update",
        "config_locations": [
            "~/.factory",
        ],
    },
    {
        "name": "OpenHands",
        "command": "openhands",
        "description": "Open-source autonomous software engineering agent",
        "install_method": "uv tool install openhands  (or: pip install openhands-ai)",
        "update_method": "uv tool upgrade openhands",
        "config_locations": [
            "~/.openhands",
        ],
    },
    {
        "name": "GitHub Copilot CLI",
        "command": "copilot",
        "description": "GitHub Copilot's terminal agent",
        "install_method": "npm install -g @github/copilot",
        "update_method": "npm update -g @github/copilot",
        "config_locations": [
            "~/.config/github-copilot",
        ],
    },
    {
        "name": "Continue CLI",
        "command": "cn",
        "description": "Continue's terminal coding agent",
        "install_method": "npm install -g @continuedev/cli",
        "update_method": "npm update -g @continuedev/cli",
        "config_locations": [
            "~/.continue",
        ],
    },
    {
        "name": "Codebuff",
        "command": "codebuff",
        "description": "Codebuff terminal coding agent",
        "install_method": "npm install -g codebuff",
        "update_method": "npm update -g codebuff",
        "config_locations": [
            "~/.config/codebuff",
        ],
    },
    {
        "name": "Kimi CLI",
        "command": "kimi",
        "description": "Moonshot Kimi's terminal coding agent",
        "install_method": "uv tool install kimi-cli",
        "update_method": "uv tool upgrade kimi-cli",
        "config_locations": [
            "~/.kimi",
        ],
    },
]


def default_config() -> dict[str, Any]:
    """Return a fresh starter config (empty — auto-sync fills it on startup)."""
    return {"agents": []}


def get_config_path() -> Path:
    """
    Resolve the active configuration path:
      1. AGENTHUB_CONFIG environment variable (if set).
      2. Local ./agents.json (if present in current directory).
      3. User home config ~/.agenthub/agents.json.
      4. Bundled package agents.json fallback.
    """
    env_cfg = os.environ.get("AGENTHUB_CONFIG")
    if env_cfg:
        return Path(env_cfg).resolve()

    local_cfg = Path.cwd() / "agents.json"
    if local_cfg.exists():
        return local_cfg

    global_dir = Path.home() / ".agenthub"
    global_cfg = global_dir / "agents.json"
    if global_cfg.exists():
        return global_cfg

    # Check bundled config file
    bundled_cfg = Path(__file__).resolve().parent / "agents.json"

    # Seed global directory automatically so additions/removals persist cleanly
    try:
        global_dir.mkdir(parents=True, exist_ok=True)
        if bundled_cfg.exists():
            shutil.copy2(bundled_cfg, global_cfg)
        else:
            with open(global_cfg, "w", encoding="utf-8") as f:
                json.dump(default_config(), f, indent=2)
        return global_cfg
    except Exception:
        if bundled_cfg.exists():
            return bundled_cfg
        return global_cfg


def load_config() -> tuple[dict[str, Any], Path]:
    """Load configuration dictionary and return (config, path)."""
    cfg_path = get_config_path()
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f), cfg_path
        except Exception as e:
            CONSOLE.print(f"[yellow]Warning:[/yellow] Could not read {cfg_path} ({e}). Using defaults.")
    return default_config(), cfg_path


def save_config(
    config: dict[str, Any],
    target_path: Path | None = None,
    *,
    quiet: bool = False,
) -> Path:
    """Save configuration dictionary to target path."""
    dest = target_path or get_config_path()
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        if not quiet:
            CONSOLE.print(f"[{COLOR_READY}]✓ Configuration saved to {dest}[/{COLOR_READY}]")
    except Exception as e:
        CONSOLE.print(f"[{COLOR_MISSING}]Failed to save config to {dest}: {e}[/{COLOR_MISSING}]")
    return dest

# ---------------------------------------------------------------------------
# Agent Detection & Environment Inspection
# ---------------------------------------------------------------------------

def find_executable(command: str) -> str | None:
    """Return the absolute path of the command if available on PATH."""
    return shutil.which(command)


def get_version(command: str) -> str:
    """Try common version flags to extract clean CLI version string."""
    for flag in ("--version", "-v", "version", "-V"):
        try:
            res = subprocess.run(
                f"{command} {flag}",
                capture_output=True,
                text=True,
                timeout=8,
                shell=True,
            )
            combined = ((res.stdout or "") + "\n" + (res.stderr or "")).strip()
            if not combined:
                continue

            lower = combined.lower()
            if "traceback" in lower or "platformerror" in lower or "eperm" in lower:
                continue

            for raw_line in combined.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("at ") or line.startswith("(") or line.startswith("{"):
                    continue
                if "warning" in line.lower() or "error" in line.lower():
                    continue
                if re.search(r"\d+\.\d+", line):
                    # Clean up long version strings
                    if len(line) > 36:
                        line = line[:33] + "..."
                    return line
        except Exception:
            continue
    return "installed"


def expand_path(path_str: str) -> str:
    """Expand environment variables and user home in path."""
    return os.path.expanduser(os.path.expandvars(path_str))


def detect_agents(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Enrich agent configurations with live detection status."""
    enriched = []
    for entry in config.get("agents", []):
        cmd = entry.get("command", "")
        exe = find_executable(cmd)
        installed = exe is not None
        version = get_version(cmd) if installed else "—"
        enriched.append({
            **entry,
            "installed": installed,
            "exe_path": exe or "not found",
            "version": version,
        })
    return enriched

# ---------------------------------------------------------------------------
# Auto-Discovery & Config Sync
# ---------------------------------------------------------------------------

def common_bin_dirs() -> list[Path]:
    """Return well-known CLI install directories that may be missing from PATH."""
    home = Path.home()
    candidates: list[Path] = []

    # npm/pnpm configured prefixes (npm sets these env vars)
    for var in ("NPM_CONFIG_PREFIX", "npm_config_prefix"):
        prefix = os.environ.get(var)
        if prefix:
            candidates.append(Path(prefix))
            candidates.append(Path(prefix) / "bin")

    if os.name == "nt":
        appdata = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
        local = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
        candidates += [
            appdata / "npm",
            local / "pnpm",
            local / "Volta" / "bin",
            home / ".bun" / "bin",
            home / ".local" / "bin",
            home / ".cargo" / "bin",
        ]
    else:
        candidates += [
            home / ".local" / "bin",
            home / ".npm-global" / "bin",
            home / ".bun" / "bin",
            home / ".cargo" / "bin",
            home / ".volta" / "bin",
            home / ".local" / "share" / "pnpm",
            Path("/opt/homebrew/bin"),
            Path("/usr/local/bin"),
        ]

    seen: set[str] = set()
    result: list[Path] = []
    for candidate in candidates:
        try:
            expanded = candidate.expanduser()
            key = os.path.normcase(os.path.abspath(str(expanded)))
        except Exception:
            continue
        if key in seen:
            continue
        seen.add(key)
        if expanded.is_dir():
            result.append(expanded)
    return result


def ensure_search_path() -> list[str]:
    """
    Append known CLI install dirs to PATH for this process.
    Makes detection *and* launching work for tools installed outside PATH
    (npm global, pipx/uv, bun, cargo, Volta, Homebrew).
    """
    added: list[str] = []
    parts = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    known = {os.path.normcase(os.path.abspath(p)) for p in parts}

    for directory in common_bin_dirs():
        key = os.path.normcase(os.path.abspath(str(directory)))
        if key in known:
            continue
        known.add(key)
        parts.append(str(directory))
        added.append(str(directory))

    if added:
        os.environ["PATH"] = os.pathsep.join(parts)
    return added


def discover_agents(
    catalog: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Probe the catalog for installed agents.

    Returns (found, missing). `found` entries carry the resolved command name,
    which may be an alias when the primary command is not installed.
    """
    entries = catalog if catalog is not None else AGENT_CATALOG
    found: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for entry in entries:
        item = {
            key: (list(value) if isinstance(value, list) else value)
            for key, value in entry.items()
        }
        names = [item.get("command", "")] + list(item.get("aliases") or [])
        resolved = next((name for name in names if name and find_executable(name)), None)
        if resolved:
            # Keep the catalog's primary name as an alias so an existing config
            # entry using it is recognised instead of duplicated.
            primary = str(item.get("command", ""))
            aliases = list(item.get("aliases") or [])
            if primary and primary.lower() != resolved.lower() and primary not in aliases:
                aliases.append(primary)
            if aliases:
                item["aliases"] = aliases
            item["command"] = resolved
            found.append(item)
        else:
            missing.append(item)

    return found, missing


def _unique_agent_name(agents: list[dict[str, Any]], name: str, command: str) -> str:
    """Avoid duplicate display names when two commands map to the same tool name."""
    used = {str(a.get("name", "")).strip().lower() for a in agents}
    if name.strip().lower() not in used:
        return name
    candidate = f"{name} ({command})"
    suffix = 2
    while candidate.lower() in used:
        candidate = f"{name} ({command} #{suffix})"
        suffix += 1
    return candidate


def merge_discovered_agents(
    config: dict[str, Any],
    discovered: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str], list[str]]:
    """
    Merge discovered catalog agents into an existing config.

    - Existing entries are never overwritten; only empty metadata is filled in.
    - New commands are appended and tagged with "source": "catalog".
    - Alias matches (e.g. `cursor-agent` vs `agent`) reuse the existing entry.

    Returns (config, added_names, enriched_names).
    """
    agents: list[dict[str, Any]] = config.setdefault("agents", [])
    index = {str(a.get("command", "")).strip().lower(): a for a in agents}
    added: list[str] = []
    enriched: list[str] = []

    for entry in discovered:
        command = str(entry.get("command", "")).strip()
        if not command:
            continue

        candidates = [command.lower()]
        candidates += [str(a).strip().lower() for a in entry.get("aliases") or [] if a]
        existing = next((index[c] for c in candidates if c in index), None)

        if existing is not None:
            changed = False
            for key in ("description", "install_method", "update_method"):
                if not existing.get(key):
                    existing[key] = entry.get(key, "")
                    changed = True
            if not existing.get("config_locations"):
                existing["config_locations"] = list(entry.get("config_locations") or [])
                changed = True

            # The stored command may be stale (e.g. renamed binary); prefer the
            # one that actually resolves on this machine.
            stored = str(existing.get("command", "")).strip()
            if stored.lower() != command.lower() and not find_executable(stored):
                index.pop(stored.lower(), None)
                existing["command"] = command
                index[command.lower()] = existing
                changed = True

            if changed:
                enriched.append(str(existing.get("name", command)))
            continue

        new_entry = {
            "name": _unique_agent_name(agents, str(entry.get("name") or command), command),
            "command": command,
            "description": entry.get("description", ""),
            "install_method": entry.get("install_method", ""),
            "update_method": entry.get("update_method", ""),
            "config_locations": list(entry.get("config_locations") or []),
            "source": "catalog",
        }
        agents.append(new_entry)
        index[command.lower()] = new_entry
        added.append(new_entry["name"])

    return config, added, enriched


def sync_config(
    config: dict[str, Any],
    config_path: Path | None = None,
    *,
    announce: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Discover installed agents and persist any changes. Returns (config, added)."""
    ensure_search_path()
    found, _missing = discover_agents()
    config, added, enriched = merge_discovered_agents(config, found)

    if added or enriched:
        if announce:
            if added:
                names = ", ".join(f"[bold white]{n}[/bold white]" for n in added)
                CONSOLE.print(
                    f"[{COLOR_READY}]✓ Auto-synced {len(added)} new agent(s):[/{COLOR_READY}] {names}"
                )
            if enriched:
                CONSOLE.print(
                    f"[{COLOR_MUTED}]Filled in metadata for: {', '.join(enriched)}[/{COLOR_MUTED}]"
                )
        save_config(config, config_path, quiet=True)

    return config, added

# ---------------------------------------------------------------------------
# Header & UI Components
# ---------------------------------------------------------------------------

def render_header(agents: list[dict[str, Any]]) -> Panel:
    """Slim one-line header: brand, version, ready count."""
    installed = sum(1 for a in agents if a["installed"])
    total = len(agents)

    if installed == total and total > 0:
        ready_style = COLOR_READY
    elif installed > 0:
        ready_style = COLOR_ACCENT
    else:
        ready_style = COLOR_MISSING

    line = Text()
    line.append(" ✳ AgentHub ", style=f"bold {COLOR_PRIMARY}")
    line.append(f"v{VERSION}", style=COLOR_MUTED)
    line.append("  ·  ", style=COLOR_MUTED)
    if total == 0:
        line.append("no agents detected", style=f"bold {COLOR_MUTED}")
    else:
        line.append(f"{installed}/{total} ready", style=f"bold {ready_style}")

    return Panel(
        line,
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY,
        padding=(0, 1),
    )


def show_banner(agents: list[dict[str, Any]] | None = None, config_path: Path | None = None) -> None:
    """Print the slim header banner."""
    if agents is None:
        cfg, _ = load_config()
        agents = detect_agents(cfg)
    CONSOLE.print(render_header(agents))


def show_status_table(agents: list[dict[str, Any]]) -> None:
    """Print a clean status table."""
    if not agents:
        CONSOLE.print(
            f"[{COLOR_MUTED}]No agents configured yet. Run [bold]agenthub sync[/bold] "
            f"to scan for installed AI CLIs, or [bold]agenthub add[/bold] to add one manually.[/{COLOR_MUTED}]"
        )
        return

    table = Table(
        title="[bold white]Agents[/bold white]",
        box=box.SIMPLE_HEAD,
        header_style=f"bold {COLOR_PRIMARY}",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("#", style=COLOR_MUTED, width=3, justify="right")
    table.add_column("Agent", min_width=16, style="bold white")
    table.add_column("Command", min_width=10, style=COLOR_CYAN)
    table.add_column("Status", min_width=10, justify="left")
    table.add_column("Version", min_width=12, style=COLOR_MUTED)

    for i, a in enumerate(agents, 1):
        if a["installed"]:
            status = f"[bold {COLOR_READY}]● ready[/bold {COLOR_READY}]"
        else:
            status = f"[{COLOR_MISSING}]○ missing[/{COLOR_MISSING}]"
        table.add_row(
            str(i),
            a["name"],
            a["command"],
            status,
            a["version"] if a["installed"] else "—",
        )

    CONSOLE.print(table)

# ---------------------------------------------------------------------------
# Keyboard Navigation
# ---------------------------------------------------------------------------

def read_navigation_key() -> str:
    """Read a single navigation key with cross-platform support."""
    if os.name == "nt":
        import msvcrt
        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(code, "")
        if key in ("\r", "\n"):
            return "enter"
        if key == "\x1b":
            return "escape"
        return key.lower()

    # POSIX fallback
    import termios
    import tty
    fd = sys.stdin.fileno()
    prev = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(seq, "escape")
        if ch in ("\r", "\n"):
            return "enter"
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, prev)

# ---------------------------------------------------------------------------
# Interactive Menu Selection
# ---------------------------------------------------------------------------

def _menu_row(
    label: str,
    shortcut: str,
    selected: bool,
    *,
    ready: bool | None = None,
    version: str = "",
) -> Text:
    """One menu row — selected gets a solid bar; others stay full brightness (no dim)."""
    row = Text(no_wrap=True)
    key = f" {shortcut} " if shortcut else "   "
    name = f" {label:<24}"

    if selected:
        row.append("❯", style=f"bold {COLOR_PRIMARY}")
        row.append(key, style=f"bold white on {COLOR_PRIMARY}")
        row.append(name, style=f"bold white on {COLOR_PRIMARY}")
        if ready is True:
            row.append(f" ● {version}", style=f"bold white on {COLOR_PRIMARY}")
        elif ready is False:
            row.append(" ○ missing", style=f"bold white on {COLOR_PRIMARY}")
    else:
        row.append(" ")
        row.append(key, style=COLOR_MUTED)
        row.append(name, style="white")
        if ready is True:
            row.append(" ● ", style=COLOR_READY)
            row.append(version, style=COLOR_MUTED)
        elif ready is False:
            row.append(" ○ missing", style=COLOR_MISSING)
    return row


def build_menu_view(
    agents: list[dict[str, Any]],
    items: list[tuple[str, str, Any, str]],
    selected: int,
) -> Group:
    """Build the full interactive menu renderable."""
    agent_count = len(agents)
    lines: list[Text] = [Text("Agents", style=f"bold {COLOR_PRIMARY}")]

    if agent_count == 0:
        lines.append(Text(
            "  No agents detected. Press r to scan, a to add manually, d for doctor.",
            style=COLOR_MUTED,
        ))

    for i, (label, kind, agent_idx, shortcut) in enumerate(items):
        if i == agent_count:
            lines.append(Text(""))
            lines.append(Text("Actions", style=f"bold {COLOR_PRIMARY}"))

        if kind == "launch":
            agent = agents[agent_idx]
            ver = str(agent["version"])
            if len(ver) > 18:
                ver = ver[:17] + "…"
            lines.append(
                _menu_row(
                    label,
                    shortcut,
                    i == selected,
                    ready=bool(agent["installed"]),
                    version=ver,
                )
            )
        else:
            lines.append(_menu_row(label, shortcut, i == selected))

    menu_body = Text("\n").join(lines)
    hints = (
        f"[{COLOR_MUTED}]↑↓ move · Enter open · "
        f"1-{min(9, max(agent_count, 1))} launch · "
        f"q quit[/{COLOR_MUTED}]"
    )

    return Group(
        render_header(agents),
        Text(""),
        Panel(
            menu_body,
            box=box.ROUNDED,
            border_style=COLOR_SECONDARY,
            padding=(1, 1),
            subtitle=hints,
            subtitle_align="left",
        ),
    )


def choose_action(agents: list[dict[str, Any]], config_path: Path) -> str:
    """
    Interactive menu with arrow/vim navigation,
    direct number jump (1-9), and single-letter hotkeys.
    Uses Live updates so navigation does not flash/dim the screen.
    """
    items: list[tuple[str, str, Any, str]] = []

    for i, a in enumerate(agents, 1):
        shortcut = str(i) if i < 10 else ""
        items.append((f"{a['name']}  ({a['command']})", "launch", i - 1, shortcut))

    items.append(("Sync & refresh", "refresh", None, "r"))
    items.append(("Doctor", "doctor", None, "d"))
    items.append(("Update", "update", None, "u"))
    items.append(("Add agent", "add", None, "a"))
    items.append(("Settings", "settings", None, "s"))
    items.append(("Quit", "exit", None, "q"))

    selected = 0
    total = len(items)

    CONSOLE.clear()
    with Live(
        build_menu_view(agents, items, selected),
        console=CONSOLE,
        auto_refresh=False,
        transient=True,
    ) as live:
        while True:
            key = read_navigation_key()

            if key in ("up", "k"):
                selected = (selected - 1) % total
                live.update(build_menu_view(agents, items, selected), refresh=True)
            elif key in ("down", "j"):
                selected = (selected + 1) % total
                live.update(build_menu_view(agents, items, selected), refresh=True)
            elif key == "enter":
                _, kind, idx, _ = items[selected]
                return f"{kind}:{idx}" if idx is not None else kind
            elif key in ("q", "escape"):
                return "exit"
            else:
                for _, kind, idx, shortcut in items:
                    if shortcut and key == shortcut.lower():
                        return f"{kind}:{idx}" if idx is not None else kind

# ---------------------------------------------------------------------------
# Agent Execution & Diagnostics
# ---------------------------------------------------------------------------

def launch_agent(agent: dict[str, Any], interactive: bool = False) -> None:
    """Launch an agent in the current working directory."""
    CONSOLE.clear()
    if not agent["installed"]:
        CONSOLE.print(Panel(
            f"[bold {COLOR_MISSING}]Agent '{agent['name']}' is not installed or not found on PATH.[/bold {COLOR_MISSING}]\n\n"
            f"[bold white]Required command:[/bold white] [cyan]`{agent['command']}`[/cyan]\n"
            f"[bold white]Installation instructions:[/bold white]\n"
            f"  [bold yellow]{agent.get('install_method', 'See tool documentation')}[/bold yellow]\n",
            title=f"[bold {COLOR_MISSING}]Missing Agent[/bold {COLOR_MISSING}]",
            box=box.ROUNDED,
            border_style=COLOR_MISSING,
        ))
        if interactive:
            Prompt.ask("\nPress Enter to return to menu", default="")
        return

    CONSOLE.print(Panel(
        f"[bold {COLOR_PRIMARY}]Starting {agent['name']}...[/bold {COLOR_PRIMARY}]\n"
        f"Command:  [bold cyan]{agent['command']}[/bold cyan]\n"
        f"Location: [dim]{agent['exe_path']}[/dim]\n"
        f"Workdir:  [dim]{os.getcwd()}[/dim]\n\n"
        f"[dim]Control is handed to {agent['name']}. When done, you will return to AgentHub.[/dim]",
        title=f"[bold {COLOR_READY}]● Launching Agent[/bold {COLOR_READY}]",
        box=box.ROUNDED,
        border_style=COLOR_READY,
    ))

    try:
        subprocess.run(agent["command"], cwd=os.getcwd(), shell=True)
    except KeyboardInterrupt:
        CONSOLE.print(f"\n[yellow]{agent['name']} session ended by user.[/yellow]")
    except Exception as e:
        CONSOLE.print(f"\n[{COLOR_MISSING}]Error running {agent['name']}: {e}[/{COLOR_MISSING}]")

    CONSOLE.print(f"\n[dim]Returned from {agent['name']}.[/dim]")
    if interactive:
        Prompt.ask("\nPress Enter to continue", default="")


def run_doctor(agents: list[dict[str, Any]], config_path: Path, interactive: bool = False) -> None:
    """Perform diagnostic health check on all agents and the environment."""
    CONSOLE.clear()
    CONSOLE.print(Panel(
        f"[bold {COLOR_PRIMARY}]AgentHub Doctor & Health Diagnostics[/bold {COLOR_PRIMARY}]\n"
        f"Checking environment, paths, CLI agents, and configurations.",
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY
    ))

    # Environment
    env_table = Table(box=box.SIMPLE, show_header=False)
    env_table.add_column("Key", style="bold white", width=20)
    env_table.add_column("Value", style=COLOR_MUTED)

    env_table.add_row("AgentHub Version", f"v{VERSION}")
    env_table.add_row("Python Executable", sys.executable)
    env_table.add_row("Python Version", f"{platform.python_version()} ({platform.architecture()[0]})")
    env_table.add_row("Operating System", f"{platform.system()} {platform.release()} ({platform.version()})")
    env_table.add_row("Working Directory", os.getcwd())
    env_table.add_row("Active Config Path", str(config_path))
    env_table.add_row("Config File Exists", "Yes" if config_path.exists() else "No (using in-memory defaults)")
    env_table.add_row("Known Agent Catalog", f"{len(AGENT_CATALOG)} agents")
    search_dirs = common_bin_dirs()
    env_table.add_row("Extra Discovery Dirs", str(len(search_dirs)) if search_dirs else "None found")
    if search_dirs:
        env_table.add_row("", ", ".join(str(d) for d in search_dirs[:4]) + (" …" if len(search_dirs) > 4 else ""))

    CONSOLE.print(Panel(env_table, title="[bold white]Environment Summary[/bold white]", box=box.ROUNDED))

    # Agents Check
    agent_table = Table(box=box.ROUNDED, header_style=f"bold {COLOR_PRIMARY}")
    agent_table.add_column("Agent", style="bold white")
    agent_table.add_column("Command")
    agent_table.add_column("PATH Status")
    agent_table.add_column("Version")
    agent_table.add_column("Config Locations Found")

    for a in agents:
        status = f"[{COLOR_READY}]✓ Found[/{COLOR_READY}]" if a["installed"] else f"[{COLOR_MISSING}]✗ Missing[/{COLOR_MISSING}]"
        
        cfg_locs = a.get("config_locations", [])
        found_locs = 0
        total_locs = len(cfg_locs)
        for loc in cfg_locs:
            if os.path.exists(expand_path(loc)):
                found_locs += 1
        cfg_summary = f"{found_locs}/{total_locs} detected" if total_locs > 0 else "None specified"

        agent_table.add_row(
            a["name"],
            f"`{a['command']}`",
            status,
            a["version"],
            cfg_summary
        )

    CONSOLE.print(agent_table)

    # Catalog agents that are known but not installed (auto-sync candidates)
    _found, missing = discover_agents()
    if missing:
        catalog_table = Table(
            box=box.SIMPLE_HEAD,
            header_style=f"bold {COLOR_PRIMARY}",
            title="[bold white]Catalog — not installed[/bold white]",
            title_justify="left",
        )
        catalog_table.add_column("Agent", style="bold white")
        catalog_table.add_column("Command", style=COLOR_CYAN)
        catalog_table.add_column("Install", style=COLOR_MUTED)
        for entry in missing:
            catalog_table.add_row(
                entry.get("name", ""),
                entry.get("command", ""),
                entry.get("install_method", ""),
            )
        CONSOLE.print(catalog_table)
        CONSOLE.print(
            f"[{COLOR_MUTED}]Install any of these and AgentHub will pick them up on the next sync.[/{COLOR_MUTED}]"
        )

    if interactive:
        Prompt.ask("\nPress Enter to return to menu", default="")


def update_agents_wizard(agents: list[dict[str, Any]]) -> None:
    """Interactive updater for installed agents."""
    CONSOLE.clear()
    CONSOLE.print(Panel(
        f"[bold {COLOR_PRIMARY}]AgentHub Updater[/bold {COLOR_PRIMARY}]\n"
        f"Safely inspect and run updates for installed agents. No command runs without confirmation.",
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY
    ))

    installed = [a for a in agents if a["installed"]]
    if not installed:
        CONSOLE.print(f"[{COLOR_MISSING}]No agents are currently installed to update.[/{COLOR_MISSING}]")
        Prompt.ask("\nPress Enter to return", default="")
        return

    for a in installed:
        method = a.get("update_method", "")
        CONSOLE.print(f"\n[bold white]{a['name']}[/bold white] (Command: [cyan]{a['command']}[/cyan])")
        CONSOLE.print(f"  Current Version: [{COLOR_ACCENT}]{a['version']}[/{COLOR_ACCENT}]")
        CONSOLE.print(f"  Binary Location: [dim]{a['exe_path']}[/dim]")

        if not method:
            CONSOLE.print(f"  [dim]No update command configured. Check provider website.[/dim]")
            continue

        CONSOLE.print(f"  Update Command:  [bold yellow]{method}[/bold yellow]")
        if Confirm.ask("  Run this update now?", default=False):
            CONSOLE.print(f"  [yellow]Executing: {method}...[/yellow]")
            try:
                subprocess.run(method, shell=True, cwd=os.getcwd())
                CONSOLE.print(f"  [{COLOR_READY}]✓ Update completed.[/{COLOR_READY}]")
            except Exception as e:
                CONSOLE.print(f"  [{COLOR_MISSING}]Update error: {e}[/{COLOR_MISSING}]")
        else:
            CONSOLE.print("  [dim]Skipped.[/dim]")

    Prompt.ask("\nPress Enter to return to menu", default="")

# ---------------------------------------------------------------------------
# Settings & Configuration Sub-Menu
# ---------------------------------------------------------------------------

def settings_menu(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Settings and agent configuration editor."""
    while True:
        CONSOLE.clear()
        CONSOLE.print(Panel(
            f"[bold {COLOR_PRIMARY}]AgentHub Settings & Configuration[/bold {COLOR_PRIMARY}]\n"
            f"Active config file: [bold cyan]{config_path}[/bold cyan]",
            box=box.ROUNDED,
            border_style=COLOR_PRIMARY
        ))

        CONSOLE.print("  [bold white]1.[/bold white] View agent details and configuration locations")
        CONSOLE.print("  [bold white]2.[/bold white] Add a new CLI agent")
        CONSOLE.print("  [bold white]3.[/bold white] Remove an agent")
        CONSOLE.print("  [bold white]4.[/bold white] Open config file in default editor")
        CONSOLE.print("  [bold white]5.[/bold white] Reset configuration to default")
        CONSOLE.print("  [bold white]6.[/bold white] Show catalog agents not installed")
        CONSOLE.print("  [bold white]7.[/bold white] Back to main menu")

        choice = Prompt.ask("\n  Select option", choices=["1", "2", "3", "4", "5", "6", "7"], default="7")

        if choice == "1":
            show_agent_details(detect_agents(config))
        elif choice == "2":
            config = add_agent_wizard(config, config_path)
        elif choice == "3":
            config = remove_agent_wizard(config, config_path)
        elif choice == "4":
            open_config_file(config_path)
        elif choice == "5":
            if Confirm.ask("  Are you sure you want to reset config to default?", default=False):
                config = default_config()
                save_config(config, config_path)
                Prompt.ask("\n  Config reset. Press Enter", default="")
        elif choice == "6":
            show_catalog_agents()
        elif choice == "7":
            break

    return config


def show_agent_details(agents: list[dict[str, Any]]) -> None:
    """Detailed card for every agent."""
    CONSOLE.clear()
    CONSOLE.print(f"[bold {COLOR_PRIMARY}]Configured Agent Specifications[/bold {COLOR_PRIMARY}]\n")
    for a in agents:
        status = f"[{COLOR_READY}]installed[/{COLOR_READY}]" if a["installed"] else f"[{COLOR_MISSING}]missing[/{COLOR_MISSING}]"
        lines = [
            f"[bold white]Command:[/]     [cyan]{a['command']}[/cyan]",
            f"[bold white]Status:[/]      {status}",
            f"[bold white]Version:[/]     {a['version']}",
            f"[bold white]Path:[/]        {a['exe_path']}",
            f"[bold white]Description:[/] {a.get('description', '—')}",
            f"[bold white]Install:[/]     [yellow]{a.get('install_method', '—')}[/yellow]",
            f"[bold white]Update:[/]      [yellow]{a.get('update_method', '—')}[/yellow]",
        ]
        cfg_locs = a.get("config_locations", [])
        if cfg_locs:
            lines.append("[bold white]Configuration paths:[/]")
            for loc in cfg_locs:
                exp = expand_path(loc)
                icon = "✓" if os.path.exists(exp) else "✗"
                lines.append(f"  {icon} {exp}")

        CONSOLE.print(Panel(
            "\n".join(lines),
            title=f"[bold white]{a['name']}[/bold white]",
            box=box.ROUNDED,
            border_style=COLOR_SECONDARY,
            padding=(0, 2)
        ))
    Prompt.ask("\nPress Enter to return", default="")


def show_catalog_agents() -> None:
    """List catalog agents that are not currently installed, with install commands."""
    CONSOLE.clear()
    CONSOLE.print(f"[bold {COLOR_PRIMARY}]Agent Catalog — Available to Install[/bold {COLOR_PRIMARY}]\n")

    found, missing = discover_agents()
    CONSOLE.print(f"[{COLOR_MUTED}]{len(found)} of {len(found) + len(missing)} catalog agents detected on this machine.[/{COLOR_MUTED}]\n")

    if not missing:
        CONSOLE.print(f"[{COLOR_READY}]✓ Every catalog agent is already installed.[/{COLOR_READY}]")
    else:
        table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {COLOR_PRIMARY}")
        table.add_column("Agent", style="bold white")
        table.add_column("Command", style=COLOR_CYAN)
        table.add_column("Description", style=COLOR_MUTED)
        table.add_column("Install", style=COLOR_ACCENT)
        for entry in missing:
            table.add_row(
                entry.get("name", ""),
                entry.get("command", ""),
                entry.get("description", ""),
                entry.get("install_method", ""),
            )
        CONSOLE.print(table)
        CONSOLE.print(
            f"\n[{COLOR_MUTED}]Install one, then run [bold]agenthub sync[/bold] (or press r in the menu) "
            f"to pick it up automatically.[/{COLOR_MUTED}]"
        )

    Prompt.ask("\nPress Enter to return", default="")


def add_agent_wizard(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Interactive wizard to register a new agent."""
    CONSOLE.print(f"\n[bold {COLOR_PRIMARY}]Register New AI CLI Agent[/bold {COLOR_PRIMARY}]\n")
    name = Prompt.ask("  Agent display name (e.g. Aider)")
    command = Prompt.ask("  CLI command (e.g. aider)")
    description = Prompt.ask("  Description", default="AI pair programmer in the terminal")
    install_method = Prompt.ask("  Install command", default=f"pip install {command}")
    update_method = Prompt.ask("  Update command", default=f"pip install --upgrade {command}")
    cfg_loc = Prompt.ask("  Config location path (optional)", default="")

    new_agent = {
        "name": name,
        "command": command,
        "description": description,
        "install_method": install_method,
        "update_method": update_method,
        "config_locations": [cfg_loc] if cfg_loc else [],
        "source": "user",
    }

    config.setdefault("agents", []).append(new_agent)
    save_config(config, config_path)
    CONSOLE.print(f"[{COLOR_READY}]✓ Added {name} successfully![/{COLOR_READY}]")
    Prompt.ask("\nPress Enter to continue", default="")
    return config


def remove_agent_wizard(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Interactive removal of an agent."""
    agents = config.get("agents", [])
    if not agents:
        CONSOLE.print("[dim]No agents to remove.[/dim]")
        Prompt.ask("\nPress Enter to return", default="")
        return config

    CONSOLE.print(f"\n[bold {COLOR_PRIMARY}]Remove Agent[/bold {COLOR_PRIMARY}]\n")
    for i, a in enumerate(agents, 1):
        CONSOLE.print(f"  [bold white]{i}.[/bold white] {a['name']} (`{a['command']}`)")

    raw = Prompt.ask("\nEnter number of agent to remove (0 to cancel)", default="0")
    try:
        idx = int(raw)
        if 1 <= idx <= len(agents):
            target = agents[idx - 1]
            if Confirm.ask(f"Remove [bold]{target['name']}[/bold]?", default=False):
                agents.pop(idx - 1)
                save_config(config, config_path)
                CONSOLE.print(f"[{COLOR_READY}]✓ Removed {target['name']}[/{COLOR_READY}]")
            else:
                CONSOLE.print("[dim]Cancelled.[/dim]")
    except ValueError:
        pass
    Prompt.ask("\nPress Enter to continue", default="")
    return config


def open_config_file(config_path: Path) -> None:
    """Open config file in the user's default system editor."""
    try:
        if sys.platform == "win32":
            os.startfile(str(config_path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(config_path)])
        else:
            subprocess.run(["xdg-open", str(config_path)])
        CONSOLE.print(f"[{COLOR_READY}]Opened {config_path}[/{COLOR_READY}]")
    except Exception as e:
        CONSOLE.print(f"[dim]Please open manually: {config_path} ({e})[/dim]")
    Prompt.ask("\nPress Enter to continue", default="")

# ---------------------------------------------------------------------------
# CLI Argument Dispatcher
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct command line arguments parser."""
    parser = argparse.ArgumentParser(
        prog="agenthub",
        description="AgentHub — The Unified AI Developer CLI Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agenthub                 # Open interactive AgentHub dashboard (auto-syncs)
  agenthub list            # Print status summary table of all agents
  agenthub sync            # Scan for installed AI CLIs and register new ones
  agenthub launch agy      # Directly launch Antigravity CLI (agy)
  agenthub launch claude   # Directly launch Claude Code
  agenthub doctor          # Run environment and PATH diagnostics
  agenthub update          # Check and update installed agents
  agenthub add             # Add a new CLI agent interactively
  agenthub config --path   # Display active configuration path
"""
    )
    parser.add_argument("-v", "--version", action="version", version=f"AgentHub v{VERSION}")
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Skip auto-discovery of installed agents for this run",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # list
    subparsers.add_parser("list", aliases=["ls"], help="List all configured agents and their status")

    # sync
    subparsers.add_parser("sync", aliases=["discover"], help="Scan for installed AI CLIs and add new ones")

    # launch
    p_launch = subparsers.add_parser("launch", aliases=["run"], help="Launch a specific agent directly")
    p_launch.add_argument("agent", help="Agent command or name or number to launch (e.g. agy, codex, 1)")

    # doctor
    subparsers.add_parser("doctor", aliases=["check"], help="Run diagnostics on environment, PATH, and agents")

    # update
    p_update = subparsers.add_parser("update", help="Update installed CLI agents")
    p_update.add_argument("agent", nargs="?", help="Optional specific agent command or name to update")

    # add
    subparsers.add_parser("add", help="Add a new CLI agent configuration")

    # config
    p_cfg = subparsers.add_parser("config", help="Inspect or edit configuration")
    p_cfg.add_argument("--path", action="store_true", help="Print active configuration file path")
    p_cfg.add_argument("--open", action="store_true", help="Open configuration file in default editor")

    return parser


def main() -> None:
    """Entry point for both direct execution and console script `agenthub`."""
    parser = build_parser()
    args, unknown = parser.parse_known_args()

    ensure_search_path()
    config, config_path = load_config()

    # Auto-sync: discover installed agents and persist them before anything else.
    if not args.no_sync and args.subcommand not in ("config", "sync", "discover"):
        config, _added = sync_config(config, config_path, announce=False)

    agents = detect_agents(config)

    # Subcommand dispatch
    if args.subcommand in ("list", "ls"):
        CONSOLE.print(render_header(agents))
        CONSOLE.print()
        show_status_table(agents)
        return

    if args.subcommand in ("sync", "discover"):
        config, added = sync_config(config, config_path, announce=True)
        agents = detect_agents(config)
        CONSOLE.print()
        CONSOLE.print(render_header(agents))
        CONSOLE.print()
        show_status_table(agents)
        found, missing = discover_agents()
        if not added:
            CONSOLE.print(f"\n[{COLOR_MUTED}]No new agents found.[/{COLOR_MUTED}]")
        CONSOLE.print(
            f"[{COLOR_MUTED}]{len(found)} of {len(found) + len(missing)} known catalog agents detected. "
            f"Run [bold]agenthub doctor[/bold] to see install suggestions.[/{COLOR_MUTED}]"
        )
        CONSOLE.print(f"[{COLOR_MUTED}]Config: {config_path}[/{COLOR_MUTED}]")
        return

    if args.subcommand in ("launch", "run"):
        target = args.agent.strip().lower()
        matched = None

        # Check numeric index (1-based)
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(agents):
                matched = agents[idx]

        # Check command or name
        if not matched:
            for a in agents:
                if a["command"].lower() == target or a["name"].lower() == target:
                    matched = a
                    break

        # Check partial name match
        if not matched:
            for a in agents:
                if target in a["name"].lower() or target in a["command"].lower():
                    matched = a
                    break

        if matched:
            launch_agent(matched, interactive=False)
        else:
            CONSOLE.print(f"[{COLOR_MISSING}]Agent '{args.agent}' not found in configuration.[/{COLOR_MISSING}]")
            CONSOLE.print("Use [bold cyan]agenthub list[/bold cyan] to see available agents.")
            sys.exit(1)
        return

    if args.subcommand in ("doctor", "check"):
        run_doctor(agents, config_path, interactive=False)
        return

    if args.subcommand == "update":
        if args.agent:
            target = args.agent.strip().lower()
            matched = [a for a in agents if a["command"].lower() == target or a["name"].lower() == target]
            if matched:
                update_agents_wizard(matched)
            else:
                CONSOLE.print(f"[{COLOR_MISSING}]Agent '{args.agent}' not found.[/{COLOR_MISSING}]")
                sys.exit(1)
        else:
            update_agents_wizard(agents)
        return

    if args.subcommand == "add":
        add_agent_wizard(config, config_path)
        return

    if args.subcommand == "config":
        if args.path:
            print(str(config_path))
            return
        if args.open:
            open_config_file(config_path)
            return
        CONSOLE.print(f"[bold white]Active Config Path:[/] [cyan]{config_path}[/cyan]")
        return

    # Default: Interactive UI
    while True:
        action = choose_action(agents, config_path)
        if action.startswith("launch:"):
            idx = int(action.split(":", 1)[1])
            launch_agent(agents[idx], interactive=True)
            # Re-detect in case something changed
            config, config_path = load_config()
            agents = detect_agents(config)
        elif action == "refresh":
            CONSOLE.clear()
            config, config_path = load_config()
            config, added = sync_config(config, config_path, announce=True)
            agents = detect_agents(config)
            if not added:
                CONSOLE.print(f"[{COLOR_MUTED}]✓ Up to date — no new agents discovered.[/{COLOR_MUTED}]")
            Prompt.ask("\nPress Enter to continue", default="")
        elif action == "doctor":
            run_doctor(agents, config_path, interactive=True)
        elif action == "update":
            update_agents_wizard(agents)
            config, config_path = load_config()
            agents = detect_agents(config)
        elif action == "add":
            config = add_agent_wizard(config, config_path)
            agents = detect_agents(config)
        elif action == "settings":
            config = settings_menu(config, config_path)
            agents = detect_agents(config)
        elif action == "exit":
            CONSOLE.clear()
            exit_banner = Panel(
                f"[bold {COLOR_PRIMARY}]Thank you for using AgentHub![/bold {COLOR_PRIMARY}]\n"
                f"Run [bold cyan]agenthub[/bold cyan] anytime to switch AI coding CLI agents.",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY
            )
            CONSOLE.print(exit_banner)
            break


if __name__ == "__main__":
    main()
