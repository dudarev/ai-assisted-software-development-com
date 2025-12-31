# AI-Assisted Software Development (Site)

This repository contains the Hugo site that publishes the knowledge base from the `content` submodule.

## Structure

- `content/`: Submodule pointing to the knowledge-base repo.
- `themes/PaperMod/`: PaperMod theme as a submodule.
- `hugo.toml`: Minimal Hugo configuration.

This site publishes from `content/published` (generated in the knowledge-base repo).

## Local preview

```sh
make init    # Initialize submodules (first time only)
make serve   # Export content and start Hugo server
```

Or manually:

```sh
git submodule update --init --recursive
python3 scripts/export_content.py
hugo server -D
```

Then open http://localhost:1313/.

Run `make help` to see all available commands.

### Update content locally

After pulling changes to the content submodule, you must re-run the export script to update the site:

```sh
make sync    # Update content and export in one step
```

Or manually:

```sh
cd content
git pull origin main
cd ..
python3 scripts/export_content.py
```

The export script copies files tagged with `publish` from `content/notes/` into `site-content/`, which Hugo serves.

**If Hugo server is running**, it will auto-reload after the export script completes.

## Publishing

This repo is intended to be deployed on Cloudflare Pages.

- Build command: `bash scripts/build.sh`
- Output directory: `public`

When content changes, the `content` submodule pointer is updated automatically via GitHub Actions:

- The knowledge-base repo dispatches `content_updated` events.
- This repo updates the `content` submodule to the latest `main` and pushes a commit, which triggers Cloudflare Pages.

During the Cloudflare build, `scripts/build.sh` exports only pages tagged `publish` from `content/notes/` into `site-content/`, then runs Hugo.

If needed, run the workflow manually via the Actions tab (“Update content submodule”).
