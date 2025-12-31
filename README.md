# AI-Assisted Software Development (Site)

This repository contains the Hugo site that publishes the knowledge base from the `content` submodule.

## Structure

- `content/`: Submodule pointing to the knowledge-base repo.
- `themes/PaperMod/`: PaperMod theme as a submodule.
- `hugo.toml`: Minimal Hugo configuration.

## Local preview

```sh
hugo server -D
```

Then open http://localhost:1313/.

## Publishing

This repo is intended to be deployed on Cloudflare Pages.

- Build command: `hugo --minify`
- Output directory: `public`

When content changes, update the `content` submodule pointer and commit it here.
