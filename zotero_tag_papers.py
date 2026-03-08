#!/usr/bin/env python3
"""
Step 3.1: Automatically tag papers in Zotero by role and tier.

Reads the paper categories and tiers from step2_1_output.md mappings,
then applies tags to matching papers in the Zotero collection via the local API.

Requirements:
  - Zotero desktop must be running
  - Papers must already be imported (via zotero_auto_import.py or magic wand)

Usage:
  python3 zotero_tag_papers.py
  python3 zotero_tag_papers.py --collection "Workshop Validation Paper"
  python3 zotero_tag_papers.py --dry-run
"""

import argparse
import json
import re
import sys
import time

import requests

ZOTERO_BASE = "http://localhost:23119/api"

# ---------------------------------------------------------------------------
# Paper → tag mappings (from step2_1_output.md)
# ---------------------------------------------------------------------------

# Category → role tags
CATEGORY_ROLE_TAGS = {
    "A": ["methods", "evaluation", "lipsync-benchmark"],
    "B": ["methods", "evaluation", "voice-cloning-benchmark"],
    "C": ["evaluation", "metrics-validation"],
    "D": ["related-work", "emotional-talking-heads"],
    "E": ["related-work", "emotion-congruence"],
    "F": ["related-work", "combined-pipeline"],
    "G": ["motivation", "survey"],
    "H": ["tool-candidate"],
    "I": ["related-work", "terminology-expansion"],
    "J": ["related-work", "citation-graph"],
}

# Tier assignments (from step2_1_output.md tiering)
READ_IN_FULL = [
    "THEval",                          # A1
    "ClonEval",                        # B1
    "Comparative Study of Perceptual", # C1
    "Stabilized Synchronization Loss", # D1
    "AV-Deepfake1M++",                # F1
    "Faces that Speak",                # I2
    "Audio-Visual Speech Representation Expert", # I3
]

SKIM_CITE = [
    "Advancing Talking Head Generation",           # G1 survey
    "Voice Cloning: Comprehensive Survey",         # G2 survey
    "From Pixels to Portraits",                    # G3 survey
    "Survey of Audio Synthesis and Lip-syncing",   # G4 survey
    "Deepfake Generation and Detection",           # G5 survey
    "Audio-Driven Facial Animation with Deep",     # G6 survey
    "Multilingual Video Dubbing",                  # G7 survey
    "Deep Learning for Visual Speech Analysis",    # G8 survey
    "Talking Human Face Generation",               # G9 survey
    "Lightweight Pipeline",                        # F2
    "Real-Time Lip-Sync with AI-Driven",          # F3
]

# Everything else is read-abstract tier

# arXiv ID / DOI → category mapping (from zotero_import_ids.txt order)
ID_TO_CATEGORY = {
    # A. Lipsync benchmarking
    "2511.04520": "A", "2505.21448": "A", "10.1111/cgf.70073": "A",
    "2410.10122": "A", "2412.09262": "A", "10.3390/electronics14173487": "A",
    # B. Voice cloning benchmarking
    "2504.20581": "B", "2602.00443": "B", "2505.23009": "B",
    # C. Metrics vs. human perception
    "2403.06421": "C", "2404.07336": "C", "2404.09003": "C",
    # D. Emotional talking heads
    "2307.09368": "D", "10.1007/978-3-030-58589-1_42": "D",
    "2309.04946": "D", "2408.07889": "D",
    "10.1007/978-981-96-0917-8_8": "D", "2410.00316": "D", "2412.08988": "D",
    # E. Emotion congruence
    "2003.06711": "E", "10.1109/ICME.2008.4607596": "E",
    "10.1109/TMM.2009.2012357": "E", "10.3390/app122412852": "E",
    "10.1002/acp.70141": "E", "2506.13477": "E",
    # F. Combined pipelines
    "2507.20579": "F", "2509.12831": "F",
    "10.1109/IMSA65733.2025.11167849": "F", "2206.04523": "F", "2110.03342": "F",
    # G. Surveys
    "2507.02900": "G", "2505.00579": "G", "2308.16041": "G",
    "10.4108/eai.14-4-2021.169187": "G", "2403.17881": "G",
    "10.3390/info15110675": "G", "10.3389/frsip.2023.1230755": "G",
    "2205.10839": "G", "10.1016/j.eswa.2023.119678": "G",
    # H. Candidate tools
    "2008.10010": "H", "2308.09716": "H", "2305.05445": "H",
    "2504.04427": "H", "2104.01818": "H",
    # I. Terminology expansion
    "2405.10272": "I", "2405.04327": "I", "2402.17485": "I",
    "2404.10667": "I", "2409.02634": "I", "2501.01808": "I",
    "2503.23660": "I", "2602.09534": "I", "2403.06375": "I",
    "10.1109/WACV61041.2025.00474": "I",
    # J. Citation graph papers
    "10.26599/CVM.2025.9450491": "J", "2408.03284": "J",
    "2311.17590": "J", "2410.06885": "J",
}


def check_zotero_running() -> bool:
    try:
        r = requests.get(f"{ZOTERO_BASE}/users/0/collections", timeout=3)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def get_collection_items(collection_key: str | None = None) -> list[dict]:
    """Get all items from a collection or the entire library."""
    if collection_key:
        url = f"{ZOTERO_BASE}/users/0/collections/{collection_key}/items"
    else:
        url = f"{ZOTERO_BASE}/users/0/items"

    all_items = []
    start = 0
    limit = 100

    while True:
        r = requests.get(url, params={"start": start, "limit": limit, "format": "json"})
        if r.status_code != 200:
            print(f"  [WARN] HTTP {r.status_code} fetching items")
            break
        items = r.json()
        if not items:
            break
        all_items.extend(items)
        start += len(items)
        if len(items) < limit:
            break

    return all_items


def find_collection(name: str) -> str | None:
    r = requests.get(f"{ZOTERO_BASE}/users/0/collections")
    if r.status_code != 200:
        return None
    for c in r.json():
        data = c.get("data", c)
        if data.get("name") == name:
            return data.get("key")
    return None


def extract_identifiers(item: dict) -> list[str]:
    """Extract DOI and arXiv ID from a Zotero item."""
    data = item.get("data", item)
    ids = []

    # DOI field
    doi = data.get("DOI", "")
    if doi:
        # Normalize: remove URL prefix if present
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        ids.append(doi)

    # arXiv in extra field
    extra = data.get("extra", "")
    arxiv_match = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", extra)
    if arxiv_match:
        ids.append(arxiv_match.group(1))

    # arXiv in URL
    url = data.get("url", "")
    arxiv_url_match = re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", url)
    if arxiv_url_match:
        ids.append(arxiv_url_match.group(1))

    return ids


def determine_tier(title: str) -> str:
    """Determine the reading tier for a paper based on its title."""
    for keyword in READ_IN_FULL:
        if keyword.lower() in title.lower():
            return "read-in-full"
    for keyword in SKIM_CITE:
        if keyword.lower() in title.lower():
            return "skim-cite"
    return "read-abstract"


def determine_category(identifiers: list[str]) -> str | None:
    """Find the category letter for a paper based on its identifiers."""
    for ident in identifiers:
        if ident in ID_TO_CATEGORY:
            return ID_TO_CATEGORY[ident]
    return None


def add_tags_to_item(item_key: str, item_version: int, new_tags: list[str], existing_tags: list[dict]) -> bool:
    """Add tags to an existing Zotero item (merges with existing tags)."""
    # Merge: keep existing + add new (avoid duplicates)
    existing_tag_names = {t.get("tag", "") for t in existing_tags}
    merged_tags = list(existing_tags)
    for tag in new_tags:
        if tag not in existing_tag_names:
            merged_tags.append({"tag": tag})

    if len(merged_tags) == len(existing_tags):
        return True  # Nothing to add

    r = requests.patch(
        f"{ZOTERO_BASE}/users/0/items/{item_key}",
        headers={
            "Content-Type": "application/json",
            "If-Unmodified-Since-Version": str(item_version),
        },
        json={"tags": merged_tags},
    )
    return r.status_code in (200, 204)


def main():
    parser = argparse.ArgumentParser(description="Step 3.1: Tag Zotero papers by role and tier")
    parser.add_argument("--collection", default=None, help="Zotero collection name (default: all library items)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be tagged without writing")
    args = parser.parse_args()

    if not args.dry_run:
        if not check_zotero_running():
            print("ERROR: Zotero is not running. Open Zotero desktop and re-run.")
            sys.exit(1)
        print("Zotero is running.\n")

    # Find collection
    collection_key = None
    if args.collection:
        collection_key = find_collection(args.collection)
        if collection_key:
            print(f"Found collection '{args.collection}' (key: {collection_key})")
        else:
            print(f"Collection '{args.collection}' not found. Searching entire library.")

    # Get items
    items = get_collection_items(collection_key)
    print(f"Found {len(items)} items in {'collection' if collection_key else 'library'}\n")

    tagged = 0
    skipped = 0
    unmatched = 0

    for item in items:
        data = item.get("data", item)
        item_type = data.get("itemType", "")

        # Skip attachments, notes, etc.
        if item_type in ("attachment", "note", "annotation"):
            continue

        title = data.get("title", "Unknown")
        item_key = data.get("key", "")
        item_version = data.get("version", 0)
        existing_tags = data.get("tags", [])

        # Extract identifiers
        identifiers = extract_identifiers(item)

        # Determine category and tier
        category = determine_category(identifiers)
        tier = determine_tier(title)

        # Build tag list
        new_tags = [tier]
        if category:
            role_tags = CATEGORY_ROLE_TAGS.get(category, [])
            new_tags.extend(role_tags)
        else:
            unmatched += 1

        # Check if all tags already exist
        existing_tag_names = {t.get("tag", "") for t in existing_tags}
        tags_to_add = [t for t in new_tags if t not in existing_tag_names]

        if not tags_to_add:
            skipped += 1
            continue

        print(f"  {title[:70]}")
        print(f"    IDs: {identifiers}")
        print(f"    Category: {category or '?'} | Tier: {tier}")
        print(f"    Adding tags: {tags_to_add}")

        if not args.dry_run:
            if add_tags_to_item(item_key, item_version, new_tags, existing_tags):
                print(f"    -> Tagged")
                tagged += 1
            else:
                print(f"    -> FAILED")
        else:
            tagged += 1

    print(f"\n{'=' * 60}")
    print(f"DONE. Tagged: {tagged} | Already tagged: {skipped} | Unmatched: {unmatched}")
    if args.dry_run:
        print("(DRY RUN — nothing was written to Zotero)")
    if unmatched:
        print(f"\n{unmatched} items could not be matched to a category.")
        print("These may be papers added manually or from Step 2.4 citations.")
    print("=" * 60)


if __name__ == "__main__":
    main()
