"""Loads the curated token JSON files bundled in the data/ directory."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).parent / "data"

# category name -> filename
CATEGORIES = {
    "color": "color.json",
    "typography": "typography.json",
    "materials": "materials.json",
    "layout": "layout.json",
    "swiftui": "swiftui.json",
    "sf_symbols": "sf_symbols.json",
}


@lru_cache(maxsize=None)
def load_category(category: str) -> Dict[str, Any]:
    """Load one token category from disk (cached). Raises KeyError if unknown."""
    filename = CATEGORIES[category]
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all() -> Dict[str, Any]:
    """Load every token category into a single dict keyed by category name."""
    return {name: load_category(name) for name in CATEGORIES}
