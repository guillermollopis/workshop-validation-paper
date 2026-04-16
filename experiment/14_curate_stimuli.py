#!/usr/bin/env python3
"""
Curate the final stimulus set from screening results.

Reads results/screening.json, selects 1 best fake per cell,
copies source + fake videos into data/curated/ for the experiment.

Usage:
  python3 14_curate_stimuli.py                      # curate with defaults
  python3 14_curate_stimuli.py --include-george      # include George (dropped by default)
  python3 14_curate_stimuli.py --accept-maybe        # also accept "maybe" rated videos
  python3 14_curate_stimuli.py --dry-run             # preview without copying
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


SCREENING_FILE = Path("results/screening.json")
SOURCE_DIR = Path("data/source")
NORMALIZED_DIR = Path("data/normalized")
OVERGENERATED_DIR = Path("data/overgenerated")
CURATED_DIR = Path("data/curated")
MANIFEST_FILE = Path("results/curated_stimuli.json")

DEFAULT_ACTORS = ["Jordi", "Lisset", "Maisa", "Selene"]
ALL_ACTORS = ["George", "Jordi", "Lisset", "Maisa", "Selene"]
EMOTIONS = ["emotional", "neutral"]
CLIPS = ["c01", "c02"]

# Preference order for VC system (pick first available)
VC_PREFERENCE = ["knn_vc", "openvoice_v2"]
LS_SYSTEM = "sonic"


def parse_screening_id(vid_id: str) -> dict:
    """Parse a screening ID like 'knn_vc/sonic/Jordi_emotional_c02_v1' into components."""
    parts = vid_id.split("/")
    if len(parts) < 3:
        return None
    vc_system = parts[0]
    ls_system = parts[1]
    name = parts[2]

    # Parse name: Identity_emotion_clip[_vN]
    m = re.match(r"^(\w+?)_(emotional|neutral)_(c\d+)(?:_v(\d+))?$", name)
    if not m:
        return None

    return {
        "vc_system": vc_system,
        "ls_system": ls_system,
        "identity": m.group(1),
        "emotion": m.group(2),
        "clip_id": m.group(3),
        "variant": m.group(4),  # None if no variant suffix
        "full_name": name,
    }


def find_video_path(parsed: dict) -> Path | None:
    """Find the actual video file for a screening entry."""
    vc = parsed["vc_system"]
    ls = parsed["ls_system"]
    name = parsed["full_name"]

    # Try overgenerated first (has _vN suffix)
    path = OVERGENERATED_DIR / vc / ls / f"{name}.mp4"
    if path.exists():
        return path

    # Try normalized
    path = NORMALIZED_DIR / vc / ls / f"{name}.mp4"
    if path.exists():
        return path

    return None


def get_video_duration(path: str) -> float:
    """Get video duration in seconds."""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "csv=p=0", path]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    try:
        return float(r.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Curate final stimulus set")
    parser.add_argument("--include-george", action="store_true",
                        help="Include George (dropped by default due to poor quality)")
    parser.add_argument("--accept-maybe", action="store_true",
                        help="Accept 'maybe' ratings when no 'keep' exists for a cell")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview selections without copying files")
    parser.add_argument("--output-dir", type=str, default=str(CURATED_DIR))
    parser.add_argument("--exclude", nargs="+", default=[],
                        help="Screening IDs to exclude (e.g., knn_vc/sonic/Selene_neutral_c01)")
    args = parser.parse_args()

    curated_dir = Path(args.output_dir)
    actors = ALL_ACTORS if args.include_george else DEFAULT_ACTORS

    # Load screening data
    if not SCREENING_FILE.exists():
        print(f"ERROR: {SCREENING_FILE} not found. Run 09_screen_stimuli.py first.")
        return

    screening = json.loads(SCREENING_FILE.read_text())
    ratings = screening.get("ratings", {})

    # Index keeps and maybes by cell
    # cell = (identity, emotion, clip_id) -> list of {vid_id, vc_system, variant, path, rating}
    cell_candidates = {}

    exclude_set = set(args.exclude)

    for vid_id, rating in ratings.items():
        if rating not in ("keep", "maybe"):
            continue
        if vid_id in exclude_set:
            continue

        parsed = parse_screening_id(vid_id)
        if not parsed:
            continue
        if parsed["ls_system"] != LS_SYSTEM:
            continue
        if parsed["identity"] not in actors:
            continue

        path = find_video_path(parsed)
        if not path:
            print(f"  WARNING: Video not found for {vid_id}")
            continue

        cell = (parsed["identity"], parsed["emotion"], parsed["clip_id"])
        if cell not in cell_candidates:
            cell_candidates[cell] = []
        cell_candidates[cell].append({
            "vid_id": vid_id,
            "vc_system": parsed["vc_system"],
            "variant": parsed["variant"],
            "path": path,
            "rating": rating,
        })

    # Select 1 best per cell
    print("=" * 60)
    print("Stimulus Curation")
    print(f"  Actors: {actors}")
    print(f"  Lipsync: {LS_SYSTEM}")
    print(f"  Accept maybe: {args.accept_maybe}")
    print("=" * 60)

    selected = {}
    missing = []

    for actor in actors:
        for emotion in EMOTIONS:
            for clip in CLIPS:
                cell = (actor, emotion, clip)
                candidates = cell_candidates.get(cell, [])

                # Filter: keeps first, then maybes if allowed
                keeps = [c for c in candidates if c["rating"] == "keep"]
                maybes = [c for c in candidates if c["rating"] == "maybe"]

                pool = keeps
                if not pool and args.accept_maybe:
                    pool = maybes

                if not pool:
                    status = f"MISSING (keeps={len(keeps)}, maybes={len(maybes)})"
                    print(f"  {actor:<8} {emotion:<10} {clip}  {status}")
                    missing.append(cell)
                    continue

                # Pick best: prefer VC in order of VC_PREFERENCE
                best = None
                for vc_pref in VC_PREFERENCE:
                    vc_pool = [c for c in pool if c["vc_system"] == vc_pref]
                    if vc_pool:
                        best = vc_pool[0]  # first available
                        break
                if not best:
                    best = pool[0]

                selected[cell] = best
                print(f"  {actor:<8} {emotion:<10} {clip}  -> {best['vid_id']} ({best['rating']})")

    # Summary
    total_cells = len(actors) * len(EMOTIONS) * len(CLIPS)
    print(f"\nSelected: {len(selected)}/{total_cells} cells")
    if missing:
        print(f"Missing:  {len(missing)} cells:")
        for m in missing:
            print(f"  {m[0]} {m[1]} {m[2]}")

    if missing and not args.accept_maybe:
        print(f"\nTip: Run with --accept-maybe to use 'maybe' rated videos for missing cells")
        maybe_fills = 0
        for m in missing:
            candidates = cell_candidates.get(m, [])
            if any(c["rating"] == "maybe" for c in candidates):
                maybe_fills += 1
        if maybe_fills:
            print(f"  {maybe_fills}/{len(missing)} missing cells have 'maybe' candidates")

    if args.dry_run:
        print("\n[DRY RUN] No files copied.")
        return

    if not selected:
        print("\nNo videos selected. Nothing to copy.")
        return

    # Create curated directory
    source_out = curated_dir / "source"
    fake_out = curated_dir / "fake"
    source_out.mkdir(parents=True, exist_ok=True)
    fake_out.mkdir(parents=True, exist_ok=True)

    # Copy files
    print(f"\nCopying to {curated_dir}/...")
    manifest = {"stimuli": {}, "actors": actors, "design": {
        "actors": len(actors), "emotions": 2, "clips_per_cell": 2,
        "total_cells": len(selected), "lipsync": LS_SYSTEM,
    }}

    for cell, info in sorted(selected.items()):
        actor, emotion, clip = cell
        cell_name = f"{actor}_{emotion}_{clip}"

        # Copy source (real) video
        src_video = NORMALIZED_DIR / "source" / f"{cell_name}.mp4"
        if not src_video.exists():
            src_video = SOURCE_DIR / f"{cell_name}.mp4"
        dst_source = source_out / f"{cell_name}.mp4"

        if src_video.exists():
            shutil.copy2(str(src_video), str(dst_source))
        else:
            print(f"  WARNING: Source video not found for {cell_name}")

        # Copy fake video (rename to uniform name)
        dst_fake = fake_out / f"{cell_name}.mp4"
        shutil.copy2(str(info["path"]), str(dst_fake))

        manifest["stimuli"][cell_name] = {
            "source": str(dst_source),
            "fake": str(dst_fake),
            "vc_system": info["vc_system"],
            "lipsync_system": LS_SYSTEM,
            "variant": info["variant"],
            "original_id": info["vid_id"],
            "rating": info["rating"],
        }

    # Validate
    print(f"\nValidating...")
    source_count = len(list(source_out.glob("*.mp4")))
    fake_count = len(list(fake_out.glob("*.mp4")))
    print(f"  Source videos: {source_count}")
    print(f"  Fake videos:   {fake_count}")

    # Check durations
    issues = 0
    for mp4 in sorted(curated_dir.rglob("*.mp4")):
        dur = get_video_duration(str(mp4))
        if dur < 3.0 or dur > 7.0:
            print(f"  WARNING: {mp4.name} duration={dur:.1f}s (expected ~5s)")
            issues += 1

    # Save manifest
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nManifest saved to {MANIFEST_FILE}")

    if issues:
        print(f"\n{issues} duration warnings — check those videos.")
    else:
        print(f"\nAll videos validated OK.")

    print(f"\nNext steps:")
    print(f"  1. Review: ls {curated_dir}/source/ {curated_dir}/fake/")
    print(f"  2. Test experiment: python3 08_4afc_experiment.py --curated-dir {curated_dir}")


if __name__ == "__main__":
    main()
