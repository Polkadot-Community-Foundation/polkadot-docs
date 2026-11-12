#!/usr/bin/env python3
"""Check that a `mkdocs build` output serves robots.txt and sitemap.xml from its root.

robots.txt must name the site's /sitemap.xml, and the sitemap must be a
sitemaps.org <urlset> listing at least one page, all on that site. A listed page
the build has no HTML for is reported as a warning.

Usage:
    python scripts/check_search_files.py [site_dir]

Exits 1 with every failure listed. Warnings alone exit 0.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
SITEMAP_LINE_RE = re.compile(r"^sitemap:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def check(site_dir):
    """Return (errors, warnings)."""
    robots_path = os.path.join(site_dir, "robots.txt")
    if not os.path.isfile(robots_path):
        return ["robots.txt is missing"], []
    with open(robots_path, encoding="utf-8") as f:
        robots = f.read()

    sitemap_url = next(
        (u for u in map(urlparse, SITEMAP_LINE_RE.findall(robots))
         if u.scheme == "https" and u.netloc and u.path == "/sitemap.xml"),
        None,
    )
    if sitemap_url is None:
        return ["robots.txt names no https://<site>/sitemap.xml"], []

    sitemap_path = os.path.join(site_dir, "sitemap.xml")
    if not os.path.isfile(sitemap_path):
        return ["sitemap.xml is missing"], []
    try:
        root = ET.parse(sitemap_path).getroot()
    except ET.ParseError as e:
        return [f"sitemap.xml is not valid XML: {e}"], []
    if root.tag != f"{SITEMAP_NS}urlset":
        return ["sitemap.xml is not a sitemaps.org <urlset>"], []

    locs = [(loc.text or "").strip() for loc in root.iter(f"{SITEMAP_NS}loc")]
    if not locs:
        return ["sitemap.xml lists no pages"], []

    errors, warnings = [], []
    for loc in locs:
        url = urlparse(loc)
        if (url.scheme, url.netloc) != (sitemap_url.scheme, sitemap_url.netloc):
            errors.append(f"sitemap.xml lists {loc}, which is not on "
                          f"{sitemap_url.scheme}://{sitemap_url.netloc}")
            continue
        path = os.path.join(site_dir, unquote(url.path).lstrip("/"))
        if url.path.endswith("/"):
            path = os.path.join(path, "index.html")
        if not os.path.isfile(path):
            warnings.append(f"sitemap.xml lists {loc}, which the build has no page for")
    if not errors:
        print(f"{site_dir}: robots.txt and sitemap.xml ok, {len(locs)} pages listed")
    return errors, warnings


def main():
    site_dir = sys.argv[1] if len(sys.argv) > 1 else "site"
    errors, warnings = check(site_dir)
    for warning in warnings:
        print(f"::warning::{site_dir}: {warning}")
    for error in errors:
        print(f"::error::{site_dir}: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
