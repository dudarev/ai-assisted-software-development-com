# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2026-01-02

### Fixed
- Fix published-page export when `tags:` is a YAML list and `publish` is not the first tag (prevents missing pages/404s).

### Changed
- Clarify agent guidance for changelog updates and optional git tagging (deployment happens from `main`).

## [0.1.4] - 2026-01-01

### Fixed
- Improve code block readability by implementing theme-aware syntax highlighting: GitHub style for light mode, Monokai for dark mode.
- Override PaperMod's default code block styling to ensure proper contrast on white backgrounds.

## [0.1.3] - 2025-12-31

### Fixed
- Disable automatic capitalization of list titles so tags like "AI agents" keep their casing.

### Changed
- Document that releases should be tagged when updating `CHANGELOG.md`.

## [0.1.2] - 2025-12-31

### Fixed
- Normalize exported pages to avoid duplicated titles when content includes a leading H1.
- Clarify that `content/` is a submodule and must not be edited locally.

## [0.1.1] - 2025-12-31

### Fixed
- Export homepage as `_index.md` so top-level pages render (prevents 404s for published pages).

## [0.1.0] - 2025-12-31

### Added
- Initial Hugo site setup with PaperMod theme
- Content export script for markdown file management
- Makefile for build automation
- AGENTS.md guide for AI agent collaboration
- CHANGELOG.md following Keep a Changelog format

[Unreleased]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dudarev/ai-assisted-software-development-com/releases/tag/v0.1.0
