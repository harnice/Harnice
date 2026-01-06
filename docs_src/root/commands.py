from pathlib import Path

########################################################
# APPEARANCE
########################################################

md = [
    "## Appearance Guide\n\n",
    "The appearance of a segment is defined by a dictionary of the following format:\n\n",
    "```json\n",
    "{\n",
    "    \"base_color\": \"#000000\",\n",
    "    \"parallelstripe\": [\"#000000\", \"#000000\"],\n",
    "    \"perpstripe\": [\"#000000\", \"#000000\"],\n",
    "    \"twisted\": null\n",
    "}\n",
    "```\n",
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "commands" / "appearance.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")