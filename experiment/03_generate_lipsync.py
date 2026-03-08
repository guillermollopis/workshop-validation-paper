#!/usr/bin/env python3
"""
Phase 2, Task 2.2: Generate talking-head videos using all lipsync systems.

For each VC output × each lipsync system, generate a lip-synced video.

Usage:
  python3 03_generate_lipsync.py
  python3 03_generate_lipsync.py --systems wav2lip sadtalker
  python3 03_generate_lipsync.py --dry-run
"""

import argparse
import csv
import json
import time
from pathlib import Path

import yaml

from tools.lipsync_systems import get_enabled_systems, LIPSYNC_SYSTEMS, standardize_output


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def load_vc_manifest(config: dict) -> list[dict]:
    vc_manifest_path = Path(config["generation"]["vc_output_dir"]) / "vc_manifest.csv"
    if not vc_manifest_path.exists():
        print(f"ERROR: VC manifest not found: {vc_manifest_path}")
        print("Run 02_generate_vc.py first.")
        raise SystemExit(1)
    with open(vc_manifest_path) as f:
        rows = list(csv.DictReader(f))
    # Filter to only existing VC outputs
    return [r for r in rows if r.get("vc_audio_exists", "True") == "True"]


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Generate lipsync videos")
    parser.add_argument("--systems", nargs="+", default=None,
                        help="Specific lipsync systems (default: all enabled)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--gpu", default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    config = load_config()
    vc_manifest = load_vc_manifest(config)
    gen_dir = Path(config["generation"]["output_dir"])
    gen_cfg = config["generation"]

    if args.systems:
        systems = {k: LIPSYNC_SYSTEMS[k] for k in args.systems if k in LIPSYNC_SYSTEMS}
    else:
        systems = get_enabled_systems(config)

    if not systems:
        print("ERROR: No lipsync systems enabled.")
        return

    total = len(vc_manifest) * len(systems)

    print("=" * 60)
    print("Phase 2, Task 2.2: Lipsync Generation")
    print("=" * 60)
    print(f"VC outputs: {len(vc_manifest)}")
    print(f"Lipsync systems: {', '.join(s['name'] for s in systems.values())}")
    print(f"Total videos to generate: {total}")
    print()

    if args.dry_run:
        print("[DRY RUN] Would generate:")
        for ls_key, ls_info in systems.items():
            vc_systems = set(r["vc_system"] for r in vc_manifest)
            for vc in vc_systems:
                out_dir = gen_dir / vc / ls_key
                count = sum(1 for r in vc_manifest if r["vc_system"] == vc)
                print(f"  {vc} + {ls_info['name']}: {count} videos → {out_dir}/")
        return

    log = {"generated": [], "failed": [], "skipped": []}
    done = 0
    full_manifest = []

    for ls_key, ls_info in systems.items():
        ls_name = ls_info["name"]
        ls_func = ls_info["func"]
        input_type = ls_info["input_type"]

        print(f"\n--- {ls_name} ---")

        for clip in vc_manifest:
            stem = f"{clip['identity']}_{clip['emotion']}_{clip['sentence_id']}"
            vc_key = clip["vc_system"]
            out_dir = gen_dir / vc_key / ls_key
            out_dir.mkdir(parents=True, exist_ok=True)

            output_raw = out_dir / f"{stem}_raw.mp4"
            output_final = out_dir / f"{stem}.mp4"
            done += 1

            if output_final.exists():
                log["skipped"].append({"vc": vc_key, "ls": ls_key, "clip": stem})
                full_manifest.append({
                    "identity": clip["identity"],
                    "emotion": clip["emotion"],
                    "sentence_id": clip["sentence_id"],
                    "vc_system": vc_key,
                    "lipsync_system": ls_key,
                    "source_video": clip["source_video"],
                    "source_audio": clip["source_audio"],
                    "vc_audio": clip["vc_audio"],
                    "output_video": str(output_final),
                })
                print(f"  [{done}/{total}] {vc_key}+{ls_key}/{stem} — skipped (exists)")
                continue

            print(f"  [{done}/{total}] {vc_key}+{ls_key}/{stem} — generating...", end=" ", flush=True)
            start = time.time()

            # Choose face input based on what the system needs
            face_input = clip["source_frame"] if input_type == "image" else clip["source_video"]

            ls_cfg = config.get("lipsync_systems", {}).get(ls_key, {})
            repo_dir = ls_cfg.get("repo_dir", f"tools/repos/{ls_key}")
            if input_type == "image":
                success = ls_func(
                    source_image=face_input,
                    driving_audio=clip["vc_audio"],
                    output_path=str(output_raw),
                    gpu=args.gpu,
                    repo_dir=repo_dir,
                    config=ls_cfg,
                )
            else:
                success = ls_func(
                    source_video=face_input,
                    driving_audio=clip["vc_audio"],
                    output_path=str(output_raw),
                    gpu=args.gpu,
                    repo_dir=repo_dir,
                    config=ls_cfg,
                )

            elapsed = time.time() - start

            if success and output_raw.exists():
                # Standardize output format
                std_ok = standardize_output(
                    str(output_raw), str(output_final),
                    fps=gen_cfg["output_fps"],
                    resolution=tuple(gen_cfg["output_resolution"]),
                )
                if std_ok and output_final.exists():
                    output_raw.unlink(missing_ok=True)  # remove raw
                    size_mb = output_final.stat().st_size / (1024 * 1024)
                    print(f"OK ({elapsed:.1f}s, {size_mb:.1f}MB)")
                    log["generated"].append({"vc": vc_key, "ls": ls_key, "clip": stem, "time": elapsed})
                else:
                    print(f"FAILED (standardize)")
                    log["failed"].append({"vc": vc_key, "ls": ls_key, "clip": stem, "stage": "standardize"})
            else:
                print(f"FAILED ({elapsed:.1f}s)")
                log["failed"].append({"vc": vc_key, "ls": ls_key, "clip": stem, "stage": "generation"})

            full_manifest.append({
                "identity": clip["identity"],
                "emotion": clip["emotion"],
                "sentence_id": clip["sentence_id"],
                "vc_system": vc_key,
                "lipsync_system": ls_key,
                "source_video": clip["source_video"],
                "source_audio": clip["source_audio"],
                "vc_audio": clip["vc_audio"],
                "output_video": str(output_final),
            })

    # Save full stimulus manifest
    manifest_path = gen_dir / "stimulus_manifest.csv"
    if full_manifest:
        with open(manifest_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=full_manifest[0].keys())
            writer.writeheader()
            writer.writerows(full_manifest)

    # Save log
    log_path = gen_dir / "generation_log.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"DONE.")
    print(f"  Generated: {len(log['generated'])}")
    print(f"  Skipped: {len(log['skipped'])}")
    print(f"  Failed: {len(log['failed'])}")
    if log["failed"]:
        print(f"  Failed details:")
        for fail in log["failed"][:10]:
            print(f"    - {fail['vc']}+{fail['ls']}: {fail['clip']} ({fail.get('stage', '?')})")
        if len(log["failed"]) > 10:
            print(f"    ... and {len(log['failed'])-10} more")
    print(f"  Manifest: {manifest_path}")
    print(f"\nNext: python3 04_compute_metrics.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
