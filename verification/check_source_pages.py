#!/usr/bin/env python3
"""
check_source_pages.py — every cited Leaguepedia source page must actually exist.

`scripts/verify_site.py --check-external` proves a source URL returns HTTP 200.
Leaguepedia returns **200 with an empty page body** for a title that does not
exist ("There is currently no text in this page"), so a 200 is not proof that the
cited tournament page exists. This script asks the Leaguepedia MediaWiki API
(`action=query&titles=…`) for the distinct tournament pages cited in the payload
and fails if any of them is reported `missing`.

One batched, read-only API request (titles are joined, 50 per request), no
scraping, so it respects the same pacing rules as the rest of the pipeline.

Usage:
  python3 verification/check_source_pages.py                 # docs/data/picks.json
  python3 verification/check_source_pages.py --payload X.json
Exit 0 when every cited page exists, 1 otherwise, 2 when the API is unreachable
(so a Leaguepedia outage does not silently read as "all pages valid").
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from lib_common import get_json, log  # noqa: E402

API = "https://lol.fandom.com/api.php"
PREFIX = "https://lol.fandom.com/wiki/"


def titles_from(payload: dict) -> dict[str, int]:
    """distinct cited page titles -> number of rows citing them."""
    cited: dict[str, int] = {}
    for m in payload.get("matches") or []:
        url = (m.get("leaguepedia_url") or "").strip()
        if not url.startswith(PREFIX):
            continue
        title = urllib.parse.unquote(url[len(PREFIX):]).split("#")[0].replace("_", " ").strip()
        if title:
            cited[title] = cited.get(title, 0) + 1
    return cited


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", default=os.path.join("docs", "data", "picks.json"))
    args = ap.parse_args()
    if not os.path.exists(args.payload):
        print(f"payload not found: {args.payload}")
        return 2
    payload = json.load(open(args.payload, encoding="utf-8"))
    cited = titles_from(payload)
    if not cited:
        print("no Leaguepedia tournament pages cited in this payload")
        return 0

    titles = sorted(cited)
    missing: list[str] = []
    checked = 0
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        url = (f"{API}?action=query&format=json&redirects=1&titles="
               + urllib.parse.quote("|".join(batch), safe=""))
        data, resp = get_json(url)
        if not isinstance(data, dict) or "query" not in data:
            print(f"Leaguepedia API unavailable (HTTP {resp.get('status')}): cannot verify source pages")
            return 2
        pages = (data.get("query") or {}).get("pages") or {}
        for page in pages.values():
            checked += 1
            if "missing" in page or page.get("invalid"):
                missing.append(str(page.get("title") or "?"))
    print(f"cited Leaguepedia pages: {len(titles)} · verified to exist: {checked - len(missing)} · missing: {len(missing)}")
    for title in titles:
        print(f"  {'MISSING' if title in missing else 'ok     '}  {title}  ({cited[title]} row(s))")
    if missing:
        print("FAIL: a cited tournament page does not exist on Leaguepedia")
        return 1
    print("Source-page existence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
