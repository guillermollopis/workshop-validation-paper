#!/usr/bin/env python3
"""
Step 3.2: Grounded Q&A on research papers via Gemini API (File Search).

Replaces manual NotebookLM usage with fully automated Gemini API calls.
Uploads PDFs to a Gemini File Search Store, asks research questions,
and saves grounded answers with citations.

Setup:
  1. Get a free API key at https://aistudio.google.com/apikey
  2. Either export it:  export GEMINI_API_KEY=your_key
     or pass it:        --api-key your_key

Requirements:
  pip install google-genai

Usage:
  python3 step3_2_gemini_qa.py --pdf-dir /path/to/pdfs
  python3 step3_2_gemini_qa.py --pdf-dir /path/to/pdfs --api-key YOUR_KEY
  python3 step3_2_gemini_qa.py --pdf-dir /path/to/pdfs --questions step3_2_questions.txt
  python3 step3_2_gemini_qa.py --pdf-dir /path/to/pdfs --model gemini-2.5-flash
"""

import argparse
import os
import sys
import time
import json
import glob
from pathlib import Path
from datetime import datetime

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed. Run: pip install google-genai")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Default questions (from step3_2_notebooklm_questions.md)
# ---------------------------------------------------------------------------

DEFAULT_QUESTIONS = [
    # For experimental design (Step 4)
    {
        "category": "Experimental Design",
        "question": "What exact computational metrics did each of these papers use to evaluate lip synchronization quality? List every metric name, what it measures, and which paper used it.",
    },
    {
        "category": "Experimental Design",
        "question": "What exact computational metrics did each of these papers use to evaluate voice/audio quality? List every metric name, what it measures, and which paper used it.",
    },
    {
        "category": "Experimental Design",
        "question": "What human evaluation methods did these papers use? For each paper that included a human study: what was the study design (MOS, A/B preference, Likert scale, etc.), how many participants, and what did they ask participants to judge?",
    },
    {
        "category": "Experimental Design",
        "question": "What datasets did each paper use for evaluation? For each dataset mentioned: how many samples, what types of speech (neutral, emotional, multilingual), and what video characteristics (resolution, length, number of speakers)?",
    },
    {
        "category": "Experimental Design",
        "question": "What sample sizes were used in each paper's experiments? This means: how many models compared, how many video clips generated, how many stimuli per condition, and how many human evaluators (if applicable)?",
    },
    {
        "category": "Experimental Design",
        "question": "Did any of these papers report effect sizes, confidence intervals, or correlation coefficients? If so, list the exact values and what they measured.",
    },
    # For gap verification
    {
        "category": "Gap Verification",
        "question": "Do any of these papers benchmark multiple voice cloning systems combined with multiple lip sync systems on the same stimuli? If not, what is the closest any paper comes to this?",
    },
    {
        "category": "Gap Verification",
        "question": "Do any of these papers compare quality between emotional and neutral speech conditions using the same generation systems? What did they find about emotional vs neutral performance?",
    },
    {
        "category": "Gap Verification",
        "question": "What do these papers say about the limitations of LSE-C and LSE-D metrics? What alternative sync metrics do they propose or recommend?",
    },
    {
        "category": "Gap Verification",
        "question": "Do any of these papers mention the interaction between voice cloning quality and lip sync quality — for example, does a better voice clone produce better lip sync, or are they independent?",
    },
    # For writing (Introduction, Related Work, Discussion)
    {
        "category": "Writing",
        "question": "What motivations do these papers give for why talking head evaluation is important? Summarize the key arguments for the significance of this research area.",
    },
    {
        "category": "Writing",
        "question": "What do these papers identify as open challenges or future work in talking head generation and evaluation?",
    },
    {
        "category": "Writing",
        "question": "Based on these papers, what is the current state of the art in lip sync evaluation? What are the recognized limitations?",
    },
]


def load_custom_questions(filepath: str) -> list[dict]:
    """Load questions from a text file (one question per line, # comments)."""
    questions = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            questions.append({"category": "Custom", "question": line})
    return questions


def find_pdfs(pdf_dir: str, patterns: list[str] | None = None) -> list[Path]:
    """Find all PDF files in a directory."""
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        print(f"ERROR: PDF directory not found: {pdf_dir}")
        sys.exit(1)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"ERROR: No PDF files found in {pdf_dir}")
        print("  Make sure your papers are downloaded as PDFs.")
        print("  In Zotero: select all → right-click → 'Find Available PDF(s)'")
        print("  Then find them in your Zotero storage folder.")
        sys.exit(1)

    return pdfs


def create_file_search_store(client, store_name: str) -> str:
    """Create a Gemini File Search Store."""
    store = client.file_search_stores.create(
        config={"display_name": store_name}
    )
    print(f"  Created File Search Store: {store.name}")
    return store.name


def upload_pdf_to_store(client, store_name: str, pdf_path: Path) -> bool:
    """Upload a single PDF to the File Search Store."""
    try:
        operation = client.file_search_stores.upload_to_file_search_store(
            file=str(pdf_path),
            file_search_store_name=store_name,
            config={"display_name": pdf_path.stem},
        )

        # Wait for processing
        timeout = 120  # 2 minutes per file
        start = time.time()
        while not operation.done:
            if time.time() - start > timeout:
                print(f"    [TIMEOUT] Processing took too long")
                return False
            time.sleep(3)
            operation = client.operations.get(operation)

        return True
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False


def ask_question(client, model: str, store_name: str, question: str) -> dict:
    """Ask a question grounded in the File Search Store."""
    try:
        response = client.models.generate_content(
            model=model,
            contents=question,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name]
                        )
                    )
                ]
            ),
        )

        # Extract answer text
        answer_text = response.text if response.text else "(No answer generated)"

        # Extract citation/grounding metadata
        citations = []
        if response.candidates and response.candidates[0].grounding_metadata:
            gm = response.candidates[0].grounding_metadata

            # Grounding chunks contain the source passages
            if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    citation = {}
                    if hasattr(chunk, "retrieved_context") and chunk.retrieved_context:
                        rc = chunk.retrieved_context
                        if hasattr(rc, "title"):
                            citation["source"] = rc.title
                        if hasattr(rc, "text"):
                            citation["passage"] = rc.text
                        if hasattr(rc, "uri"):
                            citation["uri"] = rc.uri
                    if citation:
                        citations.append(citation)

            # Grounding supports show which parts of the answer are grounded
            if hasattr(gm, "grounding_supports") and gm.grounding_supports:
                for support in gm.grounding_supports:
                    if hasattr(support, "segment") and support.segment:
                        seg = support.segment
                        # Could extract the specific text span that's grounded
                        pass

        return {
            "answer": answer_text,
            "citations": citations,
            "has_citations": len(citations) > 0,
        }

    except Exception as e:
        return {
            "answer": f"[ERROR] {e}",
            "citations": [],
            "has_citations": False,
        }


def format_output_md(results: list[dict], pdfs_used: list[str], output_path: str):
    """Format all Q&A results as markdown."""
    lines = []
    lines.append("# Step 3.2 Output: Grounded Q&A on Research Papers\n")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Tool: Gemini API (File Search with grounded citations)\n")
    lines.append("---\n")

    lines.append("## Papers uploaded\n")
    for i, pdf in enumerate(pdfs_used, 1):
        lines.append(f"{i}. {pdf}")
    lines.append("")

    lines.append("---\n")

    current_category = None
    for r in results:
        if r["category"] != current_category:
            current_category = r["category"]
            lines.append(f"## {current_category}\n")

        lines.append(f"### Q: {r['question']}\n")
        lines.append(f"{r['answer']}\n")

        if r["citations"]:
            lines.append("**Sources cited:**\n")
            seen = set()
            for cit in r["citations"]:
                source = cit.get("source", "Unknown")
                if source not in seen:
                    seen.add(source)
                    passage = cit.get("passage", "")
                    if passage:
                        # Truncate long passages
                        if len(passage) > 200:
                            passage = passage[:200] + "..."
                        lines.append(f"- **{source}:** \"{passage}\"")
                    else:
                        lines.append(f"- **{source}**")
            lines.append("")
        else:
            lines.append("*No specific source citations returned for this answer.*\n")

        lines.append("---\n")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def cleanup_store(client, store_name: str):
    """Delete all files in a File Search Store, then delete the store."""
    try:
        # List and delete all files in the store first
        files = client.file_search_stores.list_files(file_search_store_name=store_name)
        for f in files:
            try:
                client.file_search_stores.delete_file(
                    file_search_store_name=store_name,
                    file_id=f.name.split("/")[-1] if hasattr(f, "name") else f,
                )
            except Exception:
                pass
        time.sleep(2)
        client.file_search_stores.delete(name=store_name)
        print(f"  Cleaned up File Search Store: {store_name}")
    except Exception as e:
        print(f"  [WARN] Could not fully delete store: {e}")
        print(f"  You can delete it manually at https://aistudio.google.com/")


def main():
    parser = argparse.ArgumentParser(
        description="Step 3.2: Grounded Q&A on research papers via Gemini API"
    )
    parser.add_argument(
        "--pdf-dir",
        required=True,
        help="Directory containing PDF files to upload",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Gemini API key (or set GEMINI_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model to use (default: gemini-2.5-flash)",
    )
    parser.add_argument(
        "--questions",
        default=None,
        help="Custom questions file (one per line). Uses built-in research questions if not provided.",
    )
    parser.add_argument(
        "--output",
        default="step3_2_output.md",
        help="Output markdown file (default: step3_2_output.md)",
    )
    parser.add_argument(
        "--store-name",
        default=None,
        help="Name for the File Search Store (default: auto-generated from project name)",
    )
    parser.add_argument(
        "--keep-store",
        action="store_true",
        help="Keep the File Search Store after completion (for follow-up queries)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=7.0,
        help="Seconds between API calls (default: 7.0 — safe for free tier at 10 RPM)",
    )
    parser.add_argument(
        "--max-pdfs",
        type=int,
        default=20,
        help="Maximum number of PDFs to upload (default: 20)",
    )
    args = parser.parse_args()

    # --- API key ---
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "ERROR: No Gemini API key provided.\n"
            "  Get a free key at: https://aistudio.google.com/apikey\n"
            "  Then either:\n"
            "    export GEMINI_API_KEY=your_key\n"
            "    python3 step3_2_gemini_qa.py --api-key your_key --pdf-dir /path/to/pdfs\n"
        )
        sys.exit(1)

    # --- Initialize client ---
    client = genai.Client(api_key=api_key)

    # --- Find PDFs ---
    pdfs = find_pdfs(args.pdf_dir)
    if len(pdfs) > args.max_pdfs:
        print(f"Found {len(pdfs)} PDFs, limiting to {args.max_pdfs} (use --max-pdfs to change)")
        pdfs = pdfs[:args.max_pdfs]

    print("=" * 60)
    print("Step 3.2: Grounded Q&A via Gemini API")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"PDFs: {len(pdfs)} files from {args.pdf_dir}")
    print()

    # --- Load questions ---
    if args.questions:
        questions = load_custom_questions(args.questions)
        print(f"Loaded {len(questions)} custom questions from {args.questions}")
    else:
        questions = DEFAULT_QUESTIONS
        print(f"Using {len(questions)} built-in research questions")
    print()

    # --- Create File Search Store ---
    store_name_display = args.store_name or f"research-papers-{datetime.now().strftime('%Y%m%d-%H%M')}"
    print("Creating File Search Store...")
    store_name = create_file_search_store(client, store_name_display)
    print()

    # --- Upload PDFs ---
    print(f"Uploading {len(pdfs)} PDFs...")
    uploaded = []
    for i, pdf in enumerate(pdfs, 1):
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"  [{i}/{len(pdfs)}] {pdf.name} ({size_mb:.1f} MB)")

        if upload_pdf_to_store(client, store_name, pdf):
            uploaded.append(pdf.name)
            print(f"    -> Uploaded and indexed")
        else:
            print(f"    -> FAILED")

        if i < len(pdfs):
            time.sleep(2)  # Brief pause between uploads

    print(f"\nUploaded {len(uploaded)}/{len(pdfs)} PDFs successfully")

    if not uploaded:
        print("ERROR: No PDFs were uploaded successfully. Cannot proceed.")
        cleanup_store(client, store_name)
        sys.exit(1)

    # Wait for indexing to complete
    print("Waiting 10s for indexing to complete...")
    time.sleep(10)

    # --- Ask questions ---
    print(f"\nAsking {len(questions)} questions...\n")
    results = []

    for i, q in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {q['category']}: {q['question'][:70]}...")

        result = ask_question(client, args.model, store_name, q["question"])

        answer_preview = result["answer"][:100].replace("\n", " ")
        cit_count = len(result["citations"])
        print(f"    -> {answer_preview}...")
        print(f"    -> {cit_count} citation(s)")

        results.append({
            "category": q["category"],
            "question": q["question"],
            "answer": result["answer"],
            "citations": result["citations"],
            "has_citations": result["has_citations"],
        })

        if i < len(questions):
            time.sleep(args.delay)

    # --- Save output ---
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_path

    format_output_md(results, uploaded, str(output_path))
    print(f"\nOutput saved to: {output_path}")

    # --- Save raw JSON (for downstream processing) ---
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump({
            "model": args.model,
            "store_name": store_name,
            "pdfs_uploaded": uploaded,
            "results": results,
        }, f, indent=2)
    print(f"Raw JSON saved to: {json_path}")

    # --- Cleanup ---
    if not args.keep_store:
        print("\nCleaning up File Search Store...")
        cleanup_store(client, store_name)
    else:
        print(f"\nFile Search Store kept: {store_name}")
        print("Use --keep-store with follow-up queries to reuse it.")

    # --- Summary ---
    answered = sum(1 for r in results if not r["answer"].startswith("[ERROR]"))
    grounded = sum(1 for r in results if r["has_citations"])

    print(f"\n{'=' * 60}")
    print(f"DONE.")
    print(f"  Questions asked: {len(results)}")
    print(f"  Answered: {answered}")
    print(f"  With citations: {grounded}")
    print(f"  Output: {output_path}")
    print(f"\nNext step: Use {output_path} as input for Step 4 (Experimental Design)")
    print("=" * 60)


if __name__ == "__main__":
    main()
