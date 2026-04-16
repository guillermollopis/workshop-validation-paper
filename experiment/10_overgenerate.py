#!/usr/bin/env python3
"""
Overgeneration script — generate multiple variants per clip for manual screening.

1. Denoise all VC audio (removes electronic noise)
2. Generate N lipsync variants per clip (different seeds for LatentSync)
3. Normalize all outputs

Usage:
  python3 10_overgenerate.py                    # 3 variants per clip
  python3 10_overgenerate.py --variants 5       # 5 variants
  python3 10_overgenerate.py --dry-run          # preview what would be generated
  python3 10_overgenerate.py --denoise-only     # just denoise audio, don't generate
  python3 10_overgenerate.py --systems sonic     # only run Sonic
  python3 10_overgenerate.py --systems latentsync --variants 3
  python3 10_overgenerate.py --cells Jordi_neutral_c02 Maisa_emotional_c01  # specific cells only
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import noisereduce as nr
import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


# ── Audio denoising ──────────────────────────────────────────

def denoise_audio(input_path: str, output_path: str,
                  prop_decrease: float = 0.75, stationary: bool = True) -> bool:
    """Denoise a voice-cloned audio file using spectral gating."""
    try:
        audio, sr = sf.read(input_path)
        denoised = nr.reduce_noise(
            y=audio, sr=sr,
            stationary=stationary,
            prop_decrease=prop_decrease,
        )
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, denoised, sr)
        return True
    except Exception as e:
        print(f"    [ERROR] Denoise failed: {e}")
        return False


def denoise_all_vc(vc_output_dir: str, denoised_dir: str, vc_systems: list[str]):
    """Denoise all VC audio outputs."""
    vc_dir = Path(vc_output_dir)
    out_dir = Path(denoised_dir)

    total = 0
    done = 0

    for vc_name in vc_systems:
        src = vc_dir / vc_name
        if not src.exists():
            print(f"  {vc_name}: directory not found, skipping")
            continue

        wavs = sorted(src.glob("*.wav"))
        total += len(wavs)

        for wav in wavs:
            dst = out_dir / vc_name / wav.name
            done += 1
            if dst.exists():
                print(f"  [{done}/{total}] {vc_name}/{wav.stem} — already denoised")
                continue
            print(f"  [{done}/{total}] {vc_name}/{wav.stem} — denoising...", end=" ", flush=True)
            if denoise_audio(str(wav), str(dst)):
                print("OK")
            else:
                print("FAILED")
                # Copy original as fallback
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(wav), str(dst))

    return done


# ── Lipsync generation with seeds ────────────────────────────

def normalize_video(input_path: str, output_path: str,
                    duration: float = 5.0, crf: int = 18) -> bool:
    """Normalize video to standard format."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-t", str(duration),
        "-vf", f"scale=512:512:force_original_aspect_ratio=disable,fps=25",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-23:LRA=7:TP=-2",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


def generate_latentsync_variant(source_video: str, driving_audio: str, output_path: str,
                                 seed: int, config: dict) -> bool:
    """Run LatentSync with a specific seed and increased quality."""
    repo_dir = Path(config.get("repo_dir", "/home/inab/Desktop/ai_npc/LatentSync")).resolve()
    latentsync_python = config.get("python", "/home/inab/miniconda3/envs/latentsync/bin/python")
    unet_config = config.get("unet_config", "configs/unet/stage2_512.yaml")
    checkpoint = config.get("checkpoint", "checkpoints/latentsync_unet.pt")
    inference_steps = config.get("inference_steps", 50)  # increased from 30
    guidance_scale = config.get("guidance_scale", 2.0)

    # Prepare 16kHz audio for LatentSync
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        prepared_audio = f.name

    try:
        # Highpass + loudness normalize for LatentSync input
        prep_cmd = [
            "ffmpeg", "-y", "-i", driving_audio,
            "-af", "highpass=f=80,loudnorm=I=-16:LRA=7:TP=-1",
            "-ar", "16000", "-ac", "1", prepared_audio,
        ]
        r = subprocess.run(prep_cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print(f"    [ERROR] Audio prep failed")
            return False

        # Run LatentSync
        raw_output = output_path + ".ls_raw.mp4"
        cmd = [
            latentsync_python, "-m", "scripts.inference",
            "--unet_config_path", unet_config,
            "--inference_ckpt_path", checkpoint,
            "--inference_steps", str(inference_steps),
            "--guidance_scale", str(guidance_scale),
            "--video_path", str(Path(source_video).resolve()),
            "--audio_path", str(Path(prepared_audio).resolve()),
            "--video_out_path", str(Path(raw_output).resolve()),
            "--seed", str(seed),
            "--enable_deepcache",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True,
                                cwd=str(repo_dir), timeout=600)

        if result.returncode != 0 or not os.path.exists(raw_output):
            if result.stderr:
                lines = result.stderr.strip().split("\n")
                for line in lines[-3:]:
                    print(f"      {line}")
            return False

        # Re-mux with original (better quality) VC audio
        remux_cmd = [
            "ffmpeg", "-y",
            "-i", raw_output, "-i", driving_audio,
            "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", output_path,
        ]
        r = subprocess.run(remux_cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            shutil.move(raw_output, output_path)
        elif os.path.exists(raw_output):
            os.unlink(raw_output)

        return os.path.exists(output_path)

    finally:
        for f in [prepared_audio, output_path + ".ls_raw.mp4"]:
            if os.path.exists(f):
                os.unlink(f)


def generate_sonic_variant(source_frame: str, driving_audio: str, output_path: str,
                           seed: int, config: dict) -> bool:
    """Run Sonic with a specific seed."""
    sonic_dir = config.get("repo_dir", "/home/inab/Desktop/ai_npc/Sonic")
    sonic_python = config.get("python", "/home/inab/miniconda3/envs/sonic/bin/python")

    cmd = [
        sonic_python, "demo.py",
        str(Path(source_frame).resolve()),
        str(Path(driving_audio).resolve()),
        str(Path(output_path).resolve()),
        "--dynamic_scale", "1.0",
        "--seed", str(seed),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=sonic_dir, timeout=600)

    if result.returncode != 0:
        if result.stderr:
            lines = result.stderr.strip().split("\n")
            for line in lines[-3:]:
                print(f"      {line}")
        return False

    return os.path.exists(output_path)


# ── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Overgenerate lipsync variants for screening")
    parser.add_argument("--variants", type=int, default=3,
                        help="Number of variants per clip (default: 3)")
    parser.add_argument("--systems", nargs="+", default=["sonic", "latentsync"],
                        choices=["sonic", "latentsync"],
                        help="Which lipsync systems to run")
    parser.add_argument("--vc-systems", nargs="+", default=["knn_vc", "openvoice_v2"],
                        help="Which VC systems to use")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--denoise-only", action="store_true")
    parser.add_argument("--skip-denoise", action="store_true")
    parser.add_argument("--base-seed", type=int, default=42,
                        help="Base seed (variants use seed, seed+1, seed+2, ...)")
    parser.add_argument("--cells", nargs="+", default=None,
                        help="Only generate for these cells (e.g., Jordi_neutral_c02)")
    args = parser.parse_args()

    config = load_config()
    vc_output_dir = "data/vc_output"
    denoised_dir = "data/vc_denoised"
    source_dir = Path("data/source")
    overgen_dir = Path("data/overgenerated")
    normalized_dir = Path("data/overgenerated_normalized")

    # ── Step 1: Denoise VC audio ──
    if not args.skip_denoise:
        print("=" * 60)
        print("Step 1: Denoising VC audio")
        print("=" * 60)
        if args.dry_run:
            for vc in args.vc_systems:
                wavs = list(Path(vc_output_dir, vc).glob("*.wav"))
                print(f"  Would denoise {len(wavs)} files for {vc}")
        else:
            denoise_all_vc(vc_output_dir, denoised_dir, args.vc_systems)

    if args.denoise_only:
        print("\nDone (denoise only).")
        return

    # ── Step 2: Generate lipsync variants ──
    print(f"\n{'=' * 60}")
    print(f"Step 2: Generating {args.variants} lipsync variants per clip")
    print(f"  Systems: {', '.join(args.systems)}")
    print(f"  VC: {', '.join(args.vc_systems)}")
    print(f"  Seeds: {[args.base_seed + i for i in range(args.variants)]}")
    print("=" * 60)

    ls_configs = config.get("lipsync_systems", {})

    # Build clip list: source video/frame + denoised audio
    clips = []
    for vc in args.vc_systems:
        audio_dir = Path(denoised_dir) / vc
        if not audio_dir.exists():
            audio_dir = Path(vc_output_dir) / vc  # fallback to original
        for wav in sorted(audio_dir.glob("*.wav")):
            stem = wav.stem
            source_video = source_dir / f"{stem}.mp4"
            source_frame = source_dir / f"{stem}_frame.png"
            if source_video.exists():
                clips.append({
                    "stem": stem,
                    "vc_system": vc,
                    "audio": str(wav),
                    "source_video": str(source_video),
                    "source_frame": str(source_frame) if source_frame.exists() else None,
                    "identity": stem.split("_")[0],
                    "emotion": stem.split("_")[1] if len(stem.split("_")) > 1 else "unknown",
                    "clip_id": stem.split("_")[2] if len(stem.split("_")) > 2 else "unknown",
                })

    # Filter to specific cells if requested
    if args.cells:
        clips = [c for c in clips if c["stem"] in args.cells]
        print(f"\n  Filtered to {len(clips)} clips matching: {args.cells}")

    total_gen = len(clips) * len(args.systems) * args.variants
    print(f"\n  Clips: {len(clips)}")
    print(f"  Total videos to generate: {total_gen}")
    if args.dry_run:
        for ls in args.systems:
            for vc in args.vc_systems:
                vc_clips = [c for c in clips if c["vc_system"] == vc]
                print(f"  {vc} × {ls}: {len(vc_clips)} clips × {args.variants} variants = {len(vc_clips) * args.variants}")
        return

    done = 0
    failed = 0
    t0 = time.time()

    for clip in clips:
        for ls_key in args.systems:
            ls_cfg = ls_configs.get(ls_key, {})

            for variant in range(args.variants):
                seed = args.base_seed + variant
                done += 1

                # Output: data/overgenerated/{vc}/{ls}/{stem}_v{variant}.mp4
                out_dir = overgen_dir / clip["vc_system"] / ls_key
                out_dir.mkdir(parents=True, exist_ok=True)
                raw_output = out_dir / f"{clip['stem']}_v{variant}_raw.mp4"
                final_output = out_dir / f"{clip['stem']}_v{variant}.mp4"

                if final_output.exists():
                    print(f"  [{done}/{total_gen}] {clip['vc_system']}/{ls_key}/{clip['stem']}_v{variant} — exists")
                    continue

                elapsed_total = time.time() - t0
                rate = done / elapsed_total if elapsed_total > 0 else 0
                eta = (total_gen - done) / rate / 60 if rate > 0 else 0

                print(f"  [{done}/{total_gen}] {clip['vc_system']}/{ls_key}/{clip['stem']}_v{variant} "
                      f"(seed={seed}, ETA {eta:.0f}min)...", end=" ", flush=True)

                start = time.time()

                if ls_key == "latentsync":
                    success = generate_latentsync_variant(
                        source_video=clip["source_video"],
                        driving_audio=clip["audio"],
                        output_path=str(raw_output),
                        seed=seed,
                        config=ls_cfg,
                    )
                elif ls_key == "sonic":
                    if not clip["source_frame"]:
                        print("SKIP (no frame)")
                        failed += 1
                        continue
                    success = generate_sonic_variant(
                        source_frame=clip["source_frame"],
                        driving_audio=clip["audio"],
                        output_path=str(raw_output),
                        seed=seed,
                        config=ls_cfg,
                    )
                else:
                    print(f"SKIP (unknown system)")
                    continue

                gen_time = time.time() - start

                if success and raw_output.exists():
                    # Normalize
                    if normalize_video(str(raw_output), str(final_output)):
                        raw_output.unlink(missing_ok=True)
                        size_kb = final_output.stat().st_size / 1024
                        print(f"OK ({gen_time:.0f}s, {size_kb:.0f}KB)")
                    else:
                        shutil.move(str(raw_output), str(final_output))
                        print(f"OK (raw, {gen_time:.0f}s)")
                else:
                    print(f"FAILED ({gen_time:.0f}s)")
                    failed += 1

    total_time = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"DONE in {total_time/60:.1f} minutes")
    print(f"  Generated: {done - failed}/{total_gen}")
    print(f"  Failed: {failed}")

    # Count outputs
    gen_count = sum(1 for _ in overgen_dir.rglob("*.mp4"))
    print(f"  Total videos in {overgen_dir}: {gen_count}")
    print(f"\nNext step: python3 09_screen_stimuli.py --normalized-dir {overgen_dir}")


if __name__ == "__main__":
    main()
