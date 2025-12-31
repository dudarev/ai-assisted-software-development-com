#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FRONTMATTER_BOUNDARY = re.compile(r"^---\s*$")
TAG_DASH_LINE = re.compile(r"^\s*-\s*(.+?)\s*$")
PUBLISH_LINE = re.compile(r"^\s*publish:\s*true\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Frontmatter:
    raw_lines: list[str]
    has_publish: bool


def _parse_frontmatter(text: str) -> Frontmatter | None:
    lines = text.splitlines(keepends=False)
    if not lines or not FRONTMATTER_BOUNDARY.match(lines[0]):
        return None

    end_index = None
    for idx in range(1, len(lines)):
        if FRONTMATTER_BOUNDARY.match(lines[idx]):
            end_index = idx
            break
    if end_index is None:
        return None

    fm_lines = lines[1:end_index]
    has_publish = any(PUBLISH_LINE.match(line) for line in fm_lines) or _frontmatter_has_publish_tag(
        fm_lines
    )
    return Frontmatter(raw_lines=fm_lines, has_publish=has_publish)


def _frontmatter_has_publish_tag(fm_lines: list[str]) -> bool:
    inside_tags_block = False
    for line in fm_lines:
        stripped = line.strip()
        if stripped.lower().startswith("tags:"):
            inside_tags_block = True
            value = stripped[len("tags:") :].strip()
            if value.startswith("[") and value.endswith("]"):
                items = [x.strip().strip("'\"") for x in value[1:-1].split(",") if x.strip()]
                return any(item.lower() == "publish" for item in items)
            if value:
                return any(x.strip().strip("'\"").lower() == "publish" for x in value.split(","))
            continue

        if inside_tags_block:
            m = TAG_DASH_LINE.match(line)
            if m:
                return m.group(1).strip().strip("'\"").lower() == "publish"
            if stripped and not line.startswith((" ", "\t")):
                inside_tags_block = False
    return False


def _remove_publish_tag(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or not FRONTMATTER_BOUNDARY.match(lines[0]):
        return text

    out: list[str] = []
    inside_frontmatter = True
    inside_tags_block = False

    for idx, line in enumerate(lines):
        out.append(line)
        if idx == 0:
            continue

        if inside_frontmatter and FRONTMATTER_BOUNDARY.match(line.strip()):
            inside_frontmatter = False
            inside_tags_block = False
            continue

        if not inside_frontmatter:
            continue

        stripped = line.strip()
        if stripped.lower().startswith("tags:"):
            inside_tags_block = True
            prefix, _, value = line.partition(":")
            value = value.strip()
            if value.startswith("[") and "]" in value:
                before, _, after = value.partition("]")
                items = [x.strip() for x in before.lstrip("[").split(",") if x.strip()]
                items = [x for x in items if x.strip().strip("'\"").lower() != "publish"]
                rendered = ", ".join(items)
                out[-1] = f"{prefix}: [{rendered}]\n"
                if after.strip():
                    out.insert(len(out), f"{after}\n")
                continue

        if inside_tags_block:
            m = TAG_DASH_LINE.match(line)
            if m and m.group(1).strip().strip("'\"").lower() == "publish":
                out.pop()
                continue
            if stripped and not line.startswith((" ", "\t")):
                inside_tags_block = False

    return "".join(out)


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase and replace spaces/underscores with hyphens
    slug = text.lower().replace(' ', '-').replace('_', '-')
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    return slug.strip('-')


def _transform_md_links(text: str) -> str:
    """Convert markdown links from .md files to Hugo clean URLs."""
    # Match [text](file.md) or [text](path/file.md) patterns
    pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
    
    def replace_link(match):
        link_text = match.group(1)
        link_path = match.group(2)
        
        # Remove .md extension and ensure path format for Hugo
        clean_path = link_path[:-3]  # Remove .md
        
        # Add leading slash if it's a relative path without one
        if not clean_path.startswith('/'):
            clean_path = '/' + clean_path
        
        # Add trailing slash for Hugo clean URLs
        if not clean_path.endswith('/'):
            clean_path = clean_path + '/'
        
        return f'[{link_text}]({clean_path})'
    
    return re.sub(pattern, replace_link, text)


def _transform_wikilinks(text: str) -> str:
    """Convert Wikilinks [[Page]] or [[page|Display]] to Hugo markdown links."""
    # Match [[target|display]] or [[target]] patterns
    pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
    
    def replace_wikilink(match):
        target = match.group(1).strip()
        display = match.group(2).strip() if match.group(2) else target
        
        # Slugify the target for the URL
        slug = _slugify(target)
        
        # Create Hugo-style link with leading and trailing slashes
        return f'[{display}](/{slug}/)'
    
    return re.sub(pattern, replace_wikilink, text)


def export_published(source_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(source_dir.rglob("*.md")):
        rel = path.relative_to(source_dir)
        raw = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(raw)
        if fm is None or not fm.has_publish:
            continue

        # Convert filename to kebab-case for Hugo
        filename_stem = path.stem  # e.g., "Four Modes of AI Assistance"
        slugified_name = _slugify(filename_stem) + ".md"
        
        # Reconstruct output path with slugified filename
        if rel.parent == Path("."):
            out_rel = Path(slugified_name)
        else:
            out_rel = rel.parent / slugified_name
        
        out_path = output_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Transform the content: remove publish tag, fix .md links, and convert wikilinks
        transformed = _remove_publish_tag(raw)
        transformed = _transform_md_links(transformed)
        transformed = _transform_wikilinks(transformed)
        
        out_path.write_text(transformed, encoding="utf-8")


def main() -> None:
    source = ROOT / "content" / "notes"
    output = ROOT / "site-content"

    if not source.exists():
        raise SystemExit(f"Missing source: {source} (did you init submodules?)")

    if output.exists():
        shutil.rmtree(output)

    export_published(source, output)


if __name__ == "__main__":
    main()
