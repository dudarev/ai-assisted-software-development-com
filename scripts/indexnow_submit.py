#!/usr/bin/env python3

from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit


INDEXNOW_ENDPOINT_DEFAULT = "https://api.indexnow.org/indexnow"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass(frozen=True)
class SitemapEntry:
    url: str
    lastmod: str | None


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "indexnow-submit/1.0 (+https://github.com/dudarev/ai-assisted-software-development-com)",
            "Accept": "application/xml,text/xml,*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
        if encoding == "gzip" or url.endswith(".gz"):
            try:
                return gzip.decompress(raw)
            except OSError:
                return gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        return raw


def _read_sitemap_source(sitemap: str) -> bytes:
    if sitemap.startswith("http://") or sitemap.startswith("https://"):
        return _fetch_bytes(sitemap)
    return Path(sitemap).read_bytes()


def _iter_sitemap_entries_from_xml(xml_bytes: bytes, base: str) -> Iterable[SitemapEntry]:
    root = ET.fromstring(xml_bytes)
    root_kind = _local_tag(root.tag)

    if root_kind == "sitemapindex":
        for loc in root.findall("sm:sitemap/sm:loc", SITEMAP_NS):
            if not loc.text:
                continue
            nested = loc.text.strip()
            nested_xml = _read_sitemap_source(nested)
            yield from _iter_sitemap_entries_from_xml(nested_xml, base=nested)
        return

    if root_kind == "urlset":
        for url_node in root.findall("sm:url", SITEMAP_NS):
            loc = url_node.find("sm:loc", SITEMAP_NS)
            if loc is None or not loc.text:
                continue
            lastmod_node = url_node.find("sm:lastmod", SITEMAP_NS)
            lastmod = lastmod_node.text.strip() if (lastmod_node is not None and lastmod_node.text) else None
            yield SitemapEntry(url=loc.text.strip(), lastmod=lastmod)
        return

    raise ValueError(f"Unsupported sitemap root element {root.tag!r} from {base!r}")


def load_sitemap_entries(sitemap: str) -> list[SitemapEntry]:
    xml_bytes = _read_sitemap_source(sitemap)
    return list(_iter_sitemap_entries_from_xml(xml_bytes, base=sitemap))


def normalize_entries(entries: Iterable[SitemapEntry], host: str) -> dict[str, str | None]:
    normalized: dict[str, str | None] = {}
    for entry in entries:
        parts = urlsplit(entry.url)
        if not parts.scheme or not parts.netloc:
            continue
        if parts.hostname and parts.hostname.lower() != host.lower():
            continue
        normalized[entry.url] = entry.lastmod
    return normalized


def load_snapshot(path: Path) -> dict[str, str | None]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Snapshot at {path} must be a JSON object")
    out: dict[str, str | None] = {}
    for url, lastmod in raw.items():
        if isinstance(url, str) and (isinstance(lastmod, str) or lastmod is None):
            out[url] = lastmod
    return out


def write_snapshot(path: Path, snapshot: dict[str, str | None]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compute_urls_to_submit(
    current: dict[str, str | None],
    previous: dict[str, str | None] | None,
    include_deletions: bool,
) -> list[str]:
    if previous is None:
        return sorted(current.keys())

    changed = [url for url, lastmod in current.items() if previous.get(url) != lastmod]

    if include_deletions:
        deletions = [url for url in previous.keys() if url not in current]
        changed.extend(deletions)

    return sorted(set(changed))


def submit_indexnow_batch(
    *,
    endpoint: str,
    host: str,
    key: str,
    key_location: str,
    urls: list[str],
    dry_run: bool,
) -> int:
    payload = {"host": host, "key": key, "keyLocation": key_location, "urlList": urls}
    body = json.dumps(payload).encode("utf-8")

    if dry_run:
        print(f"DRY RUN: would submit {len(urls)} URLs to {endpoint}")
        return 0

    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_body = resp.read().decode("utf-8", "replace").strip()
            print(f"HTTP {resp.status} ({len(urls)} urls) {resp_body}".strip())
            return 0
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8", "replace").strip()
        print(f"HTTP {e.code} ({len(urls)} urls) {resp_body}".strip(), file=sys.stderr)
        return 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Submit sitemap URL changes to IndexNow.")
    parser.add_argument("--sitemap", required=True, help="Sitemap URL or local path (sitemap.xml)")
    parser.add_argument("--host", required=True, help="Host name to submit (e.g. ai-assisted-software-development.com)")
    parser.add_argument("--key", required=True, help="IndexNow key")
    parser.add_argument("--key-location", default=None, help="Key file URL (default: https://<host>/<key>.txt)")
    parser.add_argument("--endpoint", default=INDEXNOW_ENDPOINT_DEFAULT, help="IndexNow API endpoint")
    parser.add_argument("--snapshot-in", default=None, help="Previous snapshot JSON path (optional)")
    parser.add_argument("--snapshot-out", default=None, help="Write current snapshot JSON to this path (optional)")
    parser.add_argument("--include-deletions", action="store_true", help="Also submit URLs removed from sitemap")
    parser.add_argument("--batch-size", type=int, default=10_000, help="Max URLs per request (default: 10000)")
    parser.add_argument("--dry-run", action="store_true", help="Compute batches but do not submit")
    args = parser.parse_args(argv)

    key_location = args.key_location or f"https://{args.host}/{args.key}.txt"

    entries = load_sitemap_entries(args.sitemap)
    current = normalize_entries(entries, host=args.host)

    previous: dict[str, str | None] | None = None
    if args.snapshot_in:
        snap_path = Path(args.snapshot_in)
        if snap_path.exists():
            previous = load_snapshot(snap_path)

    to_submit = compute_urls_to_submit(current, previous, include_deletions=args.include_deletions)

    print(f"Sitemap: {args.sitemap}")
    print(f"Host: {args.host}")
    print(f"Entries (matching host): {len(current)}")
    print(f"URLs to submit: {len(to_submit)}")

    if not to_submit:
        if args.snapshot_out:
            write_snapshot(Path(args.snapshot_out), current)
        return 0

    rc = 0
    for i in range(0, len(to_submit), args.batch_size):
        batch = to_submit[i : i + args.batch_size]
        batch_rc = submit_indexnow_batch(
            endpoint=args.endpoint,
            host=args.host,
            key=args.key,
            key_location=key_location,
            urls=batch,
            dry_run=args.dry_run,
        )
        rc = max(rc, batch_rc)

    if rc == 0 and args.snapshot_out and not args.dry_run:
        write_snapshot(Path(args.snapshot_out), current)

    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
