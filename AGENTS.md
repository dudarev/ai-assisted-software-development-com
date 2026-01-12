# Agents Guide

This document explains how AI agents (human-operated or autonomous) should work with this repository.

## Purpose

Agents are used to:
- assist with site setup and maintenance
- keep the publishing workflow clear and minimal
- update configuration in small, reviewable steps

Agents are **assistive**, not authoritative.

## Core principles for agents

1. **Prefer clarity over verbosity**
2. **Preserve intent** — do not “improve” tone or scope unless asked
3. **Keep changes minimal** — avoid large rewrites or refactors
4. **Show uncertainty explicitly**
5. **Avoid hype**

## How agents should contribute

When creating or modifying content:
- keep changes small and reviewable
- explain *why* a change is suggested
- prefer incremental evolution over rewrites
- respect existing terminology and structure

Spec-driven development (SDD):
- for non-trivial features, draft a PRD in `docs/prds/` and a spec in `docs/specs/` before implementation
- use lowercase file names with a numeric prefix (e.g., `001-fuse-search.md`)
- cross-link PRD and spec in each document
- record changelog/versioning expectations in the spec
- implement only what the spec covers unless asked to expand scope

When changing site setup:
- do not commit generated output (`public/`)
- treat `content/` and `themes/` as submodules
- document any workflow changes in `README.md`

### Important: do not edit the `content/` submodule here

The `content/` folder is a git submodule pinned to a specific commit during builds.
Local edits inside `content/` will cause `git submodule update` to fail and break `make build`.

If you need to change published content:
- make the change in the upstream knowledge-base repository (the submodule repo), or
- adjust the export pipeline in `scripts/export_content.py` to transform content at export time.

When maintaining the changelog (`CHANGELOG.md`):
- follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format
- document notable changes, not every commit
- use clear, human-readable language
- group changes by type: Added, Changed, Deprecated, Removed, Fixed, Security
- maintain an Unreleased section for upcoming changes
- proactively add an entry when fixing a production-visible issue (e.g. a broken route/404) or changing the publishing workflow
- use ISO date format (YYYY-MM-DD) for release dates
- record breaking changes explicitly
- this site deploys from `main` on Cloudflare Pages; tags are optional and do not affect deployment
- if you cut a release in `CHANGELOG.md`, consider creating/pushing a matching git tag (e.g. `v0.1.2`) so the compare links at the bottom of the changelog resolve correctly

## Authority model

This repository represents the author’s evolving intent for how the site is published.

Agents may:
- propose
- question
- refactor
- summarize

Agents may not:
- present opinions as settled facts
- remove nuance for simplicity
- optimize for popularity or SEO

## Long-term goal

Keep a stable, minimal publishing setup that can evolve without breaking content ownership.
