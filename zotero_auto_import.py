#!/usr/bin/env python3
"""
Automated Zotero collection creator and paper importer.

Reads DOIs/arXiv IDs from a file, fetches metadata via Semantic Scholar API,
creates a Zotero collection, and imports all papers with metadata.

Requirements:
  - Zotero desktop must be running (uses local API on port 23119)
  - pip install pyzotero requests

Usage:
  python3 zotero_auto_import.py                          # uses defaults
  python3 zotero_auto_import.py --ids zotero_import_ids.txt --collection "My Project"
  python3 zotero_auto_import.py --ids zotero_import_ids.txt --collection "My Project" --s2-key YOUR_KEY
  python3 zotero_auto_import.py --ids zotero_import_ids.txt --collection "My Project" --attach-pdfs
"""

import argparse
import json
import os
import re
import sys
import time
import tempfile
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Zotero local API helpers (direct HTTP — avoids pyzotero version quirks)
# ---------------------------------------------------------------------------

ZOTERO_BASE = "http://localhost:23119/api"
S2_BASE = "https://api.semanticscholar.org/graph/v1"
CROSSREF_BASE = "https://api.crossref.org/works"


def check_zotero_running() -> bool:
    """Check if Zotero desktop is running and the local API is reachable."""
    try:
        r = requests.get(f"{ZOTERO_BASE}/users/0/collections", timeout=3)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def zotero_get_collections() -> list[dict]:
    """List all existing collections."""
    r = requests.get(f"{ZOTERO_BASE}/users/0/collections")
    r.raise_for_status()
    return r.json()


def zotero_create_collection(name: str, parent_key: str | None = None) -> str | None:
    """Create a new Zotero collection. Returns the collection key or None."""
    payload = {"name": name}
    if parent_key:
        payload["parentCollection"] = parent_key

    r = requests.post(
        f"{ZOTERO_BASE}/users/0/collections",
        headers={"Content-Type": "application/json"},
        json=[payload],
    )
    if r.status_code in (200, 201):
        result = r.json()
        if "successful" in result:
            for _idx, val in result["successful"].items():
                return val["data"]["key"]
        elif isinstance(result, list) and result:
            return result[0].get("key")
    print(f"  [WARN] Collection creation returned {r.status_code}: {r.text[:200]}")
    return None


def zotero_find_collection(name: str) -> str | None:
    """Find an existing collection by name. Returns key or None."""
    collections = zotero_get_collections()
    for c in collections:
        data = c.get("data", c)
        if data.get("name") == name:
            return data.get("key")
    return None


def zotero_create_item(item: dict) -> bool:
    """Create a single item in the local Zotero library."""
    r = requests.post(
        f"{ZOTERO_BASE}/users/0/items",
        headers={"Content-Type": "application/json"},
        json=[item],
    )
    if r.status_code in (200, 201):
        result = r.json()
        if "successful" in result and result["successful"]:
            return True
        if "failed" in result and result["failed"]:
            for _idx, fail in result["failed"].items():
                print(f"    [FAIL] {fail.get('message', 'Unknown error')}")
            return False
    print(f"    [WARN] Item creation returned {r.status_code}: {r.text[:300]}")
    return False


def zotero_get_item_template(item_type: str = "journalArticle") -> dict:
    """Get a blank item template from Zotero, with offline fallback."""
    try:
        r = requests.get(
            f"{ZOTERO_BASE}/items/new",
            params={"itemType": item_type},
            timeout=3,
        )
        if r.status_code == 200:
            return r.json()
    except requests.ConnectionError:
        pass
    # Fallback minimal template (works without Zotero running)
    return {
        "itemType": item_type,
        "title": "",
        "creators": [],
        "abstractNote": "",
        "date": "",
        "DOI": "",
        "url": "",
        "publicationTitle": "",
        "extra": "",
        "collections": [],
        "tags": [],
    }


def zotero_attach_url_pdf(parent_key: str, pdf_url: str, title: str) -> bool:
    """Attach a PDF by URL as a linked URL attachment."""
    item = {
        "itemType": "attachment",
        "linkMode": "linked_url",
        "title": f"{title}.pdf",
        "url": pdf_url,
        "parentItem": parent_key,
        "contentType": "application/pdf",
        "tags": [],
    }
    r = requests.post(
        f"{ZOTERO_BASE}/users/0/items",
        headers={"Content-Type": "application/json"},
        json=[item],
    )
    return r.status_code in (200, 201)


# ---------------------------------------------------------------------------
# Metadata fetching
# ---------------------------------------------------------------------------

def parse_identifier(raw: str) -> tuple[str, str]:
    """
    Classify an identifier string.
    Returns (id_type, normalized_id) where id_type is 'arxiv', 'doi', or 'unknown'.
    """
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        return ("skip", raw)

    # arXiv IDs: 4-digit year + dot + 4-5 digit number (optionally vN)
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", raw):
        return ("arxiv", raw)

    # DOIs start with 10.
    if raw.startswith("10."):
        return ("doi", raw)

    return ("unknown", raw)


def fetch_metadata_s2(identifier: str, id_type: str, api_key: str | None = None) -> dict | None:
    """Fetch paper metadata from Semantic Scholar API."""
    if id_type == "arxiv":
        paper_id = f"ARXIV:{identifier}"
    elif id_type == "doi":
        paper_id = f"DOI:{identifier}"
    else:
        paper_id = identifier

    fields = "title,authors,year,venue,publicationVenue,externalIds,abstract,url,citationCount"
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    try:
        r = requests.get(
            f"{S2_BASE}/paper/{paper_id}",
            params={"fields": fields},
            headers=headers,
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            print("    [RATE LIMITED] Waiting 30s...")
            time.sleep(30)
            r = requests.get(
                f"{S2_BASE}/paper/{paper_id}",
                params={"fields": fields},
                headers=headers,
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()
        print(f"    [S2] HTTP {r.status_code} for {paper_id}")
    except requests.RequestException as e:
        print(f"    [S2] Error for {paper_id}: {e}")
    return None


def fetch_metadata_crossref(doi: str) -> dict | None:
    """Fallback: fetch metadata from CrossRef for DOIs that S2 doesn't have."""
    try:
        r = requests.get(
            f"{CROSSREF_BASE}/{doi}",
            headers={"User-Agent": "ResearchPipeline/1.0 (mailto:research@example.com)"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("message", {})
    except requests.RequestException:
        pass
    return None


def s2_to_zotero(paper: dict, collection_key: str | None = None) -> dict:
    """Convert Semantic Scholar paper data to a Zotero item."""
    template = zotero_get_item_template("journalArticle")

    template["title"] = paper.get("title", "Untitled")
    template["abstractNote"] = paper.get("abstract") or ""
    template["date"] = str(paper.get("year", ""))
    template["url"] = paper.get("url", "")

    # Venue
    venue = paper.get("venue", "")
    pub_venue = paper.get("publicationVenue")
    if pub_venue and pub_venue.get("name"):
        venue = pub_venue["name"]
    template["publicationTitle"] = venue

    # External IDs
    ext_ids = paper.get("externalIds", {}) or {}
    if ext_ids.get("DOI"):
        template["DOI"] = ext_ids["DOI"]
    extra_parts = []
    if ext_ids.get("ArXiv"):
        extra_parts.append(f"arXiv: {ext_ids['ArXiv']}")
    if ext_ids.get("CorpusId"):
        extra_parts.append(f"S2CID: {ext_ids['CorpusId']}")
    template["extra"] = "\n".join(extra_parts)

    # Authors
    creators = []
    for author in paper.get("authors", []):
        name = author.get("name", "")
        parts = name.rsplit(" ", 1)
        if len(parts) == 2:
            creators.append({
                "creatorType": "author",
                "firstName": parts[0],
                "lastName": parts[1],
            })
        else:
            creators.append({
                "creatorType": "author",
                "firstName": "",
                "lastName": name,
            })
    template["creators"] = creators

    # Collection
    if collection_key:
        template["collections"] = [collection_key]

    return template


def crossref_to_zotero(data: dict, doi: str, collection_key: str | None = None) -> dict:
    """Convert CrossRef metadata to a Zotero item."""
    template = zotero_get_item_template("journalArticle")

    titles = data.get("title", [])
    template["title"] = titles[0] if titles else "Untitled"
    template["DOI"] = doi

    # Date
    date_parts = data.get("published", {}).get("date-parts", [[]])
    if date_parts and date_parts[0]:
        template["date"] = "-".join(str(p) for p in date_parts[0])

    # Venue
    container = data.get("container-title", [])
    template["publicationTitle"] = container[0] if container else ""

    # Authors
    creators = []
    for author in data.get("author", []):
        creators.append({
            "creatorType": "author",
            "firstName": author.get("given", ""),
            "lastName": author.get("family", ""),
        })
    template["creators"] = creators

    # Abstract
    template["abstractNote"] = data.get("abstract", "")

    if collection_key:
        template["collections"] = [collection_key]

    return template


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def load_identifiers(filepath: str) -> list[str]:
    """Load identifiers from a file, skipping comments and blank lines."""
    ids = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            ids.append(line)
    return ids


def main():
    parser = argparse.ArgumentParser(
        description="Automated Zotero collection creator and paper importer"
    )
    parser.add_argument(
        "--ids",
        default="zotero_import_ids.txt",
        help="File with DOIs/arXiv IDs, one per line (default: zotero_import_ids.txt)",
    )
    parser.add_argument(
        "--collection",
        default="Workshop Validation Paper",
        help="Name for the Zotero collection (default: 'Workshop Validation Paper')",
    )
    parser.add_argument(
        "--s2-key",
        default=None,
        help="Semantic Scholar API key (optional, avoids rate limits)",
    )
    parser.add_argument(
        "--attach-pdfs",
        action="store_true",
        help="Attach arXiv PDF links to imported items",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Seconds between API calls (default: 3.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch metadata and show what would be imported, without writing to Zotero",
    )
    args = parser.parse_args()

    # Read S2 key from environment if not passed
    s2_key = args.s2_key or os.environ.get("S2_API_KEY")

    # --- Check Zotero ---
    if not args.dry_run:
        print("Checking Zotero local API...")
        if not check_zotero_running():
            print(
                "ERROR: Zotero is not running or its local API is not reachable.\n"
                "  1. Open Zotero desktop\n"
                "  2. Make sure 'Allow other applications on this computer to communicate with Zotero'\n"
                "     is enabled (Edit > Settings > Advanced)\n"
                "  3. Re-run this script"
            )
            sys.exit(1)
        print("  Zotero is running.\n")

    # --- Load identifiers ---
    ids_file = Path(args.ids)
    if not ids_file.exists():
        print(f"ERROR: Identifier file not found: {ids_file}")
        sys.exit(1)

    raw_ids = load_identifiers(str(ids_file))
    print(f"Loaded {len(raw_ids)} identifiers from {ids_file}\n")

    # --- Create or find collection ---
    collection_key = None
    if not args.dry_run:
        existing_key = zotero_find_collection(args.collection)
        if existing_key:
            print(f"Found existing collection '{args.collection}' (key: {existing_key})")
            collection_key = existing_key
        else:
            print(f"Creating collection '{args.collection}'...")
            collection_key = zotero_create_collection(args.collection)
            if collection_key:
                print(f"  Created collection (key: {collection_key})")
            else:
                print("  WARNING: Could not create collection. Papers will go to root library.")
        print()

    # --- Fetch metadata and import ---
    success_count = 0
    fail_count = 0
    skip_count = 0
    results_log = []

    for i, raw_id in enumerate(raw_ids, 1):
        id_type, identifier = parse_identifier(raw_id)

        if id_type == "skip":
            continue

        print(f"[{i}/{len(raw_ids)}] {id_type.upper()}: {identifier}")

        # Fetch metadata from Semantic Scholar
        paper = fetch_metadata_s2(identifier, id_type, api_key=s2_key)

        if paper:
            title = paper.get("title", "???")
            year = paper.get("year", "???")
            print(f"  -> {title} ({year})")

            zotero_item = s2_to_zotero(paper, collection_key)

            if args.dry_run:
                results_log.append({"id": identifier, "title": title, "year": year, "status": "would_import"})
                success_count += 1
            else:
                if zotero_create_item(zotero_item):
                    print("  -> Imported to Zotero")
                    success_count += 1
                    results_log.append({"id": identifier, "title": title, "year": year, "status": "imported"})

                    # Attach arXiv PDF if requested
                    if args.attach_pdfs and id_type == "arxiv":
                        arxiv_id = paper.get("externalIds", {}).get("ArXiv", identifier)
                        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                        # We need the item key — re-fetch from Zotero by DOI/title
                        # For now just note the PDF URL
                        print(f"  -> arXiv PDF: {pdf_url}")
                else:
                    print("  -> FAILED to import")
                    fail_count += 1
                    results_log.append({"id": identifier, "title": title, "year": year, "status": "failed"})
        else:
            # Try CrossRef fallback for DOIs
            if id_type == "doi":
                print("  S2 failed, trying CrossRef...")
                cr_data = fetch_metadata_crossref(identifier)
                if cr_data:
                    titles = cr_data.get("title", ["???"])
                    title = titles[0] if titles else "???"
                    print(f"  -> {title}")

                    zotero_item = crossref_to_zotero(cr_data, identifier, collection_key)
                    if args.dry_run:
                        results_log.append({"id": identifier, "title": title, "status": "would_import_crossref"})
                        success_count += 1
                    else:
                        if zotero_create_item(zotero_item):
                            print("  -> Imported to Zotero (via CrossRef)")
                            success_count += 1
                            results_log.append({"id": identifier, "title": title, "status": "imported_crossref"})
                        else:
                            print("  -> FAILED to import")
                            fail_count += 1
                            results_log.append({"id": identifier, "title": title, "status": "failed"})
                else:
                    print("  -> NOT FOUND in S2 or CrossRef")
                    fail_count += 1
                    results_log.append({"id": identifier, "status": "not_found"})
            else:
                print("  -> NOT FOUND in Semantic Scholar")
                fail_count += 1
                results_log.append({"id": identifier, "status": "not_found"})

        # Rate limiting
        if i < len(raw_ids):
            time.sleep(args.delay)

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"DONE. Imported: {success_count} | Failed: {fail_count} | Skipped: {skip_count}")
    if collection_key:
        print(f"Collection: '{args.collection}' (key: {collection_key})")
    if args.dry_run:
        print("(DRY RUN — nothing was written to Zotero)")
    print("=" * 60)

    # Save log
    log_path = ids_file.parent / "zotero_import_log.json"
    with open(log_path, "w") as f:
        json.dump({
            "collection": args.collection,
            "collection_key": collection_key,
            "imported": success_count,
            "failed": fail_count,
            "details": results_log,
        }, f, indent=2)
    print(f"\nImport log saved to: {log_path}")

    # Remind about PDFs
    if not args.dry_run and success_count > 0:
        print(
            "\nNEXT STEP: In Zotero, select all items in the collection,\n"
            "right-click -> 'Find Available PDF(s)' to auto-download PDFs."
        )


if __name__ == "__main__":
    main()
