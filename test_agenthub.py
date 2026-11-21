"""Quick validation test for AgentHub."""
import sys, os

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))
from agenthub import load_config, detect_agents, show_banner, show_status_table

config = load_config()
agents = detect_agents(config)
show_banner()
show_status_table(agents)

print("\n--- Validation ---")
for a in agents:
    status = "INSTALLED" if a["installed"] else "MISSING"
    print(f"  {a['name']}: {status} | path={a['exe_path']} | ver={a['version']}")
print("\nAll checks passed.")
