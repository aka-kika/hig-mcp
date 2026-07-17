# Internal notes (pre-public: prune or keep, your call)

## Next moves

- Extend the token files: ✅ SF Symbols category, ✅ 14 SwiftUI components (was 6), ✅ per-platform typography (iOS + **verified macOS** ramp) + platform notes. No clean HIG numeric source for visionOS type or macOS control heights (AppKit, not HIG) — left qualitative. Plain JSON you own.
- `hig_search` over sosumi results — **deliberately not built** (2026-06-24): retrieval is sosumi's / skill-librarian's job; adding it here re-enters the scope this server intentionally cedes.
- ✅ `outputSchema` / structured returns (2026-06-24): all 4 tools return `structuredContent` + a declared `outputSchema` (text block kept for older clients).
- Run it through `new-project-gate`: the wedge is the structured layer; if that ever gets commoditized, this collapses back into "just use sosumi."

## Gate

> Gate 2026-06-23: GO (conditional). **Proving cut CLEARED 2026-06-24** — tokens verified vs current HIG (palette refreshed to WWDC25 values) + `examples/NowPlayingView.swift` built agent-only and graded HIG-correct without fixes. Kill if 2 native builds skip it, or Apple/sosumi ships structured tokens.

## Data freshness

- Color values re-verified 2026-07-17 vs live HIG: changelog shows no WWDC26 color change (latest entry 2025-12-16, Liquid Glass guidance only); all hex values match.
