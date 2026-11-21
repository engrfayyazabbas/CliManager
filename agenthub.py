"""
AgentHub — The Unified AI Developer CLI Manager
Inspired by the Claude Code terminal aesthetic.
Detects, displays, inspects, and launches AI coding CLI agents on any platform.
"""

from __future__ import annotations

import argparse
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

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

# ---------------------------------------------------------------------------
# Metadata & Styling Constants
# ---------------------------------------------------------------------------
VERSION = "1.1.0"
APP_NAME = "AgentHub"
CONSOLE = Console()

# Warm Claude Code aesthetic palette
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

DEFAULT_CONFIG: dict[str, Any] = {
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
            "name": "Codex CLI",
            "command": "codex",
            "description": "OpenAI's Codex CLI agent for software engineering",
            "install_method": "npm install -g @openai/codex",
            "update_method": "npm update -g @openai/codex",
            "config_locations": [
                "%USERPROFILE%\\.codex",
                "%USERPROFILE%\\.codex\\config.json"
            ]
        },
        {
            "name": "OpenCode CLI",
            "command": "opencode",
            "description": "Open-source AI coding CLI tool",
            "install_method": "npm install -g opencode-ai",
            "update_method": "npm update -g opencode-ai",
            "config_locations": [
                "%USERPROFILE%\\.opencode"
            ]
        },
        {
            "name": "Cursor CLI",
            "command": "agent",
            "description": "Cursor AI editor CLI interface",
            "install_method": "Install from https://cursor.com (add to PATH via Cursor settings)",
            "update_method": "Update via Cursor application or reinstall from https://cursor.com",
            "config_locations": [
                "%APPDATA%\\Cursor",
                "%USERPROFILE%\\.cursor"
            ]
        }
    ]
}


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
                json.dump(DEFAULT_CONFIG, f, indent=2)
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
    return DEFAULT_CONFIG.copy(), cfg_path


def save_config(config: dict[str, Any], target_path: Path | None = None) -> Path:
    """Save configuration dictionary to target path."""
    dest = target_path or get_config_path()
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
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
# Claude-Code Style Sticker Banner & UI Components
# ---------------------------------------------------------------------------

def render_sticker_banner(agents: list[dict[str, Any]], config_path: Path) -> Panel:
    """
    Renders the signature Claude Code-inspired sticker badge and workspace card.
    """
    installed_count = sum(1 for a in agents if a["installed"])
    total_count = len(agents)

    # Inner Sticker Badge
    sticker_text = Text()
    sticker_text.append(" ✳  A G E N T H U B \n", style=f"bold {COLOR_PRIMARY}")
    sticker_text.append("   ▲  ⬡  ◈  ⬢  ▲   \n", style=f"bold {COLOR_SECONDARY}")
    sticker_text.append(f" [ v{VERSION} • ACTIVE ]", style=f"reverse bold {COLOR_PRIMARY}")

    sticker_panel = Panel(
        sticker_text,
        box=box.HEAVY,
        border_style=f"bold {COLOR_PRIMARY}",
        padding=(0, 1),
    )

    # Info grid next to sticker
    info_table = Table.grid(padding=(0, 2))
    info_table.add_column(justify="left")
    info_table.add_column(justify="left")

    meta_text = Text()
    meta_text.append(f"{APP_NAME}", style="bold white")
    meta_text.append(" — Unified AI Developer CLI Manager\n", style=COLOR_MUTED)
    meta_text.append("Your mission control for coding agents: launch, switch, and inspect.\n\n", style=COLOR_SECONDARY)

    # Status pills
    if installed_count == total_count:
        meta_text.append(f"● {installed_count}/{total_count} Agents Ready  ", style=f"bold {COLOR_READY}")
    elif installed_count > 0:
        meta_text.append(f"● {installed_count}/{total_count} Agents Ready  ", style=f"bold {COLOR_ACCENT}")
    else:
        meta_text.append(f"○ {installed_count}/{total_count} Agents Ready  ", style=f"bold {COLOR_MISSING}")

    os_desc = f"{platform.system()} {platform.release()}" if platform.system() == "Windows" else platform.system()
    meta_text.append(f"•  Platform: {os_desc}  ", style=COLOR_MUTED)
    meta_text.append(f"•  Python {platform.python_version()}", style=COLOR_MUTED)

    info_table.add_row(sticker_panel, meta_text)

    # Breadcrumb bar
    cwd_str = str(Path.cwd())
    if len(cwd_str) > 50:
        cwd_str = "..." + cwd_str[-47:]

    cfg_str = str(config_path)
    if len(cfg_str) > 45:
        cfg_str = "..." + cfg_str[-42:]

    footer_grid = Table.grid(expand=True)
    footer_grid.add_column(justify="left")
    footer_grid.add_column(justify="right")
    footer_grid.add_row(
        Text.from_markup(f"[{COLOR_MUTED}]📁 Workspace:[/{COLOR_MUTED}] [white]{cwd_str}[/white]"),
        Text.from_markup(f"[{COLOR_MUTED}]⚙ Config:[/{COLOR_MUTED}] [white]{cfg_str}[/white]"),
    )

    content_table = Table.grid(padding=(0, 0))
    content_table.add_row(info_table)
    content_table.add_row(Text("─" * 72, style="dim"))
    content_table.add_row(footer_grid)

    return Panel(
        content_table,
        box=box.ROUNDED,
        border_style=COLOR_SECONDARY,
        title=f"[bold {COLOR_PRIMARY}]✦ Claude Code CLI Style Workspace ✦[/bold {COLOR_PRIMARY}]",
        title_align="left",
        subtitle=f"[dim]Run [bold white]agenthub --help[/bold white] for command line options[/dim]",
        subtitle_align="right",
        padding=(0, 1),
    )


def show_banner(agents: list[dict[str, Any]] | None = None, config_path: Path | None = None) -> None:
    """Print the main sticker banner to the console."""
    if agents is None or config_path is None:
        cfg, path = load_config()
        config_path = path
        agents = detect_agents(cfg)
    CONSOLE.print(render_sticker_banner(agents, config_path))


def show_status_table(agents: list[dict[str, Any]]) -> None:
    """Print a clean, beautiful status table."""
    table = Table(
        title="[bold white]Configured AI Agents[/bold white]",
        box=box.ROUNDED,
        header_style=f"bold {COLOR_PRIMARY}",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Agent", min_width=18, style="bold white")
    table.add_column("Command", min_width=10, style=COLOR_CYAN)
    table.add_column("Status", min_width=14, justify="center")
    table.add_column("Version", min_width=16, style=COLOR_ACCENT)
    table.add_column("Binary Location", min_width=24, style=COLOR_MUTED)

    for i, a in enumerate(agents, 1):
        if a["installed"]:
            status = f"[bold {COLOR_READY}]● READY[/bold {COLOR_READY}]"
        else:
            status = f"[bold {COLOR_MISSING}]○ MISSING[/bold {COLOR_MISSING}]"
        table.add_row(
            str(i),
            a["name"],
            f"`{a['command']}`",
            status,
            a["version"],
            a["exe_path"],
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

def choose_action(agents: list[dict[str, Any]], config_path: Path) -> str:
    """
    Claude Code-styled interactive menu with arrow/vim navigation,
    direct number jump (1-9), and single-letter hotkeys.
    """
    items: list[tuple[str, str, Any, str]] = []

    # Section 1: Agents
    for i, a in enumerate(agents, 1):
        shortcut = str(i) if i < 10 else ""
        items.append((f"Launch {a['name']} ({a['command']})", "launch", i - 1, shortcut))

    # Section 2: Actions
    items.append(("⚡ Refresh status & PATH", "refresh", None, "r"))
    items.append(("🩺 AgentHub Doctor (Diagnostics)", "doctor", None, "d"))
    items.append(("⬆ Update agents", "update", None, "u"))
    items.append(("➕ Add new CLI agent", "add", None, "a"))
    items.append(("⚙ Settings & Config paths", "settings", None, "s"))
    items.append(("✕ Exit AgentHub", "exit", None, "q"))

    selected = 0
    total = len(items)

    while True:
        CONSOLE.clear()
        CONSOLE.print(render_sticker_banner(agents, config_path))
        CONSOLE.print()

        # Render list of options
        rows = []
        rows.append(f"[bold {COLOR_PRIMARY}]AVAILABLE AI AGENTS[/bold {COLOR_PRIMARY}]")
        agent_count = len(agents)

        for i, (label, kind, agent_idx, shortcut) in enumerate(items):
            if i == agent_count:
                rows.append("")
                rows.append(f"[bold {COLOR_SECONDARY}]WORKSPACE & ACTIONS[/bold {COLOR_SECONDARY}]")

            is_sel = (i == selected)
            pointer = f"[bold {COLOR_PRIMARY}]❯[/bold {COLOR_PRIMARY}]" if is_sel else " "

            badge = f"[{shortcut}]" if shortcut else "   "
            badge_styled = f"[bold {COLOR_ACCENT}]{badge}[/bold {COLOR_ACCENT}]" if is_sel else f"[dim]{badge}[/dim]"

            if kind == "launch":
                agent = agents[agent_idx]
                if agent["installed"]:
                    status_pill = f"[{COLOR_READY}]● READY[/{COLOR_READY}]"
                    ver_pill = f"[{COLOR_MUTED}]{agent['version']}[/{COLOR_MUTED}]"
                else:
                    status_pill = f"[{COLOR_MISSING}]○ MISSING[/{COLOR_MISSING}]"
                    ver_pill = f"[{COLOR_MUTED}]install required[/{COLOR_MUTED}]"

                line = f"{pointer} {badge_styled} [bold white]{label:<32}[/bold white] {status_pill}  {ver_pill}"
            else:
                line = f"{pointer} {badge_styled} [white]{label:<32}[/white]"

            if is_sel:
                line = f"[reverse]{line}[/reverse]" if False else f"[bold]{line}[/bold]"
            rows.append(line)

        footer_text = f"[bold {COLOR_PRIMARY}]↑/↓ or j/k:[/] Navigate  •  [bold {COLOR_PRIMARY}]Enter:[/] Select  •  [bold {COLOR_PRIMARY}]1-{min(9, len(agents))}:[/] Quick Launch  •  [bold {COLOR_PRIMARY}]q:[/] Quit"

        CONSOLE.print(Panel(
            "\n".join(rows),
            title=f"[bold white]Select an Agent or Action[/bold white]",
            subtitle=footer_text,
            box=box.ROUNDED,
            border_style=COLOR_PRIMARY,
            padding=(1, 2)
        ))

        key = read_navigation_key()

        # Navigation
        if key in ("up", "k"):
            selected = (selected - 1) % total
        elif key in ("down", "j"):
            selected = (selected + 1) % total
        elif key == "enter":
            _, kind, idx, _ = items[selected]
            return f"{kind}:{idx}" if idx is not None else kind
        elif key in ("q", "escape"):
            return "exit"
        else:
            # Check for direct number or letter shortcut
            for i, (_, kind, idx, shortcut) in enumerate(items):
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
        CONSOLE.print("  [bold white]6.[/bold white] Back to main menu")

        choice = Prompt.ask("\n  Select option", choices=["1", "2", "3", "4", "5", "6"], default="6")

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
                config = DEFAULT_CONFIG.copy()
                save_config(config, config_path)
                Prompt.ask("\n  Config reset. Press Enter", default="")
        elif choice == "6":
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
        description="AgentHub — The Unified AI Developer CLI Manager (Claude Code-inspired interface)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agenthub                 # Open interactive Claude Code-styled dashboard
  agenthub list            # Print status summary table of all agents
  agenthub launch agy      # Directly launch Gemini CLI (agy)
  agenthub launch codex    # Directly launch Codex CLI
  agenthub doctor          # Run environment and PATH diagnostics
  agenthub update          # Check and update installed agents
  agenthub add             # Add a new CLI agent interactively
  agenthub config --path   # Display active configuration path
"""
    )
    parser.add_argument("-v", "--version", action="version", version=f"AgentHub v{VERSION}")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # list
    subparsers.add_parser("list", aliases=["ls"], help="List all configured agents and their status")

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

    config, config_path = load_config()
    agents = detect_agents(config)

    # Subcommand dispatch
    if args.subcommand in ("list", "ls"):
        CONSOLE.print(render_sticker_banner(agents, config_path))
        CONSOLE.print()
        show_status_table(agents)
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
            config, config_path = load_config()
            agents = detect_agents(config)
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
