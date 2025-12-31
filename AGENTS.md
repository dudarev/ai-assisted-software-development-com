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

When changing site setup:
- do not commit generated output (`public/`)
- treat `content/` and `themes/` as submodules
- document any workflow changes in `README.md`

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
