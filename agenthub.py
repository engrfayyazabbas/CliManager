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
import time
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
from rich.prompt import Prompt
from rich.text import Text
from rich import box

# ---------------------------------------------------------------------------
# Metadata & Styling Constants
# ---------------------------------------------------------------------------
VERSION = "1.3.0"
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
        "uninstall_method": "npm uninstall -g @anthropic-ai/claude-code",
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
        "uninstall_method": "npm uninstall -g @openai/codex",
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
        "uninstall_method": "npm uninstall -g @google/gemini-cli",
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
        "uninstall_method": "",
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
        "uninstall_method": "npm uninstall -g opencode-ai",
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
        "uninstall_method": "",
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
        "uninstall_method": "pip uninstall -y aider-chat  (or: uv tool uninstall aider-chat)",
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
        "uninstall_method": "",
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
        "uninstall_method": "npm uninstall -g @qwen-code/qwen-code",
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
        "uninstall_method": "npm uninstall -g @charmland/crush",
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
        "uninstall_method": "npm uninstall -g @sourcegraph/amp",
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
        "uninstall_method": "",
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
        "uninstall_method": "uv tool uninstall openhands  (or: pip uninstall -y openhands-ai)",
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
        "uninstall_method": "npm uninstall -g @github/copilot",
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
        "uninstall_method": "npm uninstall -g @continuedev/cli",
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
        "uninstall_method": "npm uninstall -g codebuff",
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
        "uninstall_method": "uv tool uninstall kimi-cli",
        "config_locations": [
            "~/.kimi",
        ],
    },
]


def default_config() -> dict[str, Any]:
    """Return a fresh starter config (empty — auto-sync fills it on startup)."""
    return {"agents": [], "ignored": []}


def hidden_commands(config: dict[str, Any]) -> set[str]:
    """Commands the user chose to hide from AgentHub."""
    return {
        str(cmd).strip().lower()
        for cmd in config.get("ignored", [])
        if str(cmd).strip()
    }


def set_agent_hidden(config: dict[str, Any], command: str, hidden: bool) -> None:
    """Add or remove a command from the hidden list (persisted by the caller)."""
    commands = hidden_commands(config)
    cmd = command.strip().lower()
    if not cmd:
        return
    if hidden:
        commands.add(cmd)
    else:
        commands.discard(cmd)
    config["ignored"] = sorted(commands)


_NON_COMMAND_PREFIXES = ("see ", "install ", "visit ", "download ", "update ")

_INSTALL_TO_UNINSTALL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^npm\s+(?:install|i)\s+(?:-g|--global)\s+(.+)$", re.IGNORECASE), r"npm uninstall -g \1"),
    (re.compile(r"^pnpm\s+(?:add|install|i)\s+(?:-g|--global)\s+(.+)$", re.IGNORECASE), r"pnpm remove -g \1"),
    (re.compile(r"^bun\s+(?:add|install|i)\s+(?:-g|--global)\s+(.+)$", re.IGNORECASE), r"bun remove -g \1"),
    (re.compile(r"^uv\s+tool\s+install\s+(.+)$", re.IGNORECASE), r"uv tool uninstall \1"),
    (re.compile(r"^pipx\s+install\s+(.+)$", re.IGNORECASE), r"pipx uninstall \1"),
    (re.compile(r"^(pip3?)\s+install\s+(.+)$", re.IGNORECASE), r"\1 uninstall -y \2"),
    (re.compile(r"^cargo\s+install\s+(.+)$", re.IGNORECASE), r"cargo uninstall \1"),
    (re.compile(r"^brew\s+install\s+(.+)$", re.IGNORECASE), r"brew uninstall \1"),
]


def _split_command_alternatives(raw: str) -> list[str]:
    """Split strings like 'pip install X  (or: uv tool install X)' into commands."""
    text = str(raw or "").strip()
    if not text:
        return []
    match = re.match(r"^(.*?)\s*\(or:\s*(.+)\)\s*$", text, flags=re.IGNORECASE)
    if match:
        parts = [match.group(1).strip()]
        parts.extend(
            p.strip()
            for p in re.split(r"\s+or\s+", match.group(2), flags=re.IGNORECASE)
            if p.strip()
        )
        return [p for p in parts if p]
    return [text]


def _is_runnable_command(cmd: str) -> bool:
    """Return True if *cmd* looks like a shell command rather than prose instructions."""
    stripped = str(cmd or "").strip()
    if not stripped:
        return False
    lower = stripped.lower()
    return not any(lower.startswith(prefix) for prefix in _NON_COMMAND_PREFIXES)


def _derive_uninstall_from_install(install_cmd: str) -> str | None:
    """Infer an uninstall command from a package-manager install command."""
    cleaned = str(install_cmd or "").strip()
    if not cleaned:
        return None
    for pattern, replacement in _INSTALL_TO_UNINSTALL_PATTERNS:
        if pattern.match(cleaned):
            derived = pattern.sub(replacement, cleaned)
            # Strip install-only flags such as --upgrade / -U when deriving uninstall
            tokens = [
                tok for tok in derived.split()
                if tok not in ("-U", "--upgrade", "--force-reinstall", "--force")
            ]
            return " ".join(tokens)
    return None


def _pick_available_command(candidates: list[str], *, preferred_hint: str = "") -> str | None:
    """Choose the best runnable command from *candidates* based on environment hints."""
    runnable = [c for c in candidates if _is_runnable_command(c)]
    if not runnable:
        return None

    hint = preferred_hint.lower()
    if any(marker in hint for marker in ("/uv/", "\\uv\\", "uv\\tools", "uv/tools")):
        for cmd in runnable:
            if cmd.lower().startswith("uv "):
                return cmd
    if "pipx" in hint:
        for cmd in runnable:
            if cmd.lower().startswith("pipx "):
                return cmd

    for cmd in runnable:
        head = cmd.split()[0]
        if find_executable(head):
            return cmd
        if head.lower() == "pip" and find_executable("pip3"):
            return cmd
    return runnable[0]


def resolve_install_command(entry: dict[str, Any]) -> str | None:
    """Return a runnable install command for *entry*, or None if manual install is needed."""
    candidates = _split_command_alternatives(str(entry.get("install_method", "")))
    return _pick_available_command(candidates)


def resolve_uninstall_command(entry: dict[str, Any]) -> str | None:
    """Return a runnable uninstall command for *entry*, or None if manual uninstall is needed."""
    explicit = _split_command_alternatives(str(entry.get("uninstall_method", "")))
    if explicit:
        candidates = explicit
    else:
        candidates = []
        for alt in _split_command_alternatives(str(entry.get("install_method", ""))):
            if _is_runnable_command(alt):
                derived = _derive_uninstall_from_install(alt)
                if derived:
                    candidates.append(derived)

    cmd = str(entry.get("command", "")).strip()
    exe_hint = str(entry.get("exe_path") or (find_executable(cmd) if cmd else "") or "")
    return _pick_available_command(candidates, preferred_hint=exe_hint)


def _resolve_entry_in_list(
    entries: list[dict[str, Any]],
    target: str,
    *,
    index_entries: list[dict[str, Any]] | None = None,
    not_found_message: str | None = None,
) -> tuple[int | None, dict[str, Any] | None, str | None]:
    """
    Resolve *target* (1-based index into *index_entries*, exact command/alias/name,
    or unique partial match) to ``(entries_index, entry, error_message)``.
    """
    raw = target.strip()
    if not raw:
        return None, None, "No agent specified."

    needle = raw.lower()

    if raw.isdigit() and index_entries is not None:
        vis_idx = int(raw) - 1
        if 0 <= vis_idx < len(index_entries):
            chosen = index_entries[vis_idx]
            chosen_cmd = str(chosen.get("command", "")).strip().lower()
            chosen_name = str(chosen.get("name", "")).strip().lower()
            for idx, entry in enumerate(entries):
                if (
                    str(entry.get("command", "")).strip().lower() == chosen_cmd
                    and str(entry.get("name", "")).strip().lower() == chosen_name
                ):
                    return idx, entry, None
            for idx, entry in enumerate(entries):
                if str(entry.get("command", "")).strip().lower() == chosen_cmd:
                    return idx, entry, None

    for idx, entry in enumerate(entries):
        cmd = str(entry.get("command", "")).strip().lower()
        name = str(entry.get("name", "")).strip().lower()
        aliases = [str(a).strip().lower() for a in entry.get("aliases") or [] if a]
        if needle == cmd or needle == name or needle in aliases:
            return idx, entry, None

    partial_matches = [
        (idx, entry)
        for idx, entry in enumerate(entries)
        if needle in str(entry.get("command", "")).strip().lower()
        or needle in str(entry.get("name", "")).strip().lower()
        or any(needle in str(a).strip().lower() for a in entry.get("aliases") or [] if a)
    ]
    if len(partial_matches) == 1:
        idx, entry = partial_matches[0]
        return idx, entry, None
    if len(partial_matches) > 1:
        names = ", ".join(
            f"{e.get('name', e.get('command', ''))} ({e.get('command', '')})"
            for _, e in partial_matches
        )
        return None, None, f"Multiple agents match '{target}': {names}. Be more specific."

    return None, None, not_found_message or f"Agent '{target}' not found."


def resolve_agent_for_removal(
    config: dict[str, Any],
    target: str,
    *,
    visible_agents: list[dict[str, Any]] | None = None,
) -> tuple[int | None, dict[str, Any] | None, str | None]:
    """Resolve *target* against configured agents for removal."""
    return _resolve_entry_in_list(
        config.get("agents", []),
        target,
        index_entries=visible_agents,
        not_found_message=f"Agent '{target}' not found in configuration.",
    )


def remove_agent_from_config(
    config: dict[str, Any],
    index: int,
    *,
    discovered: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], bool]:
    """
    Remove the agent at *index* from ``config["agents"]``.

    If the removed command corresponds to an installed catalog agent and no
    remaining entry shares that command, add it to ``config["ignored"]`` so
    auto-sync will not immediately re-add it. Otherwise remove it from
    ``ignored`` if present.

    Returns ``(removed_entry, added_to_ignored)``.
    """
    agents: list[dict[str, Any]] = config.setdefault("agents", [])
    removed = agents.pop(index)
    cmd = str(removed.get("command", "")).strip().lower()

    if not cmd:
        return removed, False

    still_present = any(
        str(a.get("command", "")).strip().lower() == cmd
        for a in agents
    )
    if still_present:
        return removed, False

    if discovered is None:
        discovered, _missing = discover_agents()

    is_discovered = False
    for entry in discovered:
        names = [str(entry.get("command", "")).strip().lower()]
        names += [str(a).strip().lower() for a in entry.get("aliases") or [] if a]
        if cmd in names:
            is_discovered = True
            break

    if is_discovered:
        set_agent_hidden(config, cmd, True)
        return removed, True

    set_agent_hidden(config, cmd, False)
    return removed, False


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
                config = json.load(f)
            config.setdefault("agents", [])
            config.setdefault("ignored", [])
            return config, cfg_path
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
    """Enrich agent configurations with live detection status (hidden agents skipped)."""
    ignored = hidden_commands(config)
    enriched = []
    for entry in config.get("agents", []):
        cmd = entry.get("command", "")
        if str(cmd).strip().lower() in ignored:
            continue
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
    ignored = hidden_commands(config)
    index = {str(a.get("command", "")).strip().lower(): a for a in agents}
    added: list[str] = []
    enriched: list[str] = []

    for entry in discovered:
        command = str(entry.get("command", "")).strip()
        if not command:
            continue

        candidates = [command.lower()]
        candidates += [str(a).strip().lower() for a in entry.get("aliases") or [] if a]
        if any(c in ignored for c in candidates):
            continue
        existing = next((index[c] for c in candidates if c in index), None)

        if existing is not None:
            changed = False
            for key in ("description", "install_method", "update_method", "uninstall_method"):
                if not existing.get(key) and entry.get(key):
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
            "uninstall_method": entry.get("uninstall_method", ""),
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
            "  No agents detected. Press r to scan, d for doctor.",
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
    items.append(("Install agent", "install", None, "i"))
    items.append(("Doctor", "doctor", None, "d"))
    items.append(("Update all agents", "update", None, "u"))
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
# Shared Sub-Menu Components (used by Update / Settings)
# ---------------------------------------------------------------------------

def _submenu_render(
    title: str,
    options: list[tuple[str, str, str]],
    selected: int,
    subtitle: str,
    footer: str,
) -> Panel:
    """Render a keyboard-driven sub-menu in the same style as the main menu."""
    lines: list[Text] = []
    if subtitle:
        lines.append(Text(subtitle, style=COLOR_MUTED))
        lines.append(Text(""))

    for i, (_key, label, hint) in enumerate(options):
        row = Text(no_wrap=True)
        if i == selected:
            row.append("❯ ", style=f"bold {COLOR_PRIMARY}")
            row.append(f"{label:<28}", style=f"bold white on {COLOR_PRIMARY}")
            if hint:
                row.append(f" {hint}", style=f"white on {COLOR_PRIMARY}")
        else:
            row.append("  ")
            row.append(f"{label:<28}", style="white")
            if hint:
                row.append(f" {hint}", style=COLOR_MUTED)
        lines.append(row)

    body = Text("\n").join(lines)
    body.append("\n\n")
    body.append(footer, style=COLOR_MUTED)
    return Panel(
        body,
        title=f"[bold {COLOR_PRIMARY}]{title}[/bold {COLOR_PRIMARY}]",
        box=box.ROUNDED,
        border_style=COLOR_SECONDARY,
        padding=(1, 1),
    )


def pick_from_menu(
    title: str,
    options: list[tuple[str, str, str]],
    *,
    subtitle: str = "",
    footer: str = "↑↓ move · Enter select · 1-9 jump · q back",
) -> str:
    """Keyboard-driven selection. Returns the option key, or "back"."""
    if not options:
        return "back"

    selected = 0
    total = len(options)

    CONSOLE.clear()
    with Live(
        _submenu_render(title, options, selected, subtitle, footer),
        console=CONSOLE,
        auto_refresh=False,
        transient=True,
    ) as live:
        while True:
            key = read_navigation_key()

            if key in ("up", "k"):
                selected = (selected - 1) % total
                live.update(_submenu_render(title, options, selected, subtitle, footer), refresh=True)
            elif key in ("down", "j"):
                selected = (selected + 1) % total
                live.update(_submenu_render(title, options, selected, subtitle, footer), refresh=True)
            elif key == "enter":
                return options[selected][0]
            elif key in ("q", "escape"):
                return "back"
            elif key.isdigit() and 1 <= int(key) <= total:
                selected = int(key) - 1
                live.update(_submenu_render(title, options, selected, subtitle, footer), refresh=True)
            else:
                for option_key, _label, _hint in options:
                    if len(option_key) == 1 and key == option_key.lower():
                        return option_key

    return "back"


def confirm_panel(title: str, message: str, *, danger: bool = False) -> bool:
    """Single-key confirmation panel. Enter/y confirms, q/n/Esc cancels."""
    CONSOLE.clear()
    CONSOLE.print(Panel(
        message,
        title=f"[bold {COLOR_MISSING if danger else COLOR_PRIMARY}]{title}[/bold {COLOR_MISSING if danger else COLOR_PRIMARY}]",
        box=box.ROUNDED,
        border_style=COLOR_MISSING if danger else COLOR_PRIMARY,
        padding=(1, 2),
    ))
    CONSOLE.print(f"[{COLOR_MUTED}]Enter / y to confirm  ·  q / n to cancel[/{COLOR_MUTED}]")
    while True:
        key = read_navigation_key()
        if key in ("enter", "y"):
            return True
        if key in ("q", "n", "escape"):
            return False


def pause(message: str = "Press any key to return") -> None:
    """Wait for a single keypress instead of a full line prompt."""
    CONSOLE.print(f"[{COLOR_MUTED}]{message}[/{COLOR_MUTED}]", end="")
    read_navigation_key()
    CONSOLE.print()

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
        pause()


def updatable_agents(agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Installed agents that declare an update command."""
    return [
        a for a in agents
        if a.get("installed") and str(a.get("update_method", "")).strip()
    ]


_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _output_tail(output: str, lines: int = 4) -> str:
    """Last few meaningful lines of captured command output."""
    cleaned = _ANSI_RE.sub("", output or "")
    rows = [line.rstrip() for line in cleaned.splitlines() if line.strip()]
    return "\n".join(rows[-lines:]) if rows else "(no output)"


def _update_preview(targets: list[dict[str, Any]]) -> Table:
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {COLOR_PRIMARY}", pad_edge=False)
    table.add_column("#", style=COLOR_MUTED, width=3, justify="right")
    table.add_column("Agent", style="bold white")
    table.add_column("Command", style=COLOR_CYAN)
    table.add_column("Version", style=COLOR_MUTED)
    table.add_column("Update command", style=COLOR_ACCENT)
    for i, agent in enumerate(targets, 1):
        table.add_row(
            str(i),
            agent["name"],
            agent["command"],
            str(agent["version"]),
            str(agent.get("update_method", "")),
        )
    return table


def _update_progress(
    targets: list[dict[str, Any]],
    states: dict[str, dict[str, Any]],
) -> Panel:
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {COLOR_PRIMARY}", pad_edge=False)
    table.add_column("Agent", style="bold white")
    table.add_column("Command", style=COLOR_CYAN)
    table.add_column("Status", min_width=24)

    for agent in targets:
        state = states.get(agent["command"], {})
        status = state.get("state", "pending")
        duration = state.get("duration", 0.0)
        if status == "running":
            label = f"[{COLOR_ACCENT}]◐ running…[/{COLOR_ACCENT}]"
        elif status == "done":
            label = f"[{COLOR_READY}]✓ updated[/{COLOR_READY}] [{COLOR_MUTED}]{duration:.1f}s[/{COLOR_MUTED}]"
        elif status == "failed":
            label = f"[{COLOR_MISSING}]✗ failed[/{COLOR_MISSING}] [{COLOR_MUTED}]{duration:.1f}s[/{COLOR_MUTED}]"
        else:
            label = f"[{COLOR_MUTED}]· waiting[/{COLOR_MUTED}]"
        table.add_row(agent["name"], agent["command"], label)

    return Panel(
        Group(
            Text(f"Updating {len(targets)} agent(s) in one batch — no per-agent prompts.", style=COLOR_MUTED),
            Text(""),
            table,
        ),
        title=f"[bold {COLOR_PRIMARY}]AgentHub — Updating[/bold {COLOR_PRIMARY}]",
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY,
    )


def update_agents_wizard(agents: list[dict[str, Any]], *, prompt_return: bool = True) -> None:
    """Update every installed agent in one batch, with a single confirmation."""
    targets = updatable_agents(agents)
    CONSOLE.clear()

    if not targets:
        CONSOLE.print(Panel(
            f"[bold white]Nothing to update.[/bold white]\n\n"
            f"[{COLOR_MUTED}]No installed agent has an update command configured. "
            f"Install or register an agent first.[/{COLOR_MUTED}]",
            title=f"[bold {COLOR_PRIMARY}]AgentHub Updater[/bold {COLOR_PRIMARY}]",
            box=box.ROUNDED,
            border_style=COLOR_PRIMARY,
        ))
        if prompt_return:
            pause()
        return

    CONSOLE.print(Panel(
        Group(
            Text("These update commands will run one after another:", style="bold white"),
            Text(""),
            _update_preview(targets),
        ),
        title=f"[bold {COLOR_PRIMARY}]AgentHub Updater[/bold {COLOR_PRIMARY}]",
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY,
    ))
    CONSOLE.print()

    if not confirm_panel(
        "Update all agents?",
        f"Run [bold yellow]{len(targets)}[/bold yellow] update command(s) now?\n\n"
        f"[{COLOR_MUTED}]Updates are sequential. You can leave this screen while they run.[/{COLOR_MUTED}]",
    ):
        CONSOLE.print(f"[{COLOR_MUTED}]Update cancelled.[/{COLOR_MUTED}]")
        if prompt_return:
            pause()
        return

    states = {
        agent["command"]: {"state": "pending", "duration": 0.0}
        for agent in targets
    }
    results: list[tuple[dict[str, Any], bool, float, str]] = []

    with Live(
        _update_progress(targets, states),
        console=CONSOLE,
        refresh_per_second=8,
        transient=False,
    ) as live:
        for agent in targets:
            states[agent["command"]]["state"] = "running"
            live.update(_update_progress(targets, states), refresh=True)

            started = time.monotonic()
            try:
                proc = subprocess.run(
                    agent["update_method"],
                    shell=True,
                    cwd=os.getcwd(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                ok = proc.returncode == 0
                output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
            except Exception as exc:
                ok = False
                output = str(exc)

            duration = time.monotonic() - started
            states[agent["command"]].update({
                "state": "done" if ok else "failed",
                "duration": duration,
            })
            live.update(_update_progress(targets, states), refresh=True)
            results.append((agent, ok, duration, output))

    succeeded = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    CONSOLE.print()
    summary_style = COLOR_READY if not failed else COLOR_ACCENT
    CONSOLE.print(
        f"[bold {summary_style}]Batch finished:[/bold {summary_style}] "
        f"[{COLOR_READY}]{len(succeeded)} updated[/{COLOR_READY}] · "
        f"[{COLOR_MISSING}]{len(failed)} failed[/{COLOR_MISSING}]"
    )
    for agent, _ok, duration, _output in succeeded:
        CONSOLE.print(f"  [{COLOR_READY}]✓[/{COLOR_READY}] {agent['name']} [{COLOR_MUTED}]({duration:.1f}s)[/{COLOR_MUTED}]")
    for agent, _ok, duration, output in failed:
        CONSOLE.print(f"  [{COLOR_MISSING}]✗[/{COLOR_MISSING}] {agent['name']} [{COLOR_MUTED}]({duration:.1f}s)[/{COLOR_MUTED}]")
        CONSOLE.print(Panel(
            Text(_output_tail(output, 6)),
            title=f"[bold {COLOR_MISSING}]{agent['name']} — last output[/bold {COLOR_MISSING}]",
            box=box.ROUNDED,
            border_style=COLOR_MISSING,
            padding=(0, 1),
        ))

    if prompt_return:
        pause()

def _agent_keys(entry: dict[str, Any]) -> set[str]:
    """All lowercase command and alias identifiers for an agent entry."""
    keys: set[str] = set()
    cmd = str(entry.get("command", "")).strip().lower()
    if cmd:
        keys.add(cmd)
    for alias in entry.get("aliases") or []:
        text = str(alias).strip().lower()
        if text:
            keys.add(text)
    return keys


def _find_installed_command(entry: dict[str, Any]) -> tuple[str, str | None]:
    """Return (resolved_command, exe_path) checking primary command and aliases."""
    cmd = str(entry.get("command", "")).strip()
    if cmd:
        exe = find_executable(cmd)
        if exe:
            return cmd, exe
    for alias in entry.get("aliases") or []:
        alias_str = str(alias).strip()
        if alias_str:
            exe = find_executable(alias_str)
            if exe:
                return alias_str, exe
    return cmd, None


def installable_agents(
    config: dict[str, Any],
    *,
    catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return catalog and configured agents that are not currently installed."""
    found, missing = discover_agents(catalog)
    seen: set[str] = set()
    for entry in found:
        seen.update(_agent_keys(entry))

    candidates: list[dict[str, Any]] = []
    for entry in missing:
        candidates.append(entry)
        seen.update(_agent_keys(entry))

    for entry in config.get("agents", []):
        cmd = str(entry.get("command", "")).strip()
        if not cmd or cmd.lower() in seen:
            continue
        if not find_executable(cmd):
            candidates.append(entry)
            seen.add(cmd.lower())

    return candidates


def uninstallable_agents(
    config: dict[str, Any],
    *,
    catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return installed agents (configured or catalog-discovered) eligible for uninstall."""
    found, _missing = discover_agents(catalog)
    catalog_by_key: dict[str, dict[str, Any]] = {}
    for entry in found:
        for key in _agent_keys(entry):
            catalog_by_key[key] = entry

    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    for entry in config.get("agents", []):
        cmd, exe = _find_installed_command(entry)
        if not cmd or not exe:
            continue
        cat_match = catalog_by_key.get(cmd.lower(), {})
        merged = {
            **entry,
            "exe_path": exe,
            "uninstall_method": entry.get("uninstall_method") or cat_match.get("uninstall_method", ""),
        }
        result.append(merged)
        seen.update(_agent_keys(merged))

    for entry in found:
        cmd, exe = _find_installed_command(entry)
        if not cmd or not exe or cmd.lower() in seen:
            continue
        result.append({**entry, "exe_path": exe})
        seen.update(_agent_keys(entry))

    return result


def _confirm_cli_or_panel(
    title: str,
    panel_message: str,
    cli_prompt: str,
    *,
    interactive: bool,
    danger: bool = False,
) -> bool:
    """Confirm either via full-screen TUI panel or inline CLI prompt."""
    if interactive:
        return confirm_panel(title, panel_message, danger=danger)
    answer = Prompt.ask(cli_prompt, choices=["y", "n"], default="n")
    return answer.lower() == "y"


def run_install_agent(
    entry: dict[str, Any],
    config: dict[str, Any],
    config_path: Path,
    *,
    skip_confirm: bool = False,
    interactive: bool = True,
) -> tuple[bool, str]:
    """Install *entry* and sync it into *config*. Returns ``(success, status_note)``."""
    cmd, existing_exe = _find_installed_command(entry)
    name = str(entry.get("name", cmd) or cmd)

    if existing_exe:
        msg = f"{name} ({cmd}) is already installed at {existing_exe}."
        if interactive:
            CONSOLE.clear()
            CONSOLE.print(Panel(
                f"[bold {COLOR_READY}]{msg}[/bold {COLOR_READY}]\n\n"
                f"[{COLOR_MUTED}]Use Update to upgrade installed agents.[/{COLOR_MUTED}]",
                title=f"[bold {COLOR_PRIMARY}]Install agent[/bold {COLOR_PRIMARY}]",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY,
            ))
        else:
            CONSOLE.print(f"[{COLOR_READY}]{msg}[/{COLOR_READY}]")
            CONSOLE.print(f"[{COLOR_MUTED}]Run [bold]agenthub update {cmd}[/bold] to update it.[/{COLOR_MUTED}]")
        if interactive:
            pause()
        return False, f"{name} is already installed."

    install_cmd = resolve_install_command(entry)
    if install_cmd is None:
        instructions = str(entry.get("install_method") or "See tool documentation.")
        if interactive:
            CONSOLE.clear()
            CONSOLE.print(Panel(
                f"[bold white]{name}[/bold white] ([cyan]{cmd}[/cyan]) requires manual installation.\n\n"
                f"[bold white]Instructions:[/bold white]\n"
                f"  [bold yellow]{instructions}[/bold yellow]",
                title=f"[bold {COLOR_ACCENT}]Manual Install Required[/bold {COLOR_ACCENT}]",
                box=box.ROUNDED,
                border_style=COLOR_ACCENT,
            ))
            pause()
        else:
            CONSOLE.print(f"[{COLOR_ACCENT}]Automatic install is not available for {name}.[/{COLOR_ACCENT}]")
            CONSOLE.print(f"[bold white]Instructions:[/bold white] [yellow]{instructions}[/yellow]")
        return False, f"Manual install required for {name}."

    if not skip_confirm:
        confirmed = _confirm_cli_or_panel(
            "Install agent?",
            f"Install [bold white]{name}[/bold white] ([cyan]{cmd}[/cyan])?\n\n"
            f"Command: [bold yellow]{install_cmd}[/bold yellow]",
            f"Install [bold white]{name}[/bold white] ([cyan]{cmd}[/cyan]) using `[yellow]{install_cmd}[/yellow]`?",
            interactive=interactive,
        )
        if not confirmed:
            if not interactive:
                CONSOLE.print(f"[{COLOR_MUTED}]Installation cancelled.[/{COLOR_MUTED}]")
            return False, "Installation cancelled."

    if interactive:
        CONSOLE.clear()
    CONSOLE.print(Panel(
        f"[bold {COLOR_PRIMARY}]Installing {name}...[/bold {COLOR_PRIMARY}]\n"
        f"Command: [bold yellow]{install_cmd}[/bold yellow]",
        title=f"[bold {COLOR_PRIMARY}]AgentHub Installer[/bold {COLOR_PRIMARY}]",
        box=box.ROUNDED,
        border_style=COLOR_PRIMARY,
    ))

    try:
        proc = subprocess.run(install_cmd, cwd=os.getcwd(), shell=True)
        ok = proc.returncode == 0
    except Exception as exc:
        ok = False
        CONSOLE.print(f"[{COLOR_MISSING}]Error running installer: {exc}[/{COLOR_MISSING}]")

    if not ok:
        CONSOLE.print(f"\n[{COLOR_MISSING}]✗ Installation failed for {name}.[/{COLOR_MISSING}]")
        if interactive:
            pause()
        return False, f"Failed to install {name}."

    ensure_search_path()
    for key in _agent_keys(entry):
        set_agent_hidden(config, key, False)

    config, _added = sync_config(config, config_path, announce=False)
    save_config(config, config_path, quiet=True)

    resolved_cmd, exe = _find_installed_command(entry)
    if exe:
        ver = get_version(resolved_cmd)
        CONSOLE.print(
            f"\n[{COLOR_READY}]✓ Installed {name} ({ver}) at {exe}[/{COLOR_READY}]"
        )
        if interactive:
            pause()
        return True, f"✓ Installed {name} ({ver})"

    CONSOLE.print(
        f"\n[{COLOR_ACCENT}]✓ Installer finished, but '{cmd}' was not found on PATH yet. "
        f"Restart your terminal if needed.[/{COLOR_ACCENT}]"
    )
    if interactive:
        pause()
    return True, f"✓ Ran installer for {name}"


def run_uninstall_agent(
    entry: dict[str, Any],
    config: dict[str, Any],
    config_path: Path,
    *,
    skip_confirm: bool = False,
    interactive: bool = True,
) -> tuple[bool, str]:
    """Uninstall *entry* from the system and clean it from *config*. Returns ``(success, status_note)``."""
    cmd, exe = _find_installed_command(entry)
    name = str(entry.get("name", cmd) or cmd)

    if not exe:
        msg = f"{name} ({cmd}) is not installed or not found on PATH."
        if interactive:
            CONSOLE.clear()
            CONSOLE.print(Panel(
                f"[{COLOR_MISSING}]{msg}[/{COLOR_MISSING}]\n\n"
                f"[{COLOR_MUTED}]Use 'Remove agent' in Settings to remove missing entries from configuration.[/{COLOR_MUTED}]",
                title=f"[bold {COLOR_PRIMARY}]Uninstall agent[/bold {COLOR_PRIMARY}]",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY,
            ))
            pause()
        else:
            CONSOLE.print(f"[{COLOR_MISSING}]{msg}[/{COLOR_MISSING}]")
        return False, f"{name} is not installed."

    uninstall_cmd = resolve_uninstall_command({**entry, "command": cmd, "exe_path": exe})
    if uninstall_cmd is None:
        if interactive:
            CONSOLE.clear()
            CONSOLE.print(Panel(
                f"[bold white]{name}[/bold white] ([cyan]{cmd}[/cyan]) does not have an automatic uninstall command.\n\n"
                f"[bold white]Binary path:[/bold white] [dim]{exe}[/dim]\n"
                f"[{COLOR_MUTED}]Uninstall it using its native installer or system settings, "
                f"or use 'Remove agent' in Settings to remove it from AgentHub.[/{COLOR_MUTED}]",
                title=f"[bold {COLOR_ACCENT}]Manual Uninstall Required[/bold {COLOR_ACCENT}]",
                box=box.ROUNDED,
                border_style=COLOR_ACCENT,
            ))
            pause()
        else:
            CONSOLE.print(f"[{COLOR_ACCENT}]Automatic uninstall is not available for {name}.[/{COLOR_ACCENT}]")
            CONSOLE.print(f"[bold white]Binary path:[/bold white] {exe}")
            CONSOLE.print(f"[{COLOR_MUTED}]Use [bold]agenthub remove {cmd}[/bold] to remove it from configuration only.[/{COLOR_MUTED}]")
        return False, f"Manual uninstall required for {name}."

    if not skip_confirm:
        confirmed = _confirm_cli_or_panel(
            "Uninstall agent?",
            f"Uninstall [bold white]{name}[/bold white] ([cyan]{cmd}[/cyan]) from your system?\n\n"
            f"Command: [bold yellow]{uninstall_cmd}[/bold yellow]\n\n"
            f"[{COLOR_MUTED}]This also removes {name} from AgentHub's configuration. "
            f"User config directories are left untouched.[/{COLOR_MUTED}]",
            f"Uninstall [bold white]{name}[/bold white] ([cyan]{cmd}[/cyan]) using `[yellow]{uninstall_cmd}[/yellow]`?",
            interactive=interactive,
            danger=True,
        )
        if not confirmed:
            if not interactive:
                CONSOLE.print(f"[{COLOR_MUTED}]Uninstall cancelled.[/{COLOR_MUTED}]")
            return False, "Uninstall cancelled."

    if interactive:
        CONSOLE.clear()
    CONSOLE.print(Panel(
        f"[bold {COLOR_MISSING}]Uninstalling {name}...[/bold {COLOR_MISSING}]\n"
        f"Command: [bold yellow]{uninstall_cmd}[/bold yellow]",
        title=f"[bold {COLOR_MISSING}]AgentHub Uninstaller[/bold {COLOR_MISSING}]",
        box=box.ROUNDED,
        border_style=COLOR_MISSING,
    ))

    try:
        proc = subprocess.run(uninstall_cmd, cwd=os.getcwd(), shell=True)
        ok = proc.returncode == 0
    except Exception as exc:
        ok = False
        CONSOLE.print(f"[{COLOR_MISSING}]Error running uninstaller: {exc}[/{COLOR_MISSING}]")

    if not ok:
        CONSOLE.print(f"\n[{COLOR_MISSING}]✗ Uninstall failed for {name}.[/{COLOR_MISSING}]")
        if interactive:
            pause()
        return False, f"Failed to uninstall {name}."

    keys = _agent_keys(entry) | {cmd.lower()}
    config["agents"] = [
        a for a in config.get("agents", [])
        if str(a.get("command", "")).strip().lower() not in keys
    ]

    _still_cmd, still_exe = _find_installed_command(entry)
    if still_exe:
        set_agent_hidden(config, cmd, True)
        CONSOLE.print(
            f"\n[{COLOR_ACCENT}]✓ Uninstaller finished, but '{cmd}' is still present at {still_exe}. "
            f"Removed from AgentHub and added to ignored list.[/{COLOR_ACCENT}]"
        )
    else:
        for key in keys:
            set_agent_hidden(config, key, False)
        CONSOLE.print(
            f"\n[{COLOR_READY}]✓ Uninstalled {name} ({cmd}) and removed from configuration.[/{COLOR_READY}]"
        )
        CONSOLE.print(f"[{COLOR_MUTED}]User configuration files were left untouched.[/{COLOR_MUTED}]")

    save_config(config, config_path, quiet=True)
    if interactive:
        pause()
    return True, f"✓ Uninstalled {name} ({cmd})"


def install_agent_wizard(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Interactive keyboard-driven menu to install an agent."""
    status_note = ""
    while True:
        candidates = installable_agents(config)
        if not candidates:
            CONSOLE.clear()
            message = "[bold white]All known catalog and configured agents are already installed.[/bold white]"
            if status_note:
                message = f"{status_note}\n\n{message}"
            CONSOLE.print(Panel(
                message,
                title=f"[bold {COLOR_PRIMARY}]Install agent[/bold {COLOR_PRIMARY}]",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY,
            ))
            pause()
            return config

        options: list[tuple[str, str, str]] = []
        for idx, entry in enumerate(candidates):
            cmd = str(entry.get("command", "")).strip()
            name = str(entry.get("name", cmd) or cmd)
            install_cmd = resolve_install_command(entry)
            hint = f"{cmd} · {install_cmd}" if install_cmd else f"{cmd} · manual install"
            options.append((f"idx:{idx}", name, hint))
        options.append(("back", "Back", ""))

        choice = pick_from_menu(
            "Install agent",
            options,
            subtitle=status_note or "Select an agent to install",
        )
        if choice == "back":
            return config

        idx = int(choice.split(":", 1)[1])
        _ok, status_note = run_install_agent(candidates[idx], config, config_path, interactive=True)


def uninstall_agent_wizard(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Interactive keyboard-driven menu to uninstall an installed agent."""
    status_note = ""
    while True:
        candidates = uninstallable_agents(config)
        if not candidates:
            CONSOLE.clear()
            message = "[bold white]No installed agents found to uninstall.[/bold white]"
            if status_note:
                message = f"{status_note}\n\n{message}"
            CONSOLE.print(Panel(
                message,
                title=f"[bold {COLOR_PRIMARY}]Uninstall agent[/bold {COLOR_PRIMARY}]",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY,
            ))
            pause()
            return config

        options: list[tuple[str, str, str]] = []
        for idx, entry in enumerate(candidates):
            cmd = str(entry.get("command", "")).strip()
            name = str(entry.get("name", cmd) or cmd)
            uninstall_cmd = resolve_uninstall_command(entry)
            hint = f"{cmd} · {uninstall_cmd}" if uninstall_cmd else f"{cmd} · manual uninstall"
            options.append((f"idx:{idx}", name, hint))
        options.append(("back", "Back", ""))

        choice = pick_from_menu(
            "Uninstall agent",
            options,
            subtitle=status_note or "Select an installed agent to uninstall from your system",
        )
        if choice == "back":
            return config

        idx = int(choice.split(":", 1)[1])
        _ok, status_note = run_uninstall_agent(candidates[idx], config, config_path, interactive=True)


# ---------------------------------------------------------------------------
# Settings & Configuration Sub-Menu
# ---------------------------------------------------------------------------

def settings_menu(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Simplified settings screen using the shared keyboard-driven menu."""
    while True:
        agents = detect_agents(config)
        hidden = hidden_commands(config)
        configured_count = len(config.get("agents", []))

        choice = pick_from_menu(
            "Settings",
            [
                ("details", "Agent details", f"{len(agents)} visible"),
                ("visibility", "Show / hide agents", f"{len(hidden)} hidden"),
                ("install", "Install agent", ""),
                ("uninstall", "Uninstall agent", "system + config"),
                ("remove", "Remove agent", f"{configured_count} configured · config only"),
                ("open", "Open config file", ""),
                ("reset", "Reset & re-detect", "clears hidden list"),
                ("back", "Back", ""),
            ],
            subtitle=f"Config: {config_path}",
        )

        if choice == "back":
            return config

        if choice == "details":
            show_agent_details(agents)
        elif choice == "visibility":
            config = manage_visibility(config, config_path)
        elif choice == "install":
            config = install_agent_wizard(config, config_path)
        elif choice == "uninstall":
            config = uninstall_agent_wizard(config, config_path)
        elif choice == "remove":
            config = remove_agent_wizard(config, config_path)
        elif choice == "open":
            open_config_file(config_path)
        elif choice == "reset":
            if confirm_panel(
                "Reset configuration?",
                "This clears the agent list and the hidden list.\n"
                "Installed agents are detected again on the next sync.",
                danger=True,
            ):
                config = default_config()
                save_config(config, config_path, quiet=True)
                config, _added = sync_config(config, config_path)
                CONSOLE.clear()
                CONSOLE.print(f"[{COLOR_READY}]✓ Configuration reset and re-detected.[/{COLOR_READY}]")
                pause()


def manage_visibility(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Toggle which agents appear in AgentHub. Hidden agents survive auto-sync."""
    while True:
        hidden = hidden_commands(config)
        found, _missing = discover_agents()

        entries: dict[str, dict[str, Any]] = {}
        for agent in config.get("agents", []):
            command = str(agent.get("command", "")).strip().lower()
            if command:
                entries[command] = agent
        for agent in found:
            command = str(agent.get("command", "")).strip().lower()
            entries.setdefault(command, agent)

        if not entries:
            CONSOLE.clear()
            CONSOLE.print(Panel(
                f"[bold white]No agents detected yet.[/bold white]\n\n"
                f"[{COLOR_MUTED}]Install an agent CLI and run sync, then come back here.[/{COLOR_MUTED}]",
                title=f"[bold {COLOR_PRIMARY}]Show / hide agents[/bold {COLOR_PRIMARY}]",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY,
            ))
            pause()
            return config

        options: list[tuple[str, str, str]] = []
        for command in sorted(entries, key=lambda c: str(entries[c].get("name", c)).lower()):
            entry = entries[command]
            state = "hidden" if command in hidden else "visible"
            installed = "installed" if find_executable(command) else "not installed"
            options.append((command, str(entry.get("name", command)), f"{state} · {installed}"))
        options.append(("back", "Back", ""))

        choice = pick_from_menu(
            "Show / hide agents",
            options,
            subtitle="Enter toggles an agent · hidden agents are skipped by auto-sync",
        )

        if choice == "back":
            return config

        was_hidden = choice in hidden
        set_agent_hidden(config, choice, not was_hidden)
        save_config(config, config_path, quiet=True)
        if was_hidden:
            configured_cmds = {
                str(a.get("command", "")).strip().lower()
                for a in config.get("agents", [])
            }
            if choice not in configured_cmds:
                config, _added = sync_config(config, config_path)


def remove_agent_wizard(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Interactive keyboard-driven flow to remove an agent from configuration."""
    status_note = ""
    while True:
        configured = config.get("agents", [])
        if not configured:
            CONSOLE.clear()
            message = "[bold white]No agents configured.[/bold white]"
            if status_note:
                message = f"{status_note}\n\n{message}"
            CONSOLE.print(Panel(
                message,
                title=f"[bold {COLOR_PRIMARY}]Remove agent[/bold {COLOR_PRIMARY}]",
                box=box.ROUNDED,
                border_style=COLOR_PRIMARY,
            ))
            pause()
            return config

        hidden = hidden_commands(config)
        options: list[tuple[str, str, str]] = []
        for idx, entry in enumerate(configured):
            cmd = str(entry.get("command", "")).strip()
            name = str(entry.get("name", cmd) or cmd)
            installed = "installed" if find_executable(cmd) else "not installed"
            hint = f"{cmd} · {installed}"
            if cmd.lower() in hidden:
                hint += " · hidden"
            options.append((f"idx:{idx}", name, hint))
        options.append(("back", "Back", ""))

        subtitle = status_note or "Select an agent to remove from AgentHub configuration"
        choice = pick_from_menu(
            "Remove agent",
            options,
            subtitle=subtitle,
        )

        if choice == "back":
            return config

        idx = int(choice.split(":", 1)[1])
        target = configured[idx]
        target_name = str(target.get("name", target.get("command", "")))
        target_cmd = str(target.get("command", ""))

        if confirm_panel(
            "Remove agent?",
            f"Remove [bold white]{target_name}[/bold white] ([cyan]{target_cmd}[/cyan]) from AgentHub?\n\n"
            f"[{COLOR_MUTED}]Only removes the entry from your configuration; "
            f"installed binaries on disk are not deleted.[/{COLOR_MUTED}]",
            danger=True,
        ):
            removed, ignored_added = remove_agent_from_config(config, idx)
            save_config(config, config_path, quiet=True)
            note = f"✓ Removed {removed.get('name', target_cmd)} ({removed.get('command', '')})"
            if ignored_added:
                note += " · added to ignored list"
            status_note = note
        else:
            status_note = "Removal cancelled."


def show_agent_details(agents: list[dict[str, Any]]) -> None:
    """Detailed card for every agent."""
    CONSOLE.clear()
    CONSOLE.print(f"[bold {COLOR_PRIMARY}]Configured Agent Specifications[/bold {COLOR_PRIMARY}]\n")
    for a in agents:
        status = f"[{COLOR_READY}]installed[/{COLOR_READY}]" if a["installed"] else f"[{COLOR_MISSING}]missing[/{COLOR_MISSING}]"
        uninstall_display = a.get("uninstall_method") or resolve_uninstall_command(a) or "—"
        lines = [
            f"[bold white]Command:[/]     [cyan]{a['command']}[/cyan]",
            f"[bold white]Status:[/]      {status}",
            f"[bold white]Version:[/]     {a['version']}",
            f"[bold white]Path:[/]        {a['exe_path']}",
            f"[bold white]Description:[/] {a.get('description', '—')}",
            f"[bold white]Install:[/]     [yellow]{a.get('install_method', '—')}[/yellow]",
            f"[bold white]Update:[/]      [yellow]{a.get('update_method', '—')}[/yellow]",
            f"[bold white]Uninstall:[/]   [yellow]{uninstall_display}[/yellow]",
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
    pause()


def add_agent_wizard(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Interactive wizard to register a new agent."""
    CONSOLE.print(f"\n[bold {COLOR_PRIMARY}]Register New AI CLI Agent[/bold {COLOR_PRIMARY}]\n")
    name = Prompt.ask("  Agent display name (e.g. Aider)")
    command = Prompt.ask("  CLI command (e.g. aider)")
    description = Prompt.ask("  Description", default="AI pair programmer in the terminal")
    install_method = Prompt.ask("  Install command", default=f"pip install {command}")
    update_method = Prompt.ask("  Update command", default=f"pip install --upgrade {command}")
    default_uninstall = _derive_uninstall_from_install(install_method) or ""
    uninstall_method = Prompt.ask("  Uninstall command (optional)", default=default_uninstall)
    cfg_loc = Prompt.ask("  Config location path (optional)", default="")

    new_agent = {
        "name": name,
        "command": command,
        "description": description,
        "install_method": install_method,
        "update_method": update_method,
        "uninstall_method": uninstall_method,
        "config_locations": [cfg_loc] if cfg_loc else [],
        "source": "user",
    }

    config.setdefault("agents", []).append(new_agent)
    set_agent_hidden(config, command, False)
    save_config(config, config_path)
    CONSOLE.print(f"[{COLOR_READY}]✓ Added {name} successfully![/{COLOR_READY}]")
    Prompt.ask("\nPress Enter to continue", default="")
    return config


def open_config_file(config_path: Path, *, pause_return: bool = True) -> None:
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
    if pause_return:
        pause()

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
  agenthub install claude  # Install an AI CLI agent
  agenthub uninstall claude # Uninstall an AI CLI agent from your system
  agenthub update          # Check and update installed agents
  agenthub add             # Add a new CLI agent interactively
  agenthub remove codex    # Remove an agent from configuration
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

    # install
    p_install = subparsers.add_parser(
        "install",
        aliases=["i"],
        help="Install an AI CLI agent",
    )
    p_install.add_argument(
        "agent",
        nargs="?",
        help="Optional agent command or name to install (e.g. claude, aider)",
    )
    p_install.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # uninstall
    p_uninstall = subparsers.add_parser(
        "uninstall",
        help="Uninstall an installed AI CLI agent and remove it from configuration",
    )
    p_uninstall.add_argument(
        "agent",
        nargs="?",
        help="Optional agent command, name, or number to uninstall (e.g. codex, 1)",
    )
    p_uninstall.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # update
    p_update = subparsers.add_parser("update", help="Update installed CLI agents")
    p_update.add_argument("agent", nargs="?", help="Optional specific agent command or name to update")

    # add
    subparsers.add_parser("add", help="Add a new CLI agent configuration")

    # remove
    p_remove = subparsers.add_parser(
        "remove",
        aliases=["rm", "delete"],
        help="Remove an agent from AgentHub configuration",
    )
    p_remove.add_argument(
        "agent",
        nargs="?",
        help="Optional agent command, name, or number to remove (e.g. codex, 1)",
    )
    p_remove.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

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

    if args.subcommand in ("install", "i"):
        if not args.agent:
            install_agent_wizard(config, config_path)
            return

        missing_candidates = installable_agents(config)
        _idx, entry, err = _resolve_entry_in_list(
            missing_candidates,
            args.agent,
            not_found_message=f"Agent '{args.agent}' not found in catalog or configuration.",
        )
        if entry is None:
            installed_candidates = uninstallable_agents(config)
            _i2, inst_entry, err2 = _resolve_entry_in_list(
                installed_candidates,
                args.agent,
                index_entries=agents,
            )
            if inst_entry is not None:
                run_install_agent(inst_entry, config, config_path, skip_confirm=args.yes, interactive=False)
                return
            CONSOLE.print(f"[{COLOR_MISSING}]{err or err2}[/{COLOR_MISSING}]")
            CONSOLE.print("Run [bold cyan]agenthub doctor[/bold cyan] to see known catalog agents.")
            sys.exit(1)

        ok, note = run_install_agent(entry, config, config_path, skip_confirm=args.yes, interactive=False)
        if not ok and note.startswith(("Failed", "Manual")):
            sys.exit(1)
        return

    if args.subcommand == "uninstall":
        if not args.agent:
            uninstall_agent_wizard(config, config_path)
            return

        installed_candidates = uninstallable_agents(config)
        _idx, entry, err = _resolve_entry_in_list(
            installed_candidates,
            args.agent,
            index_entries=agents,
            not_found_message=f"Installed agent '{args.agent}' not found.",
        )
        if entry is None:
            CONSOLE.print(f"[{COLOR_MISSING}]{err}[/{COLOR_MISSING}]")
            CONSOLE.print("Use [bold cyan]agenthub list[/bold cyan] to see installed agents.")
            sys.exit(1)

        ok, note = run_uninstall_agent(entry, config, config_path, skip_confirm=args.yes, interactive=False)
        if not ok and note.startswith(("Failed", "Manual")):
            sys.exit(1)
        return

    if args.subcommand == "update":
        if args.agent:
            target = args.agent.strip().lower()
            matched = [a for a in agents if a["command"].lower() == target or a["name"].lower() == target]
            if matched:
                update_agents_wizard(matched, prompt_return=False)
            else:
                CONSOLE.print(f"[{COLOR_MISSING}]Agent '{args.agent}' not found.[/{COLOR_MISSING}]")
                sys.exit(1)
        else:
            update_agents_wizard(agents, prompt_return=False)
        return

    if args.subcommand == "add":
        add_agent_wizard(config, config_path)
        return

    if args.subcommand in ("remove", "rm", "delete"):
        if not args.agent:
            remove_agent_wizard(config, config_path)
            return

        idx, entry, err = resolve_agent_for_removal(config, args.agent, visible_agents=agents)
        if err or idx is None or entry is None:
            CONSOLE.print(f"[{COLOR_MISSING}]{err or f'Agent {args.agent!r} not found.'}[/{COLOR_MISSING}]")
            CONSOLE.print("Use [bold cyan]agenthub list[/bold cyan] to see available agents.")
            sys.exit(1)

        target_name = str(entry.get("name", entry.get("command", "")))
        target_cmd = str(entry.get("command", ""))
        if not args.yes:
            answer = Prompt.ask(
                f"Remove [bold white]{target_name}[/bold white] ([cyan]{target_cmd}[/cyan]) from AgentHub?",
                choices=["y", "n"],
                default="n",
            )
            if answer.lower() != "y":
                CONSOLE.print(f"[{COLOR_MUTED}]Removal cancelled.[/{COLOR_MUTED}]")
                return

        removed, ignored_added = remove_agent_from_config(config, idx)
        save_config(config, config_path, quiet=True)
        CONSOLE.print(
            f"[{COLOR_READY}]✓ Removed {removed.get('name', target_cmd)} "
            f"({removed.get('command', '')}) from configuration.[/{COLOR_READY}]"
        )
        if ignored_added:
            CONSOLE.print(
                f"[{COLOR_MUTED}]Added '{removed.get('command', '')}' to ignored list "
                f"so auto-sync will not re-add it.[/{COLOR_MUTED}]"
            )
        return

    if args.subcommand == "config":
        if args.path:
            print(str(config_path))
            return
        if args.open:
            open_config_file(config_path, pause_return=False)
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
            pause()
        elif action == "install":
            config = install_agent_wizard(config, config_path)
            agents = detect_agents(config)
        elif action == "doctor":
            run_doctor(agents, config_path, interactive=True)
        elif action == "update":
            update_agents_wizard(agents)
            config, config_path = load_config()
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
