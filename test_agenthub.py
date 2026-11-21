"""Validation and smoke tests for AgentHub."""
import os
import sys

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
    load_config,
    detect_agents,
    show_banner,
    show_status_table,
    build_parser,
    get_config_path,
    VERSION,
)

print(f"Testing AgentHub v{VERSION}...")

# 1. Config path & loading
cfg, cfg_path = load_config()
print(f"Active config path: {cfg_path} (exists={cfg_path.exists()})")
assert "agents" in cfg, "Config missing 'agents' key"
assert len(cfg["agents"]) > 0, "No agents configured"

# 2. Agent detection
agents = detect_agents(cfg)
assert len(agents) == len(cfg["agents"]), "Enriched agents count mismatch"
print(f"Detected {len(agents)} agents:")
for a in agents:
    status_str = "READY" if a["installed"] else "MISSING"
    print(f"  • {a['name']:<16} [{status_str:<7}] cmd='{a['command']}' ver='{a['version']}'")

# 3. Banner & Table rendering
print("\n--- Banner Rendering ---")
show_banner(agents, cfg_path)

print("\n--- Status Table Rendering ---")
show_status_table(agents)

# 4. Parser validation
parser = build_parser()
args = parser.parse_args(["list"])
assert args.subcommand == "list"

args = parser.parse_args(["launch", "agy"])
assert args.subcommand == "launch"
assert args.agent == "agy"

args = parser.parse_args(["doctor"])
assert args.subcommand == "doctor"

print("\n✓ All tests and validations passed successfully!")
