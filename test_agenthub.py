"""Validation and smoke tests for AgentHub (v1.2 auto-sync)."""
import json
import os
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))

from agenthub import (
    AGENT_CATALOG,
    load_config,
    detect_agents,
    show_banner,
    show_status_table,
    build_parser,
    discover_agents,
    merge_discovered_agents,
    sync_config,
    default_config,
    ensure_search_path,
    hidden_commands,
    set_agent_hidden,
    updatable_agents,
    VERSION,
)

print(f"Testing AgentHub v{VERSION}...")

# ---------------------------------------------------------------------------
# 1. Catalog integrity
# ---------------------------------------------------------------------------
required = {"name", "command", "description", "install_method", "update_method", "config_locations"}
commands = [entry["command"].lower() for entry in AGENT_CATALOG]
assert len(commands) == len(set(commands)), "Duplicate commands in AGENT_CATALOG"
for entry in AGENT_CATALOG:
    missing_keys = required - set(entry)
    assert not missing_keys, f"{entry.get('name')} missing keys: {missing_keys}"
    assert entry["config_locations"], f"{entry.get('name')} has no config_locations"
print(f"✓ Catalog: {len(AGENT_CATALOG)} agents, all commands unique")

# ---------------------------------------------------------------------------
# 2. Merge engine: discovery adds new agents, never clobbers user edits
# ---------------------------------------------------------------------------
user_config = {
    "agents": [
        {
            "name": "My Codex",
            "command": "codex",
            "description": "My custom description",
            "install_method": "custom install",
            "update_method": "custom update",
            "config_locations": ["~/.codex"],
        },
        {
            "name": "Aider",
            "command": "aider",
            "description": "",
            "install_method": "",
            "update_method": "",
            "config_locations": [],
        },
    ]
}
discovered = [
    {
        "name": "Codex CLI",
        "command": "codex",
        "description": "catalog description",
        "install_method": "npm install -g @openai/codex",
        "update_method": "npm update -g @openai/codex",
        "config_locations": ["~/.codex"],
    },
    {
        "name": "Aider",
        "command": "aider",
        "description": "AI pair programming in your terminal",
        "install_method": "pip install aider-chat",
        "update_method": "pip install --upgrade aider-chat",
        "config_locations": ["~/.aider.conf.yml"],
    },
    {
        "name": "Claude Code",
        "command": "claude",
        "description": "Anthropic's agent",
        "install_method": "npm install -g @anthropic-ai/claude-code",
        "update_method": "npm update -g @anthropic-ai/claude-code",
        "config_locations": ["~/.claude"],
    },
]

merged, added, enriched = merge_discovered_agents(user_config, discovered)
by_cmd = {a["command"]: a for a in merged["agents"]}

assert added == ["Claude Code"], f"Unexpected added list: {added}"
assert "Aider" in enriched, f"Expected Aider metadata to be filled, got {enriched}"
assert by_cmd["codex"]["name"] == "My Codex", "User entry was overwritten"
assert by_cmd["codex"]["description"] == "My custom description", "User description was clobbered"
assert by_cmd["aider"]["install_method"] == "pip install aider-chat", "Empty metadata not filled"
assert by_cmd["claude"]["source"] == "catalog", "New entry not tagged as catalog-sourced"

# Idempotent: a second merge must not duplicate anything
merged2, added2, _ = merge_discovered_agents(merged, discovered)
assert added2 == [], f"Second merge added duplicates: {added2}"
assert len(merged2["agents"]) == len(merged["agents"])
print("✓ Merge: adds new, preserves user edits, idempotent")

# ---------------------------------------------------------------------------
# 3. Duplicate display names get disambiguated
# ---------------------------------------------------------------------------
cfg = {"agents": [{"name": "Gemini CLI", "command": "agy"}]}
merged, added, _ = merge_discovered_agents(
    cfg,
    [{
        "name": "Gemini CLI",
        "command": "gemini",
        "description": "",
        "install_method": "",
        "update_method": "",
        "config_locations": [],
    }],
)
assert added == ["Gemini CLI (gemini)"], f"Name collision not handled: {added}"
print("✓ Merge: duplicate names disambiguated")

# ---------------------------------------------------------------------------
# 4. Alias reuse (cursor-agent -> agent)
# ---------------------------------------------------------------------------
cfg = {"agents": [{"name": "Cursor CLI", "command": "agent"}]}
merged, added, _ = merge_discovered_agents(
    cfg,
    [{
        "name": "Cursor CLI",
        "command": "cursor-agent",
        # discover_agents() keeps the catalog's primary command as an alias
        "aliases": ["cursor-agent", "agent"],
        "description": "Cursor agent",
        "install_method": "",
        "update_method": "",
        "config_locations": [],
    }],
)
assert added == [], "Alias created a duplicate entry"
assert len(merged["agents"]) == 1
print("✓ Merge: alias reuses existing entry")

# ---------------------------------------------------------------------------
# 5. Discovery returns found/missing without crashing
# ---------------------------------------------------------------------------
found, missing = discover_agents()
assert len(found) + len(missing) == len(AGENT_CATALOG)
print(f"✓ Discovery: {len(found)} installed, {len(missing)} missing (catalog intact)")

# ---------------------------------------------------------------------------
# 6. sync_config persists to an isolated config file
# ---------------------------------------------------------------------------
tmpdir = Path(tempfile.mkdtemp(prefix="agenthub-test-"))
tmp_cfg = tmpdir / "agents.json"
tmp_cfg.write_text(json.dumps({"agents": []}), encoding="utf-8")

cfg, added_first = sync_config({"agents": []}, tmp_cfg, announce=False)
saved = json.loads(tmp_cfg.read_text(encoding="utf-8"))
assert len(saved["agents"]) == len(found), "sync_config did not persist discovered agents"
assert set(added_first) == {a["name"] for a in found} or not found

cfg2, added_second = sync_config(saved, tmp_cfg, announce=False)
assert added_second == [], "sync_config is not idempotent"
assert len(cfg2["agents"]) == len(saved["agents"])
print(f"✓ sync_config: persisted {len(saved['agents'])} agent(s), idempotent")

# ---------------------------------------------------------------------------
# 7. Hidden agents: survive auto-sync, filtered from detection
# ---------------------------------------------------------------------------
assert default_config() == {"agents": [], "ignored": []}
assert default_config() is not default_config()

cfg = {"agents": [{"name": "Aider", "command": "aider"}], "ignored": []}
set_agent_hidden(cfg, "AIDER", True)
assert hidden_commands(cfg) == {"aider"}
assert detect_agents(cfg) == [], "Hidden agent was not filtered from detection"

merged, added, _ = merge_discovered_agents(
    cfg,
    [{
        "name": "Aider",
        "command": "aider",
        "description": "AI pair programming in your terminal",
        "install_method": "pip install aider-chat",
        "update_method": "pip install --upgrade aider-chat",
        "config_locations": ["~/.aider.conf.yml"],
    }],
)
assert added == [], "Hidden agent was re-added by auto-sync"
assert len(merged["agents"]) == 1, "Hidden agent entry should be preserved, not deleted"

set_agent_hidden(merged, "aider", False)
assert hidden_commands(merged) == set()
assert len(detect_agents(merged)) == 1, "Unhidden agent did not reappear"
print("✓ Hidden agents: filtered, skipped by sync, restorable")

# ---------------------------------------------------------------------------
# 8. Batch update target selection
# ---------------------------------------------------------------------------
candidates = [
    {"name": "A", "command": "a", "installed": True, "update_method": "a --update"},
    {"name": "B", "command": "b", "installed": False, "update_method": "b --update"},
    {"name": "C", "command": "c", "installed": True, "update_method": ""},
]
assert [a["command"] for a in updatable_agents(candidates)] == ["a"]
print("✓ Batch update: only installed agents with update commands")

# ---------------------------------------------------------------------------
# 9. Parser: --no-sync flag and sync subcommand
# ---------------------------------------------------------------------------
parser = build_parser()

args = parser.parse_args(["list"])
assert args.subcommand == "list"
assert args.no_sync is False

args = parser.parse_args(["--no-sync", "list"])
assert args.no_sync is True

args = parser.parse_args(["sync"])
assert args.subcommand == "sync"

args = parser.parse_args(["launch", "codex"])
assert args.subcommand == "launch"
assert args.agent == "codex"

args = parser.parse_args(["doctor"])
assert args.subcommand == "doctor"
print("✓ Parser: sync, --no-sync, launch, doctor")

# ---------------------------------------------------------------------------
# 10. Shared sub-menu + batch update UI (mocked, no real key/command execution)
# ---------------------------------------------------------------------------
import io
import types
import agenthub
from rich.console import Console

_orig_console = agenthub.CONSOLE
_orig_key = agenthub.read_navigation_key
agenthub.CONSOLE = Console(file=io.StringIO(), force_terminal=False, width=100)

try:
    keys = iter(["down", "enter"])
    agenthub.read_navigation_key = lambda: next(keys)
    picked = agenthub.pick_from_menu(
        "Test",
        [("a", "First", ""), ("b", "Second", ""), ("back", "Back", "")],
    )
    assert picked == "b", f"Arrow + Enter navigation failed: {picked}"

    keys = iter(["q"])
    agenthub.read_navigation_key = lambda: next(keys)
    picked = agenthub.pick_from_menu("Test", [("a", "First", "")])
    assert picked == "back", f"q did not go back: {picked}"

    assert agenthub._output_tail("\x1b[31mhello\x1b[0m") == "hello"

    _orig_run = agenthub.subprocess.run
    _orig_confirm = agenthub.confirm_panel
    _orig_pause = agenthub.pause
    executed: list[str] = []

    def fake_run(command, **_kwargs):
        executed.append(command)
        return types.SimpleNamespace(returncode=0, stdout="updated ok", stderr="")

    agenthub.subprocess.run = fake_run
    agenthub.confirm_panel = lambda *_a, **_k: True
    agenthub.pause = lambda *_a, **_k: None

    try:
        agenthub.update_agents_wizard(
            [
                {"name": "A", "command": "a", "installed": True, "version": "1.0", "update_method": "a --update"},
                {"name": "B", "command": "b", "installed": True, "version": "2.0", "update_method": "b --update"},
            ],
            prompt_return=False,
        )
    finally:
        agenthub.subprocess.run = _orig_run
        agenthub.confirm_panel = _orig_confirm
        agenthub.pause = _orig_pause

    assert executed == ["a --update", "b --update"], f"Batch update ran: {executed}"
finally:
    agenthub.CONSOLE = _orig_console
    agenthub.read_navigation_key = _orig_key

print("✓ UI: sub-menu navigation, q-back, ANSI cleanup, one batch update run")

# ---------------------------------------------------------------------------
# 11. Smoke test on the live machine config
# ---------------------------------------------------------------------------
ensure_search_path()
cfg, cfg_path = load_config()
print(f"Active config path: {cfg_path} (exists={cfg_path.exists()})")
assert "agents" in cfg, "Config missing 'agents' key"

agents = detect_agents(cfg)
print(f"Detected {len(agents)} configured agents:")
for a in agents:
    status_str = "READY" if a["installed"] else "MISSING"
    print(f"  • {a['name']:<16} [{status_str:<7}] cmd='{a['command']}' ver='{a['version']}'")

print("\n--- Banner Rendering ---")
show_banner(agents, cfg_path)

print("\n--- Status Table Rendering ---")
show_status_table(agents)

print("\n--- Empty State Rendering ---")
show_status_table([])

print("\n✓ All tests and validations passed successfully!")
