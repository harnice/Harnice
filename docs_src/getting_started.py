from pathlib import Path

# ========================================================
# GIT INTEGRATION
# ========================================================

md = ["# Integrating Harnice with Git"]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "getting_started" / "_git_integration.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")
