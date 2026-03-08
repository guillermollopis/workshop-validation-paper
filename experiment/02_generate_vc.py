#!/usr/bin/env python3
"""
Phase 2, Task 2.1: Generate cloned audio using all VC systems.

For each source audio × each VC system, generate a cloned version.

Usage:
  python3 02_generate_vc.py
  python3 02_generate_vc.py --systems xtts_v2 knn_vc       # specific systems only
  python3 02_generate_vc.py --dry-run                      # preview only
"""

import argparse
import csv
import json
import time
from pathlib import Path

import yaml

from tools.vc_systems import get_enabled_systems, VC_SYSTEMS


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def load_manifest(config: dict) -> list[dict]:
    manifest_path = Path(config["source"]["data_dir"]) / "manifest.csv"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}")
        print("Run 01_prepare_data.py first.")
        raise SystemExit(1)
    with open(manifest_path) as f:
        return list(csv.DictReader(f))


def load_transcripts(config: dict) -> dict:
    """Load pre-transcribed source clips from transcripts.json."""
    transcripts_path = config["source"].get("transcripts_path", "data/source/transcripts.json")
    path = Path(transcripts_path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            transcripts = json.load(f)
        print(f"Loaded {len(transcripts)} pre-transcribed clips from {path}")
        return transcripts
    else:
        print(f"WARNING: transcripts.json not found at {path}")
        print("Text-based VC systems will fall back to Whisper medium (slower).")
        return {}


# Systems that need text input (transcript)
TEXT_BASED_SYSTEMS = {"xtts_v2", "cosyvoice"}


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Generate cloned audio")
    parser.add_argument("--systems", nargs="+", default=None,
                        help="Specific VC systems to run (default: all enabled)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without running")
    parser.add_argument("--gpu", default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    config = load_config()
    manifest = load_manifest(config)
    vc_output_dir = Path(config["generation"]["vc_output_dir"])

    # Load pre-transcribed text for text-based systems
    transcripts = load_transcripts(config)

    # Get systems to run
    if args.systems:
        systems = {k: VC_SYSTEMS[k] for k in args.systems if k in VC_SYSTEMS}
    else:
        systems = get_enabled_systems(config)

    if not systems:
        print("ERROR: No VC systems enabled. Check config.yaml or --systems flag.")
        return

    total = len(manifest) * len(systems)

    print("=" * 60)
    print("Phase 2, Task 2.1: Voice Cloning")
    print("=" * 60)
    print(f"Source clips: {len(manifest)}")
    print(f"VC systems: {', '.join(s['name'] for s in systems.values())}")
    print(f"Total to generate: {total}")
    print()

    if args.dry_run:
        print("[DRY RUN] Would generate:")
        for vc_key, vc_info in systems.items():
            out_dir = vc_output_dir / vc_key
            print(f"  {vc_info['name']}: {len(manifest)} files → {out_dir}/")
        return

    log = {"generated": [], "failed": [], "skipped": []}
    done = 0

    for vc_key, vc_info in systems.items():
        vc_name = vc_info["name"]
        vc_func = vc_info["func"]
        out_dir = vc_output_dir / vc_key
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n--- {vc_name} ---")

        for i, clip in enumerate(manifest):
            stem = f"{clip['identity']}_{clip['emotion']}_{clip['sentence_id']}"
            output_path = out_dir / f"{stem}.wav"
            done += 1

            if output_path.exists():
                log["skipped"].append({"system": vc_key, "clip": stem})
                print(f"  [{done}/{total}] {stem} — skipped (exists)")
                continue

            print(f"  [{done}/{total}] {stem} — generating...", end=" ", flush=True)
            start = time.time()

            # Build kwargs for the VC function
            kwargs = {
                "source_audio": clip["audio_path"],
                "reference_audio": clip["audio_path"],  # self-cloning (same speaker)
                "output_path": str(output_path),
                "gpu": args.gpu,
                "language": config["source"].get("language", "es"),
            }

            # Pass pre-transcribed text to text-based systems
            if vc_key in TEXT_BASED_SYSTEMS and stem in transcripts:
                kwargs["text"] = transcripts[stem]

            # For CosyVoice, also pass prompt_text (same as text for self-cloning)
            if vc_key == "cosyvoice" and stem in transcripts:
                kwargs["prompt_text"] = transcripts[stem]

            success = vc_func(**kwargs)

            elapsed = time.time() - start
            if success and output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                print(f"OK ({elapsed:.1f}s, {size_kb:.0f}KB)")
                log["generated"].append({"system": vc_key, "clip": stem, "time": elapsed})
            else:
                print(f"FAILED ({elapsed:.1f}s)")
                log["failed"].append({"system": vc_key, "clip": stem})

    # Save VC manifest (maps source clips to VC outputs)
    vc_manifest = []
    for vc_key in systems:
        out_dir = vc_output_dir / vc_key
        for clip in manifest:
            stem = f"{clip['identity']}_{clip['emotion']}_{clip['sentence_id']}"
            vc_audio = out_dir / f"{stem}.wav"
            vc_manifest.append({
                "identity": clip["identity"],
                "emotion": clip["emotion"],
                "sentence_id": clip["sentence_id"],
                "vc_system": vc_key,
                "source_audio": clip["audio_path"],
                "source_video": clip["video_path"],
                "source_frame": clip["frame_path"],
                "vc_audio": str(vc_audio),
                "vc_audio_exists": vc_audio.exists(),
            })

    vc_manifest_path = vc_output_dir / "vc_manifest.csv"
    with open(vc_manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=vc_manifest[0].keys())
        writer.writeheader()
        writer.writerows(vc_manifest)

    # Save generation log
    log_path = vc_output_dir / "generation_log.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"DONE.")
    print(f"  Generated: {len(log['generated'])}")
    print(f"  Skipped (already exist): {len(log['skipped'])}")
    print(f"  Failed: {len(log['failed'])}")
    if log["failed"]:
        print(f"  Failed details:")
        for fail in log["failed"]:
            print(f"    - {fail['system']}: {fail['clip']}")
    print(f"  VC manifest: {vc_manifest_path}")
    print(f"\nNext: python3 03_generate_lipsync.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
