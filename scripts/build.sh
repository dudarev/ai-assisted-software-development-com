#!/usr/bin/env bash
set -euo pipefail

git submodule update --init --recursive

python3 scripts/export_content.py

hugo --minify
