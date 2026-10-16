"""Smoke and data tests: run with `uv run --with pytest pytest`."""

import asyncio
import json
import re
import tomllib
from pathlib import Path

import pytest

from hig_mcp import __version__, server, tokens

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^#[0-9A-F]{6}$")


def run(coro):
    return asyncio.run(coro)


def test_version_matches_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert pyproject["project"]["version"] == __version__


@pytest.mark.parametrize("category", list(tokens.CATEGORIES))
def test_every_category_loads_and_has_checked_date(category):
    data = tokens.load_category(category)
    assert data["_meta"]["category"] == category
    assert "checked" in data["_meta"] or "checked" in json.dumps(data)


def test_colors_are_hex_with_all_four_appearances():
    color = tokens.load_category("color")
    entries = {**color["system"], **{k: v for k, v in color["system_gray_ramp"].items() if k != "note"}}
    assert {"systemMint", "systemCyan", "systemBrown"} <= set(entries)
    for name, v in entries.items():
        for key in ("light", "dark", "light_increased_contrast", "dark_increased_contrast"):
            assert HEX.match(v[key]), (name, key, v[key])


def test_post_wwdc25_blue():
    assert tokens.load_category("color")["system"]["systemBlue"]["light"] == "#0088FF"


def test_materials_use_real_swiftui_names():
    materials = tokens.load_category("materials")
    assert "chromeMaterial" not in json.dumps(materials["system_materials"]["swiftui"])
    assert ".ultraThickMaterial" in materials["system_materials"]["swiftui"]
    assert materials["liquid_glass"]["clear_dimming"]["src"] == "apple-hig"


def test_control_sizes_per_platform():
    sizes = tokens.load_category("layout")["hit_target"]["per_platform"]
    assert sizes["visionos"]["default"] == "60x60"
    assert sizes["macos"]["minimum"] == "20x20"


def test_get_tokens_all():
    out = run(server.hig_get_tokens(server.GetTokensInput()))
    assert set(out) == set(tokens.CATEGORIES)


@pytest.mark.parametrize("platform,cap", [("iphone", 40), ("mac", 60)])
def test_liquid_glass_checklist(platform, cap):
    out = run(server.hig_check_liquid_glass(server.LiquidGlassInput(context="card over a photo", platform=platform)))
    assert out["status"] == "ok" and out["blur_radius_max_px"] == cap
    assert any("35%" in line for line in out["checklist"])


def test_swiftui_mapping_and_unknown():
    listed = run(server.hig_swiftui(server.SwiftUIInput()))
    assert len(listed["available"]) == 14
    ok = run(server.hig_swiftui(server.SwiftUIInput(component="Tab Bar")))
    assert ok["component"] == "tab_bar"
    bad = run(server.hig_swiftui(server.SwiftUIInput(component="carousel")))
    assert bad["status"] == "error"


def test_tools_registered():
    names = {t.name for t in run(server.mcp.list_tools())}
    assert names == {"hig_get_tokens", "hig_check_liquid_glass", "hig_swiftui", "hig_fetch"}
