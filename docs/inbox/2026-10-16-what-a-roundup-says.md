---
title: What a Manus round-up says about hig-mcp
date: 2026-10-16
kind: polish
status: done
---

## What Kika said
Her Manus search for Apple docs and HIG MCP servers listed hig-mcp as #6, "best structured HIG tokens and Liquid Glass guidance" (36 stars). "Good idea to search from time to time for things that list my tools, to read the limitations the agents mark."

## What it means
The limitations it wrote (worth answering in the README or the code):
- Structured values are curated project data, not an official Apple SDK; it suggests verifying beta-era API names.
- Prose fetching needs network access to sosumi.ai.
- Latest commit 4 Aug 2026, latest release v0.1.1 (18 Jul 2026): it reads as quiet. A small release that refreshes values for the current OS 26 and 27 betas would answer that.
- Its recommended pairing: a full docs server plus nlaratta/hig-review for checking SwiftUI code and screenshots against the HIG.

## Fits with
- Full round-up: Kika's upload "Apple Developer Documentation and HIG MCPs" (16 Oct 2026), copy in the coordinator session uploads.
- Monthly round-up search at FMD (maintenance queue, added 2026-10-16).

## Questions for Kika
- A small refresh release (values checked against the current betas, README limits section)?

## Done (2026-10-17)
Answered in 0.3.0: all values checked against the live HIG and the OS 26 / OS 27 beta SwiftUI docs (stale bits fixed, see CHANGELOG.md), README has a "Limits" section with the pairing (apple-docs-mcp or sosumi.ai, plus nlaratta/hig-review).
