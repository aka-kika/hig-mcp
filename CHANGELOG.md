# Changelog

## 0.3.0 — 2026-10-17

A refresh release: every curated value was checked against Apple's live HIG and the SwiftUI docs for OS 26 (shipping) and the OS 27 betas on 2026-10-17. It also ships the mcp SDK 2.0 migration that was tagged 0.2.0 in the repo but never released.

Why 0.3.0 and not 0.2.1: the token data gains new fields and new entries (a minor change in 0.x terms), and the dependency moves to `mcp` 2.x. 0.2.0 was never on PyPI, so it is folded in here.

**Checked and unchanged**
- All system color values (light and dark) and the gray ramp still match the HIG table (last Apple change 2025-06-09).
- iOS and macOS type sizes still match.
- Every SwiftUI Liquid Glass name still exists in OS 27 and none is deprecated: `glassEffect(_:in:)`, `Glass.regular/.clear`, `.interactive()`, `.tint(_:)`, `GlassEffectContainer`, `glassEffectID(_:in:)`, `.buttonStyle(.glass)`, `.buttonStyle(.glassProminent)`, `tabBarMinimizeBehavior(_:)`.
- All 61 SF Symbol names resolve on macOS 27.2.

**Fixed**
- Materials: `chromeMaterial` is not a SwiftUI material. The list now uses the real SwiftUI names (`.ultraThinMaterial` … `.ultraThickMaterial`, `.bar`), with the UIKit and AppKit equivalents named separately.
- Liquid Glass over photos: now follows Apple's own rule (clear glass only over rich media, with a dark dimming layer of about 35% when the content is bright) instead of a community workaround.
- Control sizes: visionOS was listed as 44x44pt; Apple says 60x60pt. macOS does have a rule (28x28 default, 20x20 minimum). All five platforms are now listed, plus Apple's spacing between controls (12pt bezeled, 24pt without a bezel).
- The server now reports its real version in the MCP handshake and the sosumi.ai User-Agent (it said 0.1 / empty).

**Added**
- Colors: systemMint, systemCyan, systemBrown, and the Increased contrast values (light and dark) for every system color and gray.
- iOS type ramp: line heights and emphasized weights (Apple added them to the HIG on 2025-12-16).
- Liquid Glass: the regular / clear / identity variants with when to use each, the content-layer rule and its slider/toggle exception, `glassEffectUnion`, `glassEffectTransition`, `.buttonStyle(.glass(.clear))`.
- OS 27 beta APIs, marked `verify: true`: `Tab(role: .prominent)`, `toolbarMinimizationBehavior(_:for:)`, `.topBarPinnedTrailing`, `visibilityPriority(_:)`, `ToolbarOverflowMenu`.
- A `checked` date in every data file's `_meta`.
- README: a "Limits" section (curated data, not an Apple SDK; beta names checked as of a date; `hig_fetch` needs sosumi.ai; a good pairing).
- Tests (`uv run --with pytest pytest -q`).

## 0.2.0 — not released

- Migrated to the mcp SDK 2.0 (`FastMCP` → `MCPServer`, call counter as server middleware). Shipped as part of 0.3.0.

## 0.1.1 — 2026-07-18

- Docs only: Legal section in the README.

## 0.1.0 — 2026-07-17

- First public release: `hig_get_tokens`, `hig_check_liquid_glass`, `hig_swiftui`, `hig_fetch`.
