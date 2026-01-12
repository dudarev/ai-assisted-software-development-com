# PRD: Enable PaperMod Fuse.js Search

Related spec: `docs/specs/001-fuse-search.md`

## Summary
Enable the built-in PaperMod search experience (Fuse.js) so readers can search published notes at `/search`, with a simple top navigation that links to Search and Tags.

## Problem
Search is currently not enabled, so visitors cannot quickly find content by keyword.

## Goals
- Add a functional `/search` page using PaperMod's Fuse.js integration.
- Index only published content (the `site-content/` export).
- Keep changes minimal and aligned with existing build workflow.

## Non-goals
- Replace the theme's search UI or style.
- Edit `content/` or `themes/` submodules directly.
- Introduce external search services.
- Add a global search bar in the site header.

## Users
- Readers who want to find notes by keyword.

## Requirements
### Functional
- `/search` renders the PaperMod search UI.
- Search results include title, summary/snippet, and permalink.
- Index excludes search/archives pages (as PaperMod's `index.json` already does).
- Default Fuse options are used.
- Top navigation includes `Search` and `Tags` links.

### Non-functional
- Search loads quickly on mobile and desktop.
- No errors if `index.json` is missing (graceful empty state).

## Proposed Approach
- Config:
  - Update `hugo.toml` to enable JSON output for the home page (`home = ["HTML", "RSS", "JSON"]`).
  - Add menu entries that link to `/search` and `/tags`.
  - Keep default Fuse options.
- Content generation:
  - Add a generated search page (e.g., `site-content/search.md`) during `scripts/export_content.py`.
  - This avoids modifying the `content/` submodule and keeps `/search` in the build output.
- UI:
  - Use PaperMod's existing `layouts/_default/search.html` and `assets/js/fastsearch.js`.
  - Only override templates if a customization is required.

## Success Metrics
- `/search` loads and returns expected results for sample queries.
- `public/index.json` is produced during `scripts/build.sh`.
- No regressions in `make serve` and `make build`.

## Rollout Plan
1. Implement config change and generated `/search` page.
2. Validate locally with a handful of queries.
3. Deploy to Cloudflare Pages and verify.

## Open Questions / Risks
- None for now; keep defaults and a simple nav link.
