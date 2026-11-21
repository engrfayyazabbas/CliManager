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
# 7. Default config is empty (auto-sync fills it) and independent copies
# ---------------------------------------------------------------------------
assert default_config() == {"agents": []}
assert default_config() is not default_config()
print("✓ Default config: empty starter, fresh copy")

# ---------------------------------------------------------------------------
# 8. Parser: --no-sync flag and sync subcommand
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
# 9. Smoke test on the live machine config
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
