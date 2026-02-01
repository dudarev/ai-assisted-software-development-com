#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]

FRONTMATTER_BOUNDARY = re.compile(r"^---\s*$")
TAG_DASH_LINE = re.compile(r"^\s*-\s*(.+?)\s*$")
PUBLISH_LINE = re.compile(r"^\s*publish:\s*true\s*$", re.IGNORECASE)
TITLE_LINE = re.compile(r"^(\s*)title\s*:\s*(.*?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Frontmatter:
    raw_lines: list[str]
    has_publish: bool
    tags: set[str]


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
    tags = _extract_tags(fm_lines)
    has_publish = any(PUBLISH_LINE.match(line) for line in fm_lines) or "publish" in tags
    return Frontmatter(raw_lines=fm_lines, has_publish=has_publish, tags=tags)


def _extract_tags(fm_lines: list[str]) -> set[str]:
    tags: set[str] = set()
    inside_tags_block = False
    for line in fm_lines:
        stripped = line.strip()
        if stripped.lower().startswith("tags:"):
            inside_tags_block = True
            value = stripped[len("tags:") :].strip()
            if value.startswith("[") and value.endswith("]"):
                items = [x.strip().strip("'\"").lower() for x in value[1:-1].split(",") if x.strip()]
                tags.update(items)
            elif value:
                items = [x.strip().strip("'\"").lower() for x in value.split(",") if x.strip()]
                tags.update(items)
            continue

        if inside_tags_block:
            m = TAG_DASH_LINE.match(line)
            if m:
                tags.add(m.group(1).strip().strip("'\"").lower())
                continue
            if stripped and not line.startswith((" ", "\t")):
                inside_tags_block = False
    return tags


def _frontmatter_has_publish_tag(fm_lines: list[str]) -> bool:
    return "publish" in _extract_tags(fm_lines)


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


def _transform_image_wikilinks(text: str) -> str:
    """Convert Obsidian image wikilinks ![[image.ext]] to standard Markdown ![](path/to/image.ext)."""
    # Match ![[filename.ext]] or ![[filename.ext|alt]] patterns.
    pattern = r"!\[\[([^\]|]+?\.(?:svg|png|jpg|jpeg|gif|webp|pdf))(?:\|[^\]]*)?\]\]"

    def replace_image(match: re.Match[str]) -> str:
        filename = match.group(1).strip()
        if filename.startswith(("media/", "media\\")):
            filename = filename.split("/", 1)[1] if "/" in filename else filename.split("\\", 1)[1]

        encoded_filename = quote(filename, safe="/")
        return f"![{filename}](/media/{encoded_filename})"

    return re.sub(pattern, replace_image, text, flags=re.IGNORECASE)


def _escape_yaml_double_quoted(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', "\\\"")


def _normalize_title_and_strip_leading_h1(text: str) -> str:
    """If the first content line is an H1, promote it to front matter title and remove the H1.

    PaperMod renders the front matter `title` as the page title. If the body also starts with
    `# Title`, it results in a duplicated title. This normalizes exported pages without requiring
    edits to the `content/` submodule.
    """

    lines = text.splitlines(keepends=True)
    if not lines or not FRONTMATTER_BOUNDARY.match(lines[0].strip()):
        return text

    end_index = None
    for idx in range(1, len(lines)):
        if FRONTMATTER_BOUNDARY.match(lines[idx].strip()):
            end_index = idx
            break
    if end_index is None:
        return text

    # Find first non-empty content line after front matter
    content_idx = end_index + 1
    first_non_empty = None
    for idx in range(content_idx, len(lines)):
        if lines[idx].strip() != "":
            first_non_empty = idx
            break
    if first_non_empty is None:
        return text

    h1_line = lines[first_non_empty]
    if not h1_line.startswith("# ") or h1_line.startswith("##"):
        return text

    title_text = h1_line[2:].strip()
    if not title_text:
        return text

    # Remove the H1 line and a single following blank line (if present).
    del lines[first_non_empty]
    if first_non_empty < len(lines) and lines[first_non_empty].strip() == "":
        del lines[first_non_empty]

    # Replace or insert title in front matter.
    escaped = _escape_yaml_double_quoted(title_text)
    title_written = False
    for idx in range(1, end_index):
        m = TITLE_LINE.match(lines[idx].rstrip("\n"))
        if m:
            indent = m.group(1) or ""
            newline = "\n" if lines[idx].endswith("\n") else ""
            lines[idx] = f'{indent}title: "{escaped}"{newline}'
            title_written = True
            break

    if not title_written:
        lines.insert(1, f'title: "{escaped}"\n')
        end_index += 1

    return "".join(lines)


def copy_media_files(source_root: Path, static_dir: Path) -> None:
    """Copy media files from content/media to static/media for Hugo serving."""
    media_source = source_root / "media"
    media_dest = static_dir / "media"
    
    if not media_source.exists():
        return
    
    # Clean and recreate media destination
    if media_dest.exists():
        shutil.rmtree(media_dest)
    media_dest.mkdir(parents=True, exist_ok=True)
    
    # Copy all media files
    for media_file in media_source.rglob("*"):
        if media_file.is_file():
            rel_path = media_file.relative_to(media_source)
            dest_file = media_dest / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(media_file, dest_file)


def export_published(source_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(source_dir.rglob("*.md")):
        rel = path.relative_to(source_dir)
        raw = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(raw)
        if fm is None or not fm.has_publish:
            continue

        # Convert filename to kebab-case for Hugo
        # Hugo treats `index.md` as a leaf bundle. If we export an `index.md` into
        # the content root, sibling pages won't be rendered as standalone pages.
        # Use `_index.md` for the homepage to keep the root as a list bundle.
        if rel.parent == Path(".") and path.name.lower() in {"index.md", "_index.md"}:
            slugified_name = "_index.md"
        else:
            filename_stem = path.stem  # e.g., "Four Modes of AI Assistance"
            slugified_name = _slugify(filename_stem) + ".md"
        
        # Reconstruct output path with slugified filename
        if "weekly" in fm.tags:
            out_rel = Path("weekly") / slugified_name
        elif rel.parent == Path("."):
            out_rel = Path(slugified_name)
        else:
            out_rel = rel.parent / slugified_name
        
        out_path = output_dir / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Transform the content: remove publish tag, fix .md links, convert wikilinks and images
        transformed = _remove_publish_tag(raw)
        transformed = _normalize_title_and_strip_leading_h1(transformed)
        transformed = _transform_md_links(transformed)
        transformed = _transform_image_wikilinks(transformed)
        transformed = _transform_wikilinks(transformed)
        
        out_path.write_text(transformed, encoding="utf-8")


def write_search_page(output_dir: Path) -> None:
    search_path = output_dir / "search.md"
    content = "---\n" + 'title: "Search"\n' + 'layout: "search"\n' + "---\n"
    search_path.write_text(content, encoding="utf-8")


def write_weekly_index(output_dir: Path) -> None:
    weekly_dir = output_dir / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    index_path = weekly_dir / "_index.md"
    content = "---\n" + 'title: "Weekly YouTube Picks"\n' + 'layout: "list"\n' + "---\n"
    index_path.write_text(content, encoding="utf-8")


def main() -> None:
    source = ROOT / "content" / "notes"
    output = ROOT / "site-content"
    content_root = ROOT / "content"
    static_dir = ROOT / "static"

    if not source.exists():
        raise SystemExit(f"Missing source: {source} (did you init submodules?)")

    if output.exists():
        shutil.rmtree(output)

    export_published(source, output)
    write_search_page(output)
    write_weekly_index(output)
    copy_media_files(content_root, static_dir)


if __name__ == "__main__":
    main()
