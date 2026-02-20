#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


FRONTMATTER_BOUNDARY = re.compile(r"^---\s*$")
TAG_DASH_LINE = re.compile(r"^\s*-\s*(.+?)\s*$")
PUBLISH_LINE = re.compile(r"^\s*publish:\s*true\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Frontmatter:
    has_publish: bool
    tags: set[str]


def _slugify(text: str) -> str:
    slug = text.lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


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
    return Frontmatter(has_publish=has_publish, tags=tags)


def _note_to_out_rel(note_rel: Path, fm: Frontmatter) -> Path:
    if note_rel.parent == Path(".") and note_rel.name.lower() in {"index.md", "_index.md"}:
        slugified_name = "_index.md"
    else:
        slugified_name = _slugify(note_rel.stem) + ".md"

    if "weekly" in fm.tags:
        return Path("weekly") / slugified_name
    if note_rel.parent == Path("."):
        return Path(slugified_name)
    return note_rel.parent / slugified_name


def _out_rel_to_url(out_rel: Path, base_url: str) -> str:
    base = base_url.rstrip("/")
    if out_rel.name == "_index.md":
        if out_rel.parent == Path("."):
            return f"{base}/"
        return f"{base}/{out_rel.parent.as_posix().strip('/')}/"

    without_ext = out_rel.as_posix()
    if without_ext.endswith(".md"):
        without_ext = without_ext[: -len(".md")]
    return f"{base}/{without_ext.strip('/')}/"


def _tag_to_url(tag: str, base_url: str) -> str:
    return f"{base_url.rstrip('/')}/tags/{_slugify(tag)}/"


def _run_git(content_dir: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(content_dir), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git failed: {' '.join(args)}")
    return proc.stdout


def _git_show(content_dir: Path, sha: str, rel_path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(content_dir), "show", f"{sha}:{rel_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _iter_changed_note_paths(content_dir: Path, old_sha: str, new_sha: str, notes_dir: str) -> list[tuple[str | None, str | None]]:
    out = _run_git(content_dir, ["diff", "--name-status", old_sha, new_sha, "--", notes_dir])
    pairs: list[tuple[str | None, str | None]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        status = fields[0]
        if status.startswith(("R", "C")):
            if len(fields) >= 3:
                pairs.append((fields[1], fields[2]))
            continue
        if status in {"A", "M"} and len(fields) >= 2:
            pairs.append((None, fields[1]))
            continue
        if status == "D" and len(fields) >= 2:
            pairs.append((fields[1], None))
            continue
    return pairs


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compute IndexNow URLs affected by a content submodule diff.")
    parser.add_argument("--content-dir", default="content", help="Path to content submodule working tree")
    parser.add_argument("--notes-dir", default="notes", help="Notes directory inside content repo (default: notes)")
    parser.add_argument("--old-sha", required=True, help="Old content commit SHA")
    parser.add_argument("--new-sha", required=True, help="New content commit SHA")
    parser.add_argument("--host", required=True, help="Host to emit URLs for (must match the sitemap host)")
    parser.add_argument("--base-url", default=None, help="Base URL (default: https://<host>)")
    parser.add_argument("--include-taxonomies", action="store_true", help="Also emit affected /tags/ URLs")
    args = parser.parse_args(argv)

    content_dir = Path(args.content_dir)
    notes_dir = args.notes_dir.strip("/").rstrip("/")
    base_url = args.base_url or f"https://{args.host}"
    old_sha = args.old_sha.strip()
    new_sha = args.new_sha.strip()

    if not old_sha or not new_sha:
        print("Missing old/new content SHA; no URLs emitted.", file=sys.stderr)
        return 0
    if old_sha == new_sha:
        print("Content SHA unchanged; no URLs emitted.", file=sys.stderr)
        return 0

    changed_pairs = _iter_changed_note_paths(content_dir, old_sha, new_sha, notes_dir)

    urls: set[str] = set()
    tags: set[str] = set()

    def add_from_version(sha: str, rel_path: str) -> None:
        if not rel_path.lower().endswith(".md"):
            return
        text = _git_show(content_dir, sha, rel_path)
        if text is None:
            return
        fm = _parse_frontmatter(text)
        if fm is None or not fm.has_publish:
            return
        note_rel = Path(rel_path).relative_to(notes_dir)
        out_rel = _note_to_out_rel(note_rel, fm)
        urls.add(_out_rel_to_url(out_rel, base_url=base_url))
        if args.include_taxonomies:
            tags.update(fm.tags)

    for old_path, new_path in changed_pairs:
        if old_path:
            add_from_version(old_sha, old_path)
        if new_path:
            add_from_version(new_sha, new_path)

    if args.include_taxonomies and tags:
        urls.add(f"{base_url.rstrip('/')}/tags/")
        for tag in tags:
            if tag == "publish":
                continue
            urls.add(_tag_to_url(tag, base_url=base_url))

    # Filter to requested host (defense-in-depth).
    urls = {u for u in urls if urlsplit(u).hostname and urlsplit(u).hostname.lower() == args.host.lower()}

    for url in sorted(urls):
        print(url)

    print(f"Changed note files: {len(changed_pairs)}", file=sys.stderr)
    print(f"URLs emitted: {len(urls)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
