#!/usr/bin/env python3
"""
Phase 3: Compute all computational metrics on generated videos.

Reads the stimulus manifest from Phase 2, computes sync + visual + audio metrics,
and saves a master CSV with all results.

Usage:
  python3 04_compute_metrics.py
  python3 04_compute_metrics.py --metrics sync visual audio   # specific groups
  python3 04_compute_metrics.py --dry-run
"""

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import yaml

from tools.metrics import (
    compute_lse_c_d,
    compute_avs_metrics,
    compute_lmd,
    compute_ssim_score,
    compute_cpbd,
    compute_wavlm_similarity,
    compute_mel_similarity,
    compute_wer,
)


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def load_stimulus_manifest(config: dict) -> list[dict]:
    manifest_path = Path(config["generation"]["output_dir"]) / "stimulus_manifest.csv"
    if not manifest_path.exists():
        print(f"ERROR: Stimulus manifest not found: {manifest_path}")
        print("Run 03_generate_lipsync.py first.")
        raise SystemExit(1)
    with open(manifest_path) as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description="Phase 3: Compute metrics")
    parser.add_argument("--metrics", nargs="+", default=["sync", "visual", "audio"],
                        choices=["sync", "visual", "audio"],
                        help="Which metric groups to compute")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config()
    manifest = load_stimulus_manifest(config)
    metrics_cfg = config["metrics"]
    output_path = Path(metrics_cfg["output_file"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter to existing videos only
    valid = [m for m in manifest if Path(m["output_video"]).exists()]

    print("=" * 60)
    print("Phase 3: Compute Metrics")
    print("=" * 60)
    print(f"Videos to evaluate: {len(valid)} (of {len(manifest)} in manifest)")
    print(f"Metric groups: {', '.join(args.metrics)}")
    print()

    if args.dry_run:
        print(f"[DRY RUN] Would compute metrics on {len(valid)} videos")
        print(f"Output: {output_path}")
        return

    results = []
    total = len(valid)

    # Cache for expensive models (load once)
    _whisper_model = None

    for i, clip in enumerate(valid, 1):
        stem = f"{clip['vc_system']}/{clip['lipsync_system']}/{clip['identity']}_{clip['emotion']}_{clip['sentence_id']}"
        print(f"[{i}/{total}] {stem}")
        start = time.time()

        row = {
            "identity": clip["identity"],
            "emotion": clip["emotion"],
            "sentence_id": clip["sentence_id"],
            "vc_system": clip["vc_system"],
            "lipsync_system": clip["lipsync_system"],
            "output_video": clip["output_video"],
        }

        # --- Sync metrics ---
        if "sync" in args.metrics:
            # LSE-C, LSE-D
            lse = compute_lse_c_d(clip["output_video"])
            row["lse_c"] = lse["lse_c"]
            row["lse_d"] = lse["lse_d"]

            # AVSu, AVSm
            avs = compute_avs_metrics(
                clip["output_video"],
                gt_video_path=clip.get("source_video"),
            )
            row["avsu"] = avs["avsu"]
            row["avsm"] = avs["avsm"]

            # LMD
            if clip.get("source_video") and Path(clip["source_video"]).exists():
                lmd = compute_lmd(clip["output_video"], clip["source_video"])
                row["lmd"] = lmd["lmd"]
            else:
                row["lmd"] = float("nan")

        # --- Visual quality metrics ---
        if "visual" in args.metrics:
            # SSIM (needs GT)
            if clip.get("source_video") and Path(clip["source_video"]).exists():
                ssim_result = compute_ssim_score(clip["output_video"], clip["source_video"])
                row["ssim"] = ssim_result["ssim"]
            else:
                row["ssim"] = float("nan")

            # CPBD (no reference needed)
            cpbd_result = compute_cpbd(clip["output_video"])
            row["cpbd"] = cpbd_result["cpbd"]

            # FID is computed per-condition (across frames), not per-video
            # We'll compute it in the analysis step

        # --- Audio quality metrics ---
        if "audio" in args.metrics:
            vc_audio = clip.get("vc_audio", "")
            source_audio = clip.get("source_audio", "")

            if vc_audio and Path(vc_audio).exists() and source_audio and Path(source_audio).exists():
                # WavLM speaker similarity
                wavlm = compute_wavlm_similarity(vc_audio, source_audio)
                row["wavlm_sim"] = wavlm["wavlm_sim"]

                # Mel spectrogram similarity
                mel = compute_mel_similarity(vc_audio, source_audio)
                row["mel_sim"] = mel["mel_sim"]

                # WER
                wer_result = compute_wer(
                    vc_audio, reference_audio=source_audio,
                    language=metrics_cfg.get("whisper_language", "es"),
                    whisper_model_size=metrics_cfg.get("whisper_model", "medium"),
                )
                row["wer"] = wer_result["wer"]
            else:
                row["wavlm_sim"] = float("nan")
                row["mel_sim"] = float("nan")
                row["wer"] = float("nan")

        elapsed = time.time() - start
        print(f"  Done ({elapsed:.1f}s)")

        results.append(row)

        # Save incrementally every 50 videos
        if i % 50 == 0 or i == total:
            _save_results(results, output_path)

    # Final save
    _save_results(results, output_path)

    # Summary statistics
    print(f"\n{'=' * 60}")
    print(f"DONE. Metrics computed for {len(results)} videos.")
    print(f"Output: {output_path}")
    print()

    if results:
        import pandas as pd
        df = pd.DataFrame(results)
        metric_cols = [c for c in df.columns if c not in
                       ["identity", "emotion", "sentence_id", "vc_system",
                        "lipsync_system", "output_video"]]
        print("Metric summary (mean ± std):")
        for col in metric_cols:
            vals = df[col].dropna()
            if len(vals) > 0:
                print(f"  {col:20s}: {vals.mean():.4f} ± {vals.std():.4f} (n={len(vals)})")

    print(f"\nNext: python3 05_run_analysis.py")
    print(f"{'=' * 60}")


def _save_results(results: list[dict], output_path: Path):
    """Save results to CSV."""
    if not results:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
