#!/usr/bin/env python3
"""
Phase 1: Prepare source data for the experiment.

Finds INSTRUCCIONES (neutral) and LLORON (emotional) videos for each actor,
splits ~60s videos into short clips, face-crops to 512x512, and extracts
audio + reference frames.

Usage:
  python3 01_prepare_data.py                  # process real data
  python3 01_prepare_data.py --demo           # create synthetic demo data
  python3 01_prepare_data.py --no-face-crop   # skip face cropping
"""

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path

import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def extract_audio(video_path: Path, audio_path: Path, sr: int = 16000):
    """Extract audio from video using ffmpeg."""
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", str(sr), "-ac", "1",
        str(audio_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def extract_frame(video_path: Path, frame_path: Path, timestamp_sec: float = 2.0):
    """Extract a single frame as a reference image."""
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ss", str(timestamp_sec),
        "-vframes", "1", "-q:v", "2",
        str(frame_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def split_clip(source_video: Path, output_path: Path, start_sec: float,
               duration: float, fps: int = 25):
    """Extract a clip from a longer video using ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", str(source_video),
        "-t", str(duration),
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def find_actor_video(raw_dir: Path, identity: str, condition_cfg: dict) -> Path | None:
    """Find the source video for an actor + condition."""
    subdir = raw_dir / condition_cfg["subdir"]
    pattern = condition_cfg["filename_pattern"].format(identity=identity)
    candidate = subdir / pattern
    if candidate.exists():
        return candidate

    # Fuzzy fallback: search for files starting with identity name in that subdir
    if subdir.exists():
        for f in subdir.iterdir():
            if f.name.startswith(identity) and f.suffix in (".mp4", ".avi", ".mkv"):
                return f
    return None


def process_actors(config: dict, do_face_crop: bool = True):
    """Process all actors: find videos, split clips, face-crop, extract audio/frame."""
    source_dir = Path(config["source"]["data_dir"])
    source_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = Path(config["source"]["raw_video_dir"])
    if not raw_dir.exists():
        print(f"ERROR: Raw video directory not found: {raw_dir}")
        print("Update 'raw_video_dir' in config.yaml")
        return None

    identities = config["source"]["identities"]
    conditions = config["source"]["conditions"]
    clips_per_video = config["source"].get("clips_per_video", 2)
    clip_duration = config["source"].get("clip_duration", 5)
    start_offset = config["source"].get("start_offset", 10)
    clip_gap = config["source"].get("clip_gap", 5)
    fps = config["source"].get("video_fps", 25)
    sr = config["source"].get("audio_sr", 16000)

    fc_cfg = config.get("face_crop", {})
    fc_enabled = do_face_crop and fc_cfg.get("enabled", True)
    if fc_enabled:
        from tools.face_crop import crop_video, extract_reference_frame

    manifest = []

    for identity in identities:
        for emotion, cond_cfg in conditions.items():
            video_path = find_actor_video(raw_dir, identity, cond_cfg)
            if video_path is None:
                print(f"  [WARN] Video not found: {identity} / {emotion}")
                continue

            print(f"  {identity} / {emotion}: {video_path.name}")

            for clip_idx in range(1, clips_per_video + 1):
                start_sec = start_offset + (clip_idx - 1) * (clip_duration + clip_gap)
                stem = f"{identity}_{emotion}_c{clip_idx:02d}"

                # Step 1: Split clip from source
                raw_clip = source_dir / "raw_clips" / f"{stem}.mp4"
                if not raw_clip.exists():
                    raw_clip.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        split_clip(video_path, raw_clip, start_sec, clip_duration, fps)
                        print(f"    Split {stem} (start={start_sec}s)")
                    except subprocess.CalledProcessError as e:
                        print(f"    [ERROR] Failed to split {stem}: {e}")
                        continue

                # Step 2: Face crop (or copy as-is)
                cropped_clip = source_dir / f"{stem}.mp4"
                if not cropped_clip.exists():
                    if fc_enabled:
                        try:
                            ok = crop_video(
                                raw_clip, cropped_clip,
                                target_size=tuple(fc_cfg.get("target_size", [512, 512])),
                                padding=fc_cfg.get("padding_factor", 1.5),
                                smooth_window=fc_cfg.get("smooth_window", 7),
                            )
                            if ok:
                                print(f"    Face-cropped {stem}")
                            else:
                                print(f"    [WARN] Face crop failed for {stem}, copying raw")
                                import shutil
                                shutil.copy2(str(raw_clip), str(cropped_clip))
                        except Exception as e:
                            print(f"    [ERROR] Face crop {stem}: {e}")
                            import shutil
                            shutil.copy2(str(raw_clip), str(cropped_clip))
                    else:
                        import shutil
                        shutil.copy2(str(raw_clip), str(cropped_clip))
                        print(f"    Copied {stem} (no face crop)")

                # Step 3: Extract audio
                audio_path = source_dir / f"{stem}.wav"
                if not audio_path.exists():
                    try:
                        extract_audio(cropped_clip, audio_path, sr)
                    except subprocess.CalledProcessError:
                        print(f"    [WARN] Audio extraction failed for {stem}")

                # Step 4: Extract reference frame (face-cropped)
                frame_path = source_dir / f"{stem}_frame.png"
                if not frame_path.exists():
                    if fc_enabled:
                        try:
                            extract_reference_frame(
                                cropped_clip, frame_path,
                                timestamp_sec=2.0,
                                target_size=tuple(fc_cfg.get("target_size", [512, 512])),
                                padding=fc_cfg.get("padding_factor", 1.5),
                            )
                        except Exception:
                            extract_frame(cropped_clip, frame_path)
                    else:
                        extract_frame(cropped_clip, frame_path)

                manifest.append({
                    "identity": identity,
                    "emotion": emotion,
                    "sentence_id": f"c{clip_idx:02d}",
                    "video_path": str(cropped_clip),
                    "audio_path": str(audio_path),
                    "frame_path": str(frame_path),
                    "duration_sec": clip_duration,
                })

    if not manifest:
        print("No clips processed. Check source paths.")
        return None

    manifest_path = source_dir / "manifest.csv"
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest[0].keys())
        writer.writeheader()
        writer.writerows(manifest)

    print(f"\nManifest saved: {manifest_path} ({len(manifest)} clips)")
    return manifest


def create_demo_data(config: dict):
    """Create synthetic demo data for testing the pipeline without real data."""
    source_dir = Path(config["source"]["data_dir"])
    source_dir.mkdir(parents=True, exist_ok=True)

    identities = config["source"]["identities"]
    clips_per_video = config["source"].get("clips_per_video", 2)
    fps = config["source"].get("video_fps", 25)
    sr = config["source"].get("audio_sr", 16000)
    duration = config["generation"]["clip_duration_sec"]
    emotions = list(config["source"]["conditions"].keys())

    manifest = []

    for identity in identities:
        for emotion in emotions:
            for clip_idx in range(1, clips_per_video + 1):
                stem = f"{identity}_{emotion}_c{clip_idx:02d}"
                video_path = source_dir / f"{stem}.mp4"
                audio_path = source_dir / f"{stem}.wav"
                frame_path = source_dir / f"{stem}_frame.png"

                if not video_path.exists():
                    color = "blue" if emotion == "neutral" else "red"
                    cmd = [
                        "ffmpeg", "-y",
                        "-f", "lavfi", "-i",
                        f"color=c={color}:size=512x512:duration={duration}:rate={fps},"
                        f"drawtext=text='{stem}':fontsize=24:fontcolor=white:"
                        f"x=(w-text_w)/2:y=(h-text_h)/2",
                        "-f", "lavfi", "-i",
                        f"sine=frequency={220 + hash(stem) % 440}:duration={duration}:sample_rate={sr}",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-c:a", "pcm_s16le",
                        "-shortest",
                        str(video_path),
                    ]
                    subprocess.run(cmd, capture_output=True, check=True)
                    print(f"  Created {video_path.name}")

                if not audio_path.exists():
                    extract_audio(video_path, audio_path, sr)

                if not frame_path.exists():
                    extract_frame(video_path, frame_path)

                manifest.append({
                    "identity": identity,
                    "emotion": emotion,
                    "sentence_id": f"c{clip_idx:02d}",
                    "video_path": str(video_path),
                    "audio_path": str(audio_path),
                    "frame_path": str(frame_path),
                    "duration_sec": duration,
                })

    manifest_path = source_dir / "manifest.csv"
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest[0].keys())
        writer.writeheader()
        writer.writerows(manifest)

    print(f"\nManifest saved: {manifest_path} ({len(manifest)} clips)")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Prepare source data")
    parser.add_argument("--demo", action="store_true",
                        help="Create synthetic demo data for pipeline testing")
    parser.add_argument("--no-face-crop", action="store_true",
                        help="Skip face cropping (just split clips)")
    args = parser.parse_args()

    config = load_config()

    print("=" * 60)
    print("Phase 1: Prepare Source Data")
    print("=" * 60)

    if args.demo:
        print("\nCreating synthetic demo data...")
        manifest = create_demo_data(config)
    else:
        print(f"\nProcessing actors from: {config['source']['raw_video_dir']}")
        print(f"Identities: {', '.join(config['source']['identities'])}")
        print(f"Face cropping: {'ON' if not args.no_face_crop else 'OFF'}")
        print()
        manifest = process_actors(config, do_face_crop=not args.no_face_crop)

    if manifest:
        n_identities = len(set(m["identity"] for m in manifest))
        n_neutral = sum(1 for m in manifest if m["emotion"] == "neutral")
        n_emotional = sum(1 for m in manifest if m["emotion"] == "emotional")
        print(f"\n{'=' * 60}")
        print(f"DONE.")
        print(f"  Identities: {n_identities}")
        print(f"  Neutral clips: {n_neutral}")
        print(f"  Emotional clips: {n_emotional}")
        print(f"  Total source clips: {len(manifest)}")
        print(f"\nNext: python3 02_generate_vc.py")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
