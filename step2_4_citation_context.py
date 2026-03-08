#!/usr/bin/env python3
"""
Step 2.4: Check Citation Context and Limitations
=================================================

Uses Semantic Scholar API to find how the top 5 papers from Steps 2.1+2.2
are cited by other work. Extracts:
  - Citation context snippets (what other papers say about them)
  - Citation intent (background, methodology, result comparison)
  - Influential citation flags
  - Limitations and criticisms mentioned by citing papers

Produces a structured output file for Step 2.5.

Usage:
  python3 step2_4_citation_context.py
  python3 step2_4_citation_context.py --s2-key YOUR_KEY
  python3 step2_4_citation_context.py --s2-key YOUR_KEY --output step2_4_output.md
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

S2_BASE = "https://api.semanticscholar.org/graph/v1"

# ---------------------------------------------------------------------------
# Top 5 papers from Steps 2.1+2.2 (closest to the gaps)
# Edit these if your top 5 are different.
# ---------------------------------------------------------------------------
TOP_PAPERS = [
    {
        "id": "ARXIV:2511.04520",
        "label": "A1",
        "short": "THEval (2025)",
        "why": "Benchmarks 17 lipsync models with 8 metrics, 0.870 Spearman with human ratings",
    },
    {
        "id": "ARXIV:2504.20581",
        "label": "B1",
        "short": "ClonEval (2025)",
        "why": "Benchmarks 5 VC systems on neutral + emotional datasets",
    },
    {
        "id": "ARXIV:2403.06421",
        "label": "C1",
        "short": "Perceptual Quality Metrics for TH Videos (ICIP 2024)",
        "why": "Shows LSE-C/LSE-D correlate poorly with human preferences",
    },
    {
        "id": "ARXIV:2307.09368",
        "label": "D1",
        "short": "Stabilized Sync Loss (ECCV 2024)",
        "why": "Documents SyncNet bias toward neutral faces",
    },
    {
        "id": "ARXIV:2507.20579",
        "label": "F1",
        "short": "AV-Deepfake1M++ (ACM MM 2025)",
        "why": "Uses 5 TTS + 3 lipsync tools — closest to your pipeline design",
    },
]


def s2_request_with_retry(url: str, params: dict, api_key: str | None = None, max_retries: int = 5) -> requests.Response | None:
    """Make a Semantic Scholar API request with exponential backoff on 429."""
    headers = {"x-api-key": api_key} if api_key else {}
    wait = 10

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                print(f"    [429 rate limited, attempt {attempt}/{max_retries}] waiting {wait}s...")
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            print(f"    [HTTP {r.status_code}] {r.text[:200]}")
            return None
        except requests.RequestException as e:
            print(f"    [ERROR] {e}")
            return None
    print(f"    [FAILED] Max retries exceeded")
    return None


def fetch_paper_details(paper_id: str, api_key: str | None = None) -> dict | None:
    """Fetch basic paper info (title, year, citation count)."""
    fields = "title,year,citationCount,externalIds,url"
    r = s2_request_with_retry(
        f"{S2_BASE}/paper/{paper_id}",
        params={"fields": fields},
        api_key=api_key,
    )
    if r:
        return r.json()
    return None


def fetch_citations(paper_id: str, api_key: str | None = None, limit: int = 100) -> list[dict]:
    """
    Fetch citations of a paper with context and intent.
    Returns list of citing papers with their context snippets.
    """
    fields = "title,year,citationCount,contexts,intents,isInfluential,externalIds,url"
    all_citations = []
    offset = 0

    while offset < limit:
        batch_size = min(100, limit - offset)
        r = s2_request_with_retry(
            f"{S2_BASE}/paper/{paper_id}/citations",
            params={"fields": fields, "limit": batch_size, "offset": offset},
            api_key=api_key,
        )
        if r:
            data = r.json()
            batch = data.get("data", [])
            if not batch:
                break
            all_citations.extend(batch)
            offset += len(batch)
            if len(batch) < batch_size:
                break
        else:
            break

        time.sleep(3)  # rate limit courtesy

    return all_citations


def analyze_citation(citation: dict) -> dict:
    """Analyze a single citation for relevance signals."""
    citing_paper = citation.get("citingPaper", {})
    contexts = citation.get("contexts", []) or []
    intents = citation.get("intents", []) or []
    is_influential = citation.get("isInfluential", False)

    # Look for limitation/criticism keywords in context snippets
    limitation_keywords = [
        r"\blimit\w*\b", r"\bfail\w*\b", r"\bshortcoming\b", r"\bweakness\b",
        r"\bdrawback\b", r"\bbias\w*\b", r"\bpoor\w*\b", r"\bnot\s+account\b",
        r"\bneglect\b", r"\bignore[sd]?\b", r"\black\w*\b", r"\binsufficient\b",
        r"\binadequat\w*\b", r"\boverlooked?\b", r"\bunreliab\w*\b",
        r"\binconsisten\w*\b", r"\bdisagreement\b", r"\bcontradicts?\b",
        r"\bflawed?\b", r"\bnarrow\b", r"\brestrict\w*\b", r"\bnot\s+generaliz\w*\b",
        r"\bhowever\b", r"\bdespite\b", r"\balthough\b", r"\bnevertheless\b",
        r"\bunlike\b", r"\bin\s+contrast\b", r"\bon\s+the\s+other\s+hand\b",
        r"\bfuture\s+work\b", r"\bremains?\s+open\b", r"\bopen\s+question\b",
        r"\bopen\s+problem\b", r"\bopen\s+challenge\b",
    ]

    # Score contexts for potential criticism/limitation signals
    critical_contexts = []
    neutral_contexts = []
    future_work_mentions = []

    for ctx in contexts:
        if not ctx:
            continue
        ctx_lower = ctx.lower()
        matches = [kw for kw in limitation_keywords if re.search(kw, ctx_lower)]
        if any(re.search(kw, ctx_lower) for kw in [r"\bfuture\s+work\b", r"\bremains?\s+open\b", r"\bopen\s+question\b"]):
            future_work_mentions.append(ctx)
        elif matches:
            critical_contexts.append({"text": ctx, "signals": [m for m in matches]})
        else:
            neutral_contexts.append(ctx)

    return {
        "title": citing_paper.get("title", "Unknown"),
        "year": citing_paper.get("year"),
        "citations": citing_paper.get("citationCount", 0),
        "url": citing_paper.get("url", ""),
        "ext_ids": citing_paper.get("externalIds", {}),
        "intents": intents,
        "is_influential": is_influential,
        "critical_contexts": critical_contexts,
        "future_work_mentions": future_work_mentions,
        "neutral_contexts": neutral_contexts,
        "all_contexts": contexts,
    }


def format_output_md(results: list[dict], output_path: str):
    """Format the results as a markdown file for Step 2.5."""
    lines = []
    lines.append("# Step 2.4 Output: Citation Context and Limitations\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    # Summary of new papers discovered
    all_new_papers = []
    all_limitations = []

    for result in results:
        paper = result["paper"]
        citations = result["analyzed_citations"]
        lines.append(f"## {paper['label']}: {paper['short']}\n")
        lines.append(f"**Why top 5:** {paper['why']}\n")

        details = result.get("details")
        if details:
            lines.append(f"**Total citations:** {details.get('citationCount', '?')}\n")
        lines.append(f"**Citations analyzed:** {len(citations)}\n")

        # Influential citations
        influential = [c for c in citations if c["is_influential"]]
        lines.append(f"**Influential citations:** {len(influential)}\n")

        # --- Limitations / Critical mentions ---
        critical = [c for c in citations if c["critical_contexts"]]
        lines.append(f"\n### Limitations and criticisms ({len(critical)} citing papers)\n")

        if critical:
            for c in critical[:10]:  # top 10 most relevant
                ext_ids = c.get("ext_ids", {})
                doi = ext_ids.get("DOI", "")
                arxiv = ext_ids.get("ArXiv", "")
                id_str = f"DOI:{doi}" if doi else (f"arXiv:{arxiv}" if arxiv else "")

                lines.append(f"- **{c['title']}** ({c['year']}) {id_str}")
                if c["is_influential"]:
                    lines.append("  - *Influential citation*")
                for ctx in c["critical_contexts"][:3]:
                    text = ctx["text"][:500]
                    lines.append(f'  - > "{text}"')
                lines.append("")

                # Track for global limitations
                for ctx in c["critical_contexts"]:
                    all_limitations.append({
                        "about": paper["short"],
                        "from": c["title"],
                        "from_year": c["year"],
                        "context": ctx["text"][:300],
                    })
        else:
            lines.append("No critical/contrastive citations found.\n")

        # --- Future work mentions ---
        future_work = [c for c in citations if c["future_work_mentions"]]
        if future_work:
            lines.append(f"\n### Future work mentions ({len(future_work)} citing papers)\n")
            for c in future_work[:5]:
                lines.append(f"- **{c['title']}** ({c['year']})")
                for fw in c["future_work_mentions"][:2]:
                    lines.append(f'  - > "{fw[:500]}"')
                lines.append("")

        # --- Methodological citations (how others use this paper) ---
        methodology = [c for c in citations if "methodology" in c["intents"]]
        if methodology:
            lines.append(f"\n### Used as methodology reference ({len(methodology)} papers)\n")
            for c in methodology[:5]:
                lines.append(f"- {c['title']} ({c['year']})")
            lines.append("")

        # --- Result comparison citations ---
        result_cmp = [c for c in citations if "result" in c["intents"]]
        if result_cmp:
            lines.append(f"\n### Cited for result comparison ({len(result_cmp)} papers)\n")
            for c in result_cmp[:5]:
                lines.append(f"- {c['title']} ({c['year']})")
                for ctx in (c["critical_contexts"] + [{"text": nc} for nc in c["neutral_contexts"]])[:2]:
                    text = ctx["text"][:400] if isinstance(ctx, dict) else ctx[:400]
                    lines.append(f'  - > "{text}"')
            lines.append("")

        # --- New papers worth adding ---
        # Papers that cite this work AND are influential AND recent
        new_candidates = [
            c for c in citations
            if c["is_influential"]
            and c.get("year", 0) and c["year"] >= 2024
            and c["citations"] >= 3
        ]
        new_candidates.sort(key=lambda x: x.get("citations", 0), reverse=True)

        if new_candidates:
            lines.append(f"\n### New papers to consider adding ({len(new_candidates[:5])} most relevant)\n")
            for c in new_candidates[:5]:
                ext_ids = c.get("ext_ids", {})
                doi = ext_ids.get("DOI", "")
                arxiv = ext_ids.get("ArXiv", "")
                id_str = doi if doi else (arxiv if arxiv else "")

                lines.append(f"- **{c['title']}** ({c['year']}, {c['citations']} cites) — {id_str}")
                all_new_papers.append({
                    "title": c["title"],
                    "year": c["year"],
                    "citations": c["citations"],
                    "id": id_str,
                    "found_via": paper["short"],
                })
            lines.append("")

        lines.append("---\n")

    # --- Global summary ---
    lines.append("## Summary for Step 2.5\n")

    lines.append("### Consolidated limitations\n")
    if all_limitations:
        # Deduplicate and group
        seen = set()
        for lim in all_limitations:
            key = lim["context"][:100]
            if key not in seen:
                seen.add(key)
                lines.append(f"- **About {lim['about']}** (from {lim['from']}, {lim['from_year']}):")
                lines.append(f'  > "{lim["context"]}"')
                lines.append("")
    else:
        lines.append("No explicit limitations found in citation contexts.\n")

    lines.append("### New papers discovered (add to collection)\n")
    if all_new_papers:
        # Deduplicate by title
        seen_titles = set()
        unique_new = []
        for p in all_new_papers:
            if p["title"] not in seen_titles:
                seen_titles.add(p["title"])
                unique_new.append(p)

        unique_new.sort(key=lambda x: x.get("citations", 0), reverse=True)
        for p in unique_new[:10]:
            lines.append(f"- {p['title']} ({p['year']}, {p['citations']} cites) — {p['id']} [via {p['found_via']}]")
        lines.append("")

        # Also output IDs for Zotero import
        lines.append("### Identifiers for Zotero import\n")
        lines.append("```")
        for p in unique_new[:10]:
            if p["id"]:
                lines.append(p["id"])
        lines.append("```\n")
    else:
        lines.append("No new highly-cited papers found via citation analysis.\n")

    # Write
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return all_limitations, all_new_papers


def main():
    parser = argparse.ArgumentParser(
        description="Step 2.4: Citation context and limitations via Semantic Scholar"
    )
    parser.add_argument(
        "--s2-key",
        default=None,
        help="Semantic Scholar API key (recommended to avoid rate limits)",
    )
    parser.add_argument(
        "--output",
        default="step2_4_output.md",
        help="Output markdown file (default: step2_4_output.md)",
    )
    parser.add_argument(
        "--max-citations",
        type=int,
        default=100,
        help="Max citations to fetch per paper (default: 100)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Seconds between API calls (default: 3.0)",
    )
    args = parser.parse_args()

    s2_key = args.s2_key or os.environ.get("S2_API_KEY")
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_path

    if not s2_key:
        print(
            "WARNING: No Semantic Scholar API key provided.\n"
            "  You may hit rate limits. Get a free key at:\n"
            "  https://www.semanticscholar.org/product/api#api-key-form\n"
            "  Pass it with --s2-key YOUR_KEY or set S2_API_KEY env var.\n"
        )

    print("=" * 60)
    print("Step 2.4: Citation Context and Limitations")
    print("=" * 60)
    print(f"Analyzing {len(TOP_PAPERS)} papers...\n")

    results = []

    for i, paper in enumerate(TOP_PAPERS, 1):
        print(f"\n[{i}/{len(TOP_PAPERS)}] {paper['label']}: {paper['short']}")
        print(f"  ID: {paper['id']}")

        # Get paper details (citation count)
        details = fetch_paper_details(paper["id"], api_key=s2_key)
        if details:
            ccount = details.get("citationCount", 0)
            print(f"  Total citations: {ccount}")
        else:
            print("  Could not fetch paper details")
            ccount = 0

        time.sleep(args.delay)

        # Fetch citations with context
        if ccount == 0:
            print("  No citations to analyze (paper may be too new)")
            results.append({
                "paper": paper,
                "details": details,
                "analyzed_citations": [],
            })
            continue

        print(f"  Fetching up to {min(args.max_citations, ccount)} citations with context...")
        raw_citations = fetch_citations(paper["id"], api_key=s2_key, limit=args.max_citations)
        print(f"  Got {len(raw_citations)} citations")

        time.sleep(args.delay)

        # Analyze each citation
        analyzed = []
        for cit in raw_citations:
            analyzed.append(analyze_citation(cit))

        # Stats
        influential_count = sum(1 for a in analyzed if a["is_influential"])
        critical_count = sum(1 for a in analyzed if a["critical_contexts"])
        future_count = sum(1 for a in analyzed if a["future_work_mentions"])

        print(f"  Influential: {influential_count} | Critical/contrastive: {critical_count} | Future work: {future_count}")

        results.append({
            "paper": paper,
            "details": details,
            "analyzed_citations": analyzed,
        })

    # Generate output
    print(f"\n\nWriting output to {output_path}...")
    limitations, new_papers = format_output_md(results, str(output_path))

    print(f"\nDONE.")
    print(f"  Limitations found: {len(limitations)}")
    print(f"  New papers discovered: {len(new_papers)}")
    print(f"  Output: {output_path}")
    print(f"\nNext step: Use {output_path} as input for Step 2.5 (Crystallize Research Question)")


if __name__ == "__main__":
    main()
