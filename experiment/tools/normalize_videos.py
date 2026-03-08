#!/usr/bin/env python3
"""
Normalize all videos (source + generated) for human evaluation.

Ensures all videos have identical encoding parameters so participants
cannot distinguish real from fake based on compression artifacts,
loudness differences, or duration variation.

What it does:
1. Re-encodes ALL videos (source + generated) with identical ffmpeg settings
2. Normalizes audio loudness to -23 LUFS (EBU R128)
3. Trims/pads all clips to exactly target_duration seconds
4. Outputs to data/normalized/ directory preserving structure

Usage:
    python3 tools/normalize_videos.py
    python3 tools/normalize_videos.py --dry-run               # preview only
    python3 tools/normalize_videos.py --crf 26                 # adjust quality
    python3 tools/normalize_videos.py --target-duration 5.0    # force 5s clips
"""

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def get_video_info(path):
    """Get duration, bitrate, resolution, audio sample rate via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(path)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    info = json.loads(r.stdout)
    vs = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    aus = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not vs:
        return None
    return {
        "duration": float(info["format"]["duration"]),
        "bitrate": int(info["format"].get("bit_rate", 0)),
        "width": int(vs["width"]),
        "height": int(vs["height"]),
        "fps": vs.get("r_frame_rate", "25/1"),
        "audio_rate": int(aus["sample_rate"]) if aus else None,
    }


def get_loudness(path):
    """Measure integrated loudness (LUFS) using ffmpeg loudnorm filter."""
    cmd = [
        "ffmpeg", "-i", str(path), "-af", "loudnorm=print_format=json",
        "-f", "null", "-"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    # Parse loudnorm JSON output from stderr
    stderr = r.stderr
    try:
        # Find the JSON block in stderr
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            loudness_info = json.loads(stderr[json_start:json_end])
            return float(loudness_info.get("input_i", -23))
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def normalize_video(input_path, output_path, crf=23, target_duration=5.0,
                    audio_rate=16000, resolution=512, dry_run=False):
    """
    Re-encode video with standardized settings + LUFS normalization.

    Parameters:
        crf: Constant Rate Factor (18=high quality, 23=default, 28=lower quality).
        target_duration: Exact clip duration in seconds. Trims or pads to match.
        audio_rate: Target audio sample rate in Hz.
        resolution: Target resolution (square, NxN).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if dry_run:
        print(f"  [DRY RUN] {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        return True

    info = get_video_info(input_path)
    if not info:
        print(f"  ERROR: Cannot probe {input_path}")
        return False

    input_dur = info["duration"]

    # Build video filter: scale + fps + trim/pad
    vf_parts = [
        f"scale={resolution}:{resolution}:force_original_aspect_ratio=disable",
        "fps=25",
    ]

    # Pad short videos with last frame, or trim long videos
    if input_dur < target_duration:
        # tpad will repeat the last frame to extend
        pad_frames = int((target_duration - input_dur) * 25)
        vf_parts.append(f"tpad=stop_mode=clone:stop={pad_frames}")

    vf = ",".join(vf_parts)

    # Build audio filter: loudnorm to -23 LUFS (EBU R128)
    af = "loudnorm=I=-23:LRA=7:TP=-2"

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        # Video settings
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-vf", vf,
        # Audio settings with loudness normalization
        "-c:a", "aac",
        "-ar", str(audio_rate),
        "-b:a", "64k",
        "-ac", "1",
        "-af", af,
        # Trim to exact duration (handles both long and tpad-extended videos)
        "-t", f"{target_duration:.2f}",
        str(output_path),
    ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[-200:]}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Normalize videos for human evaluation")
    parser.add_argument("--crf", type=int, default=23,
                        help="CRF value (18=high, 23=default, 28=low). Default: 23")
    parser.add_argument("--audio-rate", type=int, default=16000,
                        help="Audio sample rate in Hz. Default: 16000")
    parser.add_argument("--target-duration", type=float, default=5.0,
                        help="Exact duration for all clips in seconds. Default: 5.0")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be done without encoding")
    parser.add_argument("--output-dir", type=str, default="data/normalized",
                        help="Output directory. Default: data/normalized")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    os.chdir(base_dir)

    source_dir = Path("data/source")
    output_dir = Path(args.output_dir)

    # Load stimulus manifest to know which generated videos exist
    manifest_path = Path("data/generated/stimulus_manifest.csv")
    if not manifest_path.exists():
        print("ERROR: stimulus_manifest.csv not found. Run the experiment first.")
        sys.exit(1)

    with open(manifest_path) as f:
        reader = csv.DictReader(f)
        stimuli = [row for row in reader]

    # Find all source clips
    source_clips = sorted(source_dir.glob("*.mp4"))
    print(f"Found {len(source_clips)} source clips")
    print(f"Found {len(stimuli)} stimulus entries")

    # Gather all videos and their info
    print("\nAnalyzing video properties...")
    all_videos = []

    for clip in source_clips:
        info = get_video_info(clip)
        if info:
            all_videos.append({
                "type": "source",
                "input": clip,
                "output": output_dir / "source" / clip.name,
                "info": info,
                "clip_id": clip.stem,
            })

    for row in stimuli:
        video_path = Path(row.get("output_video", ""))
        if not video_path.exists():
            continue
        info = get_video_info(video_path)
        if info:
            vc = row.get("vc_system", "unknown")
            ls = row.get("lipsync_system", "unknown")
            all_videos.append({
                "type": "generated",
                "input": video_path,
                "output": output_dir / vc / ls / video_path.name,
                "info": info,
                "vc": vc,
                "ls": ls,
                "clip_id": video_path.stem,
            })

    if not all_videos:
        print("ERROR: No videos found!")
        sys.exit(1)

    # Compute statistics
    durations = [v["info"]["duration"] for v in all_videos]
    bitrates = [v["info"]["bitrate"] // 1000 for v in all_videos]
    print(f"\nBefore normalization:")
    print(f"  Duration range: {min(durations):.2f}s – {max(durations):.2f}s")
    print(f"  Bitrate range:  {min(bitrates)}k – {max(bitrates)}k")
    print(f"\nTarget: {args.target_duration:.1f}s, CRF {args.crf}, "
          f"512×512, 25fps, -23 LUFS, {args.audio_rate}Hz mono")

    # Normalize all videos
    print(f"\nNormalizing {len(all_videos)} videos...")

    success = 0
    failed = 0
    for i, v in enumerate(all_videos, 1):
        ok = normalize_video(
            v["input"], v["output"],
            crf=args.crf,
            target_duration=args.target_duration,
            audio_rate=args.audio_rate,
            dry_run=args.dry_run,
        )
        if ok:
            success += 1
        else:
            failed += 1
            print(f"  FAILED: {v['input']}")

        if i % 50 == 0:
            print(f"  Progress: {i}/{len(all_videos)}")

    print(f"\nDone: {success} normalized, {failed} failed")

    if not args.dry_run and success > 0:
        # Verify a sample
        print("\nVerification (sample of normalized videos):")
        sample = list(output_dir.rglob("*.mp4"))[:5]
        for s in sample:
            info = get_video_info(s)
            lufs = get_loudness(s)
            if info:
                lufs_str = f"{lufs:.1f} LUFS" if lufs is not None else "N/A"
                print(f"  {s.name}: {info['width']}x{info['height']}, "
                      f"{info['bitrate']//1000}k, {info['duration']:.2f}s, "
                      f"audio={info['audio_rate']}Hz, loudness={lufs_str}")

        # Write normalization log
        log_path = output_dir / "normalization_log.txt"
        with open(log_path, "w") as f:
            f.write(f"Normalization settings:\n")
            f.write(f"  CRF: {args.crf}\n")
            f.write(f"  Audio: {args.audio_rate} Hz, AAC 64k mono\n")
            f.write(f"  Audio loudness: -23 LUFS (EBU R128, loudnorm I=-23:LRA=7:TP=-2)\n")
            f.write(f"  Resolution: 512x512\n")
            f.write(f"  Framerate: 25 fps\n")
            f.write(f"  Codec: H.264 (libx264), yuv420p\n")
            f.write(f"  Duration: {args.target_duration:.1f}s (trimmed/padded)\n")
            f.write(f"  Videos normalized: {success}\n")
            f.write(f"  Videos failed: {failed}\n")
        print(f"\nLog saved to {log_path}")


if __name__ == "__main__":
    main()
