"""
AgentHub — Local CLI Agent Manager
Detects, displays, and launches AI coding CLI agents on Windows.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 encoding for standard streams on Windows to prevent UnicodeEncodeError
# in legacy consoles (e.g. cp1252) or IDE output panes like VS Code Code Runner.
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
# Constants
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "agents.json"
console = Console()

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load agent configuration from JSON file."""
    if not CONFIG_PATH.exists():
        console.print("[red]Config file not found:[/red] agents.json")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Write agent configuration back to JSON file."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    console.print("[green]Configuration saved.[/green]")

# ---------------------------------------------------------------------------
# Agent detection
# ---------------------------------------------------------------------------

def find_executable(command: str) -> str | None:
    """Return the full path of *command* if it is on PATH, else None."""
    return shutil.which(command)


def get_version(command: str) -> str:
    """Try common flags to retrieve the version string of a CLI tool."""
    import re
    for flag in ("--version", "-v", "version", "-V"):
        try:
            result = subprocess.run(
                f"{command} {flag}",
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            # Combine stdout and stderr — some tools print version to stderr
            combined = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            if not combined:
                continue

            # Skip entirely if the output is clearly an error dump
            lower = combined.lower()
            if "traceback" in lower or "platformerror" in lower or "eperm" in lower:
                continue

            # Look for a line containing a version-like pattern
            for line in combined.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Skip stack trace lines, warnings, errors
                if (line.startswith("at ") or line.startswith("(") or
                    "warning" in line.lower() or "error" in line.lower() or
                    line.startswith("{")):
                    continue
                if re.search(r"\d+\.\d+", line):
                    return line
        except Exception:
            continue
    return "unknown"


def expand_path(p: str) -> str:
    """Expand environment variables in a path string."""
    return os.path.expandvars(p)


def detect_agents(config: dict) -> list[dict]:
    """Return enriched agent records with installation status."""
    agents = []
    for entry in config.get("agents", []):
        cmd = entry["command"]
        exe_path = find_executable(cmd)
        installed = exe_path is not None
        version = get_version(cmd) if installed else "—"
        agents.append({
            **entry,
            "installed": installed,
            "exe_path": exe_path or "not found",
            "version": version,
        })
    return agents

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def show_banner() -> None:
    banner = Text("⚡ AgentHub", style="bold bright_cyan")
    banner.append(" — Local CLI Agent Manager", style="dim")
    console.print(Panel(banner, box=box.DOUBLE, expand=False, padding=(0, 2)))


def show_status_table(agents: list[dict]) -> None:
    """Print a Rich table summarising each agent."""
    table = Table(
        title="Agent Status",
        box=box.ROUNDED,
        title_style="bold white",
        header_style="bold bright_cyan",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Agent", min_width=14)
    table.add_column("Status", min_width=10, justify="center")
    table.add_column("Version", min_width=14)
    table.add_column("Path", min_width=20)

    for i, a in enumerate(agents, 1):
        status = "[green]● installed[/green]" if a["installed"] else "[red]✗ missing[/red]"
        table.add_row(str(i), a["name"], status, a["version"], a["exe_path"])

    console.print(table)


def show_menu(agents: list[dict]) -> None:
    """Print the interactive menu."""
    console.print()
    menu_items = []
    for i, a in enumerate(agents, 1):
        tag = "[green]●[/green]" if a["installed"] else "[red]✗[/red]"
        menu_items.append(f"  {tag} [bold]{i}.[/bold] Launch {a['name']}")

    n = len(agents)
    menu_items.append(f"  [bold]{n+1}.[/bold] Refresh agent status")
    menu_items.append(f"  [bold]{n+2}.[/bold] Check agent versions")
    menu_items.append(f"  [bold]{n+3}.[/bold] Update agents")
    menu_items.append(f"  [bold]{n+4}.[/bold] Settings")
    menu_items.append(f"  [bold]{n+5}.[/bold] Exit")

    console.print(Panel(
        "\n".join(menu_items),
        title="[bold]Menu[/bold]",
        box=box.ROUNDED,
        expand=False,
        padding=(1, 3),
    ))

# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def launch_agent(agent: dict) -> None:
    """Launch an agent in the current working directory."""
    if not agent["installed"]:
        console.print(f"[red]{agent['name']} is not installed.[/red]")
        console.print(f"  Install with: [cyan]{agent.get('install_method', 'see documentation')}[/cyan]")
        return

    console.print(f"\n[bold bright_cyan]Launching {agent['name']}...[/bold bright_cyan]")
    console.print(f"[dim]Working directory: {os.getcwd()}[/dim]\n")
    try:
        subprocess.run(agent["command"], cwd=os.getcwd(), shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[yellow]{agent['name']} session ended.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error launching {agent['name']}: {e}[/red]")


def check_versions(agents: list[dict]) -> None:
    """Display version information for all installed agents."""
    console.print("\n[bold]Checking versions...[/bold]\n")
    table = Table(box=box.SIMPLE, header_style="bold")
    table.add_column("Agent", min_width=14)
    table.add_column("Version")
    for a in agents:
        if a["installed"]:
            ver = get_version(a["command"])
            table.add_row(a["name"], ver)
        else:
            table.add_row(a["name"], "[dim]not installed[/dim]")
    console.print(table)


def update_agents(agents: list[dict]) -> None:
    """Offer to update each installed agent using its documented method."""
    console.print("\n[bold]Agent Update[/bold]\n")
    for a in agents:
        if not a["installed"]:
            console.print(f"  [dim]{a['name']} — not installed, skipping[/dim]")
            continue

        method = a.get("update_method", "")
        if not method:
            console.print(f"  [dim]{a['name']} — no update method configured[/dim]")
            continue

        console.print(f"  [bold]{a['name']}[/bold]")
        console.print(f"    Update command: [cyan]{method}[/cyan]")

        if not Confirm.ask("    Run this update?", default=False):
            console.print("    [dim]Skipped.[/dim]")
            continue

        console.print(f"    [yellow]Running: {method}[/yellow]")
        try:
            subprocess.run(method, shell=True, cwd=os.getcwd())
            console.print(f"    [green]Done.[/green]")
        except Exception as e:
            console.print(f"    [red]Error: {e}[/red]")


def show_agent_info(agents: list[dict]) -> None:
    """Show detailed info and config locations for each agent."""
    console.print("\n[bold]Agent Details[/bold]\n")
    for a in agents:
        status = "[green]installed[/green]" if a["installed"] else "[red]missing[/red]"
        lines = [
            f"[bold]Status:[/bold]  {status}",
            f"[bold]Command:[/bold] {a['command']}",
            f"[bold]Path:[/bold]    {a['exe_path']}",
            f"[bold]Version:[/bold] {a['version']}",
            f"[bold]Description:[/bold] {a.get('description', '—')}",
            f"[bold]Install:[/bold] [cyan]{a.get('install_method', '—')}[/cyan]",
            f"[bold]Update:[/bold]  [cyan]{a.get('update_method', '—')}[/cyan]",
        ]
        config_locs = a.get("config_locations", [])
        if config_locs:
            lines.append("[bold]Config locations:[/bold]")
            for loc in config_locs:
                expanded = expand_path(loc)
                exists = "✓" if os.path.exists(expanded) else "✗"
                lines.append(f"  {exists} {expanded}")

        console.print(Panel(
            "\n".join(lines),
            title=f"[bold]{a['name']}[/bold]",
            box=box.ROUNDED,
            expand=False,
            padding=(0, 2),
        ))


def settings_menu(config: dict) -> dict:
    """Simple settings sub-menu."""
    while True:
        console.print("\n[bold]Settings[/bold]\n")
        console.print("  [bold]1.[/bold] View agent details & config locations")
        console.print("  [bold]2.[/bold] Add a new agent")
        console.print("  [bold]3.[/bold] Remove an agent")
        console.print("  [bold]4.[/bold] Open agents.json in editor")
        console.print("  [bold]5.[/bold] Back to main menu")

        choice = Prompt.ask("\n  Choice", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == "1":
            agents = detect_agents(config)
            show_agent_info(agents)

        elif choice == "2":
            config = add_agent(config)

        elif choice == "3":
            config = remove_agent(config)

        elif choice == "4":
            open_config_in_editor()

        elif choice == "5":
            break

    return config


def add_agent(config: dict) -> dict:
    """Interactively add a new agent entry."""
    console.print("\n[bold]Add New Agent[/bold]\n")
    name = Prompt.ask("  Agent name")
    command = Prompt.ask("  CLI command")
    description = Prompt.ask("  Description", default="")
    install_method = Prompt.ask("  Install command", default="")
    update_method = Prompt.ask("  Update command", default="")
    config_loc = Prompt.ask("  Config location (optional)", default="")

    entry = {
        "name": name,
        "command": command,
        "description": description,
        "install_method": install_method,
        "update_method": update_method,
        "config_locations": [config_loc] if config_loc else [],
    }

    config.setdefault("agents", []).append(entry)
    save_config(config)
    console.print(f"[green]{name} added.[/green]")
    return config


def remove_agent(config: dict) -> dict:
    """Interactively remove an agent entry."""
    agents = config.get("agents", [])
    if not agents:
        console.print("[dim]No agents configured.[/dim]")
        return config

    console.print("\n[bold]Remove Agent[/bold]\n")
    for i, a in enumerate(agents, 1):
        console.print(f"  [bold]{i}.[/bold] {a['name']} ({a['command']})")

    idx = Prompt.ask("  Agent # to remove (0 to cancel)", default="0")
    try:
        idx = int(idx)
    except ValueError:
        return config

    if 1 <= idx <= len(agents):
        removed = agents.pop(idx - 1)
        if Confirm.ask(f"  Remove [bold]{removed['name']}[/bold]?", default=False):
            save_config(config)
            console.print(f"[green]{removed['name']} removed.[/green]")
        else:
            agents.insert(idx - 1, removed)
            console.print("[dim]Cancelled.[/dim]")

    return config


def open_config_in_editor() -> None:
    """Open agents.json in the default editor."""
    try:
        os.startfile(str(CONFIG_PATH))  # Windows-specific
    except Exception:
        console.print(f"[dim]Open manually: {CONFIG_PATH}[/dim]")

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    console.clear()
    show_banner()

    config = load_config()
    agents = detect_agents(config)
    show_status_table(agents)

    while True:
        show_menu(agents)
        n = len(agents)
        valid = [str(i) for i in range(1, n + 6)]
        choice = Prompt.ask("\n  Select", choices=valid, default=str(n + 5))
        idx = int(choice)

        if idx <= n:
            # Launch agent
            launch_agent(agents[idx - 1])

        elif idx == n + 1:
            # Refresh
            console.print("\n[yellow]Refreshing...[/yellow]")
            config = load_config()
            agents = detect_agents(config)
            show_status_table(agents)

        elif idx == n + 2:
            # Check versions
            check_versions(agents)

        elif idx == n + 3:
            # Update agents
            update_agents(agents)

        elif idx == n + 4:
            # Settings
            config = settings_menu(config)
            agents = detect_agents(config)

        elif idx == n + 5:
            # Exit
            console.print("\n[dim]Goodbye.[/dim]\n")
            break


if __name__ == "__main__":
    main()
