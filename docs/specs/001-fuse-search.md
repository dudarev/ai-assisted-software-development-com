# Spec: Enable PaperMod Fuse.js Search

Related PRD: `docs/prds/001-fuse-search.md`

## Decisions
- Use PaperMod's built-in Fuse.js search with default options.
- Add simple navigation links to `/search` and `/tags` (no global search bar).
- Generate a dedicated search page during export (no edits to submodules).

## Implementation
### Config (`hugo.toml`)
- Add JSON to home outputs so `public/index.json` is built:
  - `home = ["HTML", "RSS", "JSON"]`
- Add menu entries for Search and Tags pointing to `/search/` and `/tags/`.

### Content generation (`scripts/export_content.py`)
- After exporting published notes, write `site-content/search.md` with front matter:
  - `title: "Search"`
  - `layout: "search"`
- No body content is required.

### UI
- Use PaperMod's existing `layouts/_default/search.html` and bundled `fastsearch.js`.
- No template overrides unless search page requires customization.

## Changelog and Versioning
- Add an entry under `CHANGELOG.md` -> `Unreleased`:
  - `Added: Enable /search using PaperMod Fuse.js`
- Release as the next feature version (target `0.2.0`, not a patch release).

## Validation
- `make serve`:
  - Visit `/search/` and confirm results appear for sample queries.
- `make build`:
  - Confirm `public/index.json` and `public/search/index.html` exist.

## Rollout
- Merge to `main`, let Cloudflare Pages build, and smoke-test `/search/`.
