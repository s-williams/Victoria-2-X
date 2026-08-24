#!/usr/bin/env python3
"""
Scrapes https://x4-foundations-wiki.fandom.com/wiki/Category:Sectors
and extracts the "Sunlight" percentage from each sector's infobox.

Usage:
    python3 scrape_sectors.py [output.csv]

Uses the MediaWiki API to enumerate category members (handles pagination
automatically), then fetches each sector's page and parses the portable
infobox for the sunlight data row.
"""
import sys
import csv
import time
import requests
from bs4 import BeautifulSoup

WIKI_BASE = "https://x4-foundations-wiki.fandom.com"
API_URL = f"{WIKI_BASE}/api.php"
CATEGORY = "Category:Sectors"
HEADERS = {"User-Agent": "sector-sunlight-scraper/1.0 (personal script)"}
REQUEST_DELAY = 0.5  # seconds between requests, be polite to the wiki


def get_category_members(category):
    """Yield page titles (main namespace only) in the given category."""
    session = requests.Session()
    session.headers.update(HEADERS)
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "500",
            "cmnamespace": "0",  # articles only, skip subcategories/files
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        resp = session.get(API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for member in data.get("query", {}).get("categorymembers", []):
            yield member["title"]

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break


def get_sunlight(session, title):
    """Fetch a wiki page's rendered HTML via the API and extract the
    infobox sunlight percentage.

    Note: fetching the plain /wiki/<title> URL directly hits a Cloudflare
    JS challenge page ("Just a moment...") that a plain HTTP client can't
    pass. The action=parse API endpoint returns the same rendered infobox
    HTML without tripping that challenge.
    """
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
    }
    resp = session.get(API_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        return None

    html = data.get("parse", {}).get("text", {}).get("*", "")
    soup = BeautifulSoup(html, "html.parser")

    row = soup.find("div", attrs={"data-source": "sunlight"})
    if row is None:
        return None

    value_div = row.find("div", class_="pi-data-value")
    if value_div is None:
        return None

    return value_div.get_text(strip=True)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "sectors_sunlight.csv"

    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"Fetching category members for {CATEGORY}...")
    titles = list(get_category_members(CATEGORY))
    print(f"Found {len(titles)} sector pages.")

    results = []
    for i, title in enumerate(titles, 1):
        try:
            sunlight = get_sunlight(session, title)
        except requests.RequestException as e:
            print(f"[{i}/{len(titles)}] {title}: ERROR ({e})")
            sunlight = None
        else:
            print(f"[{i}/{len(titles)}] {title}: {sunlight!r}")
        results.append((title, sunlight))
        time.sleep(REQUEST_DELAY)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Sector", "Sunlight"])
        writer.writerows(results)

    missing = [t for t, s in results if s is None]
    print(f"\nWrote {len(results)} rows to {out_path}")
    if missing:
        print(f"{len(missing)} pages had no sunlight value found: {missing}")


if __name__ == "__main__":
    main()
