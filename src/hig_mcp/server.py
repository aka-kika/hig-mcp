"""hig_mcp server.

Four tools:
  - hig_get_tokens        : curated design tokens by category (offline, deterministic)
  - hig_check_liquid_glass : Liquid Glass constraint engine + fallback guidance (offline)
  - hig_swiftui           : HIG component -> SwiftUI API + token refs (offline)
  - hig_fetch             : live HIG prose as Markdown via sosumi.ai (network)

Design stance: the prose-retrieval problem is already solved well by sosumi.ai
(and apple-docs-mcp), so this server does NOT rebuild DocC extraction. It owns
the structured layer those tools don't serve, and delegates prose to sosumi.
"""

import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from mcp.server.mcpserver import MCPServer

from . import tokens

# --- Constants -------------------------------------------------------------

SOSUMI_BASE = os.environ.get("HIG_SOSUMI_BASE", "https://sosumi.ai").rstrip("/")
APPLE_HIG_BASE = "https://developer.apple.com"
HTTP_TIMEOUT = 20.0
USER_AGENT = "hig-mcp/0.1 (+https://github.com/aka-kika/hig-mcp)"

CALL_LOG = Path(
    os.environ.get("HIG_MCP_CALL_LOG")
    or Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    / "hig-mcp" / "calls.jsonl"
)

async def _count_tool_calls(ctx, call_next):
    """mcp 2.x server middleware: one JSONL line per tool call (ts, tool, client)."""
    if ctx.method == "tools/call":
        try:
            try:
                cp = ctx.session.client_params
                info = getattr(cp, "client_info", None) or getattr(cp, "clientInfo")
                client, client_version = info.name, info.version
            except Exception:  # noqa: BLE001 - client identity is best-effort
                client, client_version = "unknown", None
            CALL_LOG.parent.mkdir(parents=True, exist_ok=True)
            with CALL_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "tool": (ctx.params or {}).get("name", "?"),
                    "client": client,
                    "client_version": client_version,
                }) + "\n")
        except Exception:  # noqa: BLE001
            pass  # counting must never break a tool call
    return await call_next(ctx)


mcp = MCPServer("hig_mcp", middleware=[_count_tool_calls])


# --- Shared helpers --------------------------------------------------------

def _normalize_path(path: str) -> str:
    """Accept a full Apple URL, a /design/... path, or a bare slug."""
    p = path.strip()
    if p.startswith(APPLE_HIG_BASE):
        p = p[len(APPLE_HIG_BASE):]
    if not p.startswith("/"):
        # bare slug -> assume HIG section
        p = "/design/human-interface-guidelines/" + p
    return p


def _handle_http_error(e: Exception, path: str) -> dict[str, Any]:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 404:
            return {
                "status": "error",
                "error": f"Not found at sosumi for path '{path}'. Check the HIG slug "
                         "(e.g. /design/human-interface-guidelines/materials).",
            }
        return {"status": "error", "error": f"sosumi returned HTTP {code} for '{path}'."}
    if isinstance(e, httpx.TimeoutException):
        return {"status": "error", "error": "Request to sosumi timed out. Try again."}
    return {"status": "error", "error": f"Unexpected error: {type(e).__name__}: {e}"}


# --- Tool inputs -----------------------------------------------------------

class TokenCategory(str, Enum):
    color = "color"
    typography = "typography"
    materials = "materials"
    layout = "layout"
    swiftui = "swiftui"
    sf_symbols = "sf_symbols"
    all = "all"


class GetTokensInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    category: TokenCategory = Field(
        default=TokenCategory.all,
        description="Which token category to return: color, typography, materials, layout, swiftui, sf_symbols, or all.",
    )


class LiquidGlassInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    context: str = Field(
        ...,
        description="Where Liquid Glass will be used, e.g. 'tab bar background', 'card over a photo', 'sidebar'.",
        min_length=2, max_length=200,
    )
    platform: str = Field(
        default="iphone",
        description="'iphone' or 'ipad_mac' — selects the blur budget.",
    )


class SwiftUIInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    component: Optional[str] = Field(
        default=None,
        description="HIG component name (e.g. button, text_field, toggle, picker, alert, progress; 14 total). Omit to list all.",
        max_length=60,
    )


class FetchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(
        ...,
        description="HIG path, slug, or full URL — e.g. 'materials', "
                    "'/design/human-interface-guidelines/color', or a developer.apple.com URL.",
        min_length=2, max_length=300,
    )


# --- Tools -----------------------------------------------------------------

@mcp.tool(
    name="hig_get_tokens",
    annotations={
        "title": "Get HIG Design Tokens",
        "readOnlyHint": True, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": False,
    },
    structured_output=True,
)
async def hig_get_tokens(params: GetTokensInput) -> dict[str, Any]:
    """Return curated Apple HIG design tokens for a category.

    Tokens carry provenance: 'src' tags each value (apple-system, apple-hig,
    figma-effect, community-bestpractice, convention, wcag-aa) and 'verify':true
    flags values to confirm against the current OS. Semantic colors are dynamic —
    reference by name, never hardcode hex.

    Args:
        params.category: one of color | typography | materials | layout | swiftui | sf_symbols | all

    Returns:
        dict: the requested token category (or all categories), as structured data.
    """
    if params.category == TokenCategory.all:
        return tokens.load_all()
    return tokens.load_category(params.category.value)


@mcp.tool(
    name="hig_check_liquid_glass",
    annotations={
        "title": "Check Liquid Glass Constraints",
        "readOnlyHint": True, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": False,
    },
    structured_output=True,
)
async def hig_check_liquid_glass(params: LiquidGlassInput) -> dict[str, Any]:
    """Return the Liquid Glass guardrails for a given usage context.

    Surfaces the budgets agents routinely get wrong — blur radius cap, max
    compositing layers, contrast-after-blur, depth/frost ranges, and the
    required reduced-transparency fallback — with provenance so you know which
    numbers are Apple's vs. community/Figma-derived.

    Args:
        params.context: where the material is applied (free text)
        params.platform: 'iphone' or 'ipad_mac' (selects blur budget)

    Returns:
        dict: applicable rules, the platform blur cap, and a checklist.
    """
    materials = tokens.load_category("materials")
    lg = materials["liquid_glass"]
    plat = "ipad_mac" if params.platform.lower() in ("ipad", "mac", "ipad_mac") else "iphone"
    blur_cap = lg["blur_radius_max_px"][plat]

    checklist = [
        f"Blur radius \u2264 {blur_cap}px on {plat} ({lg['blur_radius_max_px']['src']}, verify).",
        f"\u2264 {lg['max_compositing_layers']['value']} compositing layers on this screen.",
        f"Text contrast \u2265 {lg['min_text_contrast']['ratio']} measured AFTER blur, against the real backdrop.",
        "Keep text/symbols on a layer above the glass; use vibrancy, not raw color.",
        f"Provide a {lg['fallback']['trigger']} fallback: {lg['fallback']['rule']}",
        "If the backdrop is busy/high-contrast (e.g. a photo), prefer a heavier system material over custom glass.",
    ]
    return {
        "status": "ok",
        "context": params.context,
        "platform": plat,
        "blur_radius_max_px": blur_cap,
        "rules": lg,
        "checklist": checklist,
        "confirm_with": "hig_fetch('materials') for the current Apple prose.",
    }


@mcp.tool(
    name="hig_swiftui",
    annotations={
        "title": "HIG Component to SwiftUI",
        "readOnlyHint": True, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": False,
    },
    structured_output=True,
)
async def hig_swiftui(params: SwiftUIInput) -> dict[str, Any]:
    """Map a HIG component to its SwiftUI API plus the token references to apply.

    Stable APIs are confident; Liquid-Glass-era modifiers are flagged verify:true
    because names shift between betas — confirm via hig_fetch or Xcode before shipping.

    Args:
        params.component: button | navigation_bar | tab_bar | list | sheet (omit to list all)

    Returns:
        dict: mapping with swiftui API, token refs, hig_path, and verify flags.
    """
    data = tokens.load_category("swiftui")
    components = data["components"]
    if params.component is None:
        return {"status": "ok", "available": list(components), "_meta": data["_meta"]}
    key = params.component.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in components:
        return {
            "status": "error",
            "error": f"No mapping for '{params.component}'. Available: {', '.join(components)}.",
        }
    return {"status": "ok", "component": key, "mapping": components[key]}


@mcp.tool(
    name="hig_fetch",
    annotations={
        "title": "Fetch HIG Prose (via sosumi.ai)",
        "readOnlyHint": True, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": True,
    },
    structured_output=True,
)
async def hig_fetch(params: FetchInput) -> dict[str, Any]:
    """Fetch current HIG prose as clean Markdown via sosumi.ai.

    Thin convenience wrapper so this one server covers both tokens and prose.
    sosumi.ai renders Apple's DocC pages to AI-friendly Markdown. Returned text
    is for grounding only: summarize and cite the canonical Apple URL, do not
    reproduce it wholesale. Override the backend with HIG_SOSUMI_BASE.

    Args:
        params.path: HIG slug, /design/... path, or full developer.apple.com URL.

    Returns:
        dict: markdown content, the sosumi source, and the canonical Apple URL.
    """
    path = _normalize_path(params.path)
    url = f"{SOSUMI_BASE}{path}"
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT, "Accept": "text/markdown, text/plain, */*"},
            timeout=HTTP_TIMEOUT, follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content = resp.text
    except Exception as e:  # noqa: BLE001 - normalized into an actionable message
        return _handle_http_error(e, path)

    return {
        "status": "ok",
        "path": path,
        "source": url,
        "apple_url": f"{APPLE_HIG_BASE}{path}",
        "markdown": content,
        "usage": "Grounding only — summarize and cite apple_url; do not reproduce verbatim.",
    }


def main() -> None:
    """Console entry point: run over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
