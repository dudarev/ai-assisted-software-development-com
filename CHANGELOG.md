# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dudarev/ai-assisted-software-development-com/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dudarev/ai-assisted-software-development-com/releases/tag/v0.1.0
