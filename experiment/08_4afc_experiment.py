#!/usr/bin/env python3
"""
Deepfake Detection Experiment — Mixed paired (4AFC) + single (2AFC) trials.

Paired trials: two videos side by side → choose which is real or both fake.
Single trials: one video → choose real or generated.

Designs:
  --design mixed    Full 4AFC+2AFC (8 conditions, paired + single)
  --design 2afc     Single-video only (4 conditions: real/fake × emotional/neutral)

Usage:
  python3 08_4afc_experiment.py                                 # 2AFC with curated videos
  python3 08_4afc_experiment.py --design mixed                  # original mixed design
  python3 08_4afc_experiment.py --curated-dir data/curated      # 2AFC with curated dir
  python3 08_4afc_experiment.py --trials-per-cond 4             # 16 trials (pilot)
  python3 08_4afc_experiment.py --no-feedback                   # real experiment mode
  python3 08_4afc_experiment.py --port 5001

Deploy with gunicorn:
  ./serve.sh                    # pilot (feedback ON)
  ./serve.sh --no-feedback      # real experiment
"""

import argparse
import itertools
import json
import os
import random
import shutil
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file, session
from flask_session import Session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

# Server-side sessions (no 4KB cookie limit — needed for 64+ trials)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.environ.get(
    "SESSION_DIR", os.path.join(tempfile.gettempdir(), "flask_experiment_sessions"))
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 7200  # 2 hours
Session(app)

TRIALS: list[dict] = []
# Results directory — use RESULTS_DIR env var for Railway volume mount
RESULTS_DIR = Path(os.environ.get(
    "RESULTS_DIR",
    str(Path(__file__).resolve().parent / "results" / "4afc_tests")))

# Admin key for /admin endpoints (set via env var in production)
ADMIN_KEY = os.environ.get("ADMIN_KEY", "pilot2026")

# ── Condition labels ──────────────────────────────────────────────
CONDITION_LABELS = {
    "real_fake_emotional": "Real–Fake Emotional",
    "real_fake_neutral": "Real–Fake Neutral",
    "fake_fake_emotional": "Fake–Fake Emotional",
    "fake_fake_neutral": "Fake–Fake Neutral",
    "single_real_emotional": "Single Real Emotional",
    "single_real_neutral": "Single Real Neutral",
    "single_fake_emotional": "Single Fake Emotional",
    "single_fake_neutral": "Single Fake Neutral",
}

# ── Correct-answer mapping ────────────────────────────────────────
# For real-fake: "video_a" or "video_b" depending on which side the real is on
# For fake-fake: always "both_fake"
# "both_real" is never correct (we never show two reals)


def get_video_duration(path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def get_audio_mean_volume(path: str) -> float:
    """Get mean audio volume in dB using ffmpeg volumedetect."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "/dev/null"],
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stderr.split("\n"):
            if "mean_volume" in line:
                return float(line.split("mean_volume:")[1].strip().split()[0])
    except Exception:
        pass
    return -100.0


def discover_videos(normalized_dir: str, min_duration: float = 3.0,
                     min_volume_db: float = -28.0,
                     skip_checks: bool = False) -> dict:
    """Index all videos by (identity, emotion, clip_id) -> {pipeline: path}.

    Generated videos are excluded if:
      - Shorter than min_duration seconds
      - Mean audio volume below min_volume_db (too quiet / noise-only)
    Source (real) videos are always included.
    Set skip_checks=True to skip ffprobe/ffmpeg checks (for pre-validated videos).
    """
    ndir = Path(normalized_dir)
    index: dict[tuple, dict] = {}
    skipped_dur = []
    skipped_audio = []

    # Source (real)
    source_dir = ndir / "source"
    if source_dir.exists():
        for mp4 in source_dir.glob("*.mp4"):
            parts = mp4.stem.split("_")
            if len(parts) < 3:
                continue
            key = (parts[0], parts[1], parts[2])
            index.setdefault(key, {})["source"] = str(mp4.resolve())

    # Generated (fake): {vc_system}/{lipsync_system}/{clip}.mp4
    for vc_dir in sorted(ndir.iterdir()):
        if not vc_dir.is_dir() or vc_dir.name in ("source", "_old_backup"):
            continue
        for ls_dir in sorted(vc_dir.iterdir()):
            if not ls_dir.is_dir():
                continue
            pipeline = f"{vc_dir.name}/{ls_dir.name}"
            for mp4 in ls_dir.glob("*.mp4"):
                parts = mp4.stem.split("_")
                if len(parts) < 3:
                    continue

                if not skip_checks:
                    # Check duration
                    dur = get_video_duration(str(mp4))
                    if dur < min_duration:
                        skipped_dur.append((mp4.name, pipeline, f"{dur:.1f}s"))
                        continue
                    # Check audio quality
                    vol = get_audio_mean_volume(str(mp4))
                    if vol < min_volume_db:
                        skipped_audio.append((mp4.name, pipeline, f"{vol:.1f}dB"))
                        continue

                key = (parts[0], parts[1], parts[2])
                index.setdefault(key, {})
                index[key][pipeline] = str(mp4.resolve())

    if skipped_dur:
        print(f"  Skipped {len(skipped_dur)} videos shorter than {min_duration}s:")
        for name, pipe, dur in skipped_dur:
            print(f"    {pipe}/{name}: {dur}")
    if skipped_audio:
        print(f"  Skipped {len(skipped_audio)} videos with audio below {min_volume_db}dB:")
        for name, pipe, vol in skipped_audio:
            print(f"    {pipe}/{name}: {vol}")

    return index


def discover_curated_videos(curated_dir: str, skip_checks: bool = False) -> dict:
    """Index curated videos from flat source/ + fake/ structure.

    Returns the same format as discover_videos:
      {(identity, emotion, clip_id): {"source": path, "curated": path}}
    """
    cdir = Path(curated_dir)
    index: dict[tuple, dict] = {}

    for subdir, pipeline in [("source", "source"), ("fake", "curated")]:
        d = cdir / subdir
        if not d.exists():
            print(f"  WARNING: {d} not found")
            continue
        for mp4 in d.glob("*.mp4"):
            parts = mp4.stem.split("_")
            if len(parts) < 3:
                continue
            key = (parts[0], parts[1], parts[2])
            index.setdefault(key, {})[pipeline] = str(mp4.resolve())

    return index


def build_2afc_pool(index: dict) -> dict[str, list[dict]]:
    """Build single-video trials only (2AFC: real or fake?)."""
    pool = {
        "single_real_emotional": [],
        "single_real_neutral": [],
        "single_fake_emotional": [],
        "single_fake_neutral": [],
    }

    for (identity, emotion, clip_id), pipelines in index.items():
        suffix = "emotional" if emotion == "emotional" else "neutral"

        if "source" in pipelines:
            pool[f"single_real_{suffix}"].append({
                "type": "single",
                "condition": f"single_real_{suffix}",
                "identity": identity,
                "emotion": emotion,
                "clip_id": clip_id,
                "video_a": pipelines["source"],
                "video_b": "",
                "pipeline_a": "source",
                "pipeline_b": "",
                "correct_answer": "real",
                "real_side": "none",
            })

        # Fake trials (from any non-source pipeline)
        for pipe, path in pipelines.items():
            if pipe == "source":
                continue
            pool[f"single_fake_{suffix}"].append({
                "type": "single",
                "condition": f"single_fake_{suffix}",
                "identity": identity,
                "emotion": emotion,
                "clip_id": clip_id,
                "video_a": path,
                "video_b": "",
                "pipeline_a": pipe,
                "pipeline_b": "",
                "correct_answer": "fake",
                "real_side": "none",
            })

    return pool


def build_trial_pool(index: dict) -> dict[str, list[dict]]:
    """Build all possible trials for each condition.

    IMPORTANT: Videos in a pair always come from DIFFERENT clips (c01 vs c02)
    of the same identity+emotion, so they say different text. This prevents
    the same-text cue from revealing that one video is fake.
    """
    pool: dict[str, list[dict]] = {
        "real_fake_emotional": [],
        "real_fake_neutral": [],
        "fake_fake_emotional": [],
        "fake_fake_neutral": [],
    }

    # Group clips by (identity, emotion) so we can cross-pair c01 with c02
    groups: dict[tuple, list[tuple]] = {}  # (identity, emotion) -> [(clip_id, pipelines), ...]
    for (identity, emotion, clip_id), pipelines in index.items():
        groups.setdefault((identity, emotion), []).append((clip_id, pipelines))

    for (identity, emotion), clips in groups.items():
        if len(clips) < 2:
            continue  # Need at least 2 clips to cross-pair
        condition_suffix = "emotional" if emotion == "emotional" else "neutral"

        # Cross all clip pairs (c01 with c02, etc.)
        for (clip_a, pipes_a), (clip_b, pipes_b) in itertools.combinations(clips, 2):

            # ── Real-Fake pairs: real from clip_a, fake from clip_b (and vice versa) ──
            if "source" in pipes_a:
                fake_pipelines_b = [p for p in pipes_b if p != "source"]
                for fp in fake_pipelines_b:
                    for real_side in ("A", "B"):
                        if real_side == "A":
                            va, vb = pipes_a["source"], pipes_b[fp]
                            pa, pb = "source", fp
                            ca, cb = clip_a, clip_b
                        else:
                            va, vb = pipes_b[fp], pipes_a["source"]
                            pa, pb = fp, "source"
                            ca, cb = clip_b, clip_a

                        pool[f"real_fake_{condition_suffix}"].append({
                            "type": "paired",
                            "condition": f"real_fake_{condition_suffix}",
                            "identity": identity,
                            "emotion": emotion,
                            "clip_id": f"{ca}+{cb}",
                            "clip_a": ca, "clip_b": cb,
                            "video_a": va, "video_b": vb,
                            "pipeline_a": pa, "pipeline_b": pb,
                            "correct_answer": "video_a" if real_side == "A" else "video_b",
                            "real_side": real_side,
                        })

            # Also: real from clip_b, fake from clip_a
            if "source" in pipes_b:
                fake_pipelines_a = [p for p in pipes_a if p != "source"]
                for fp in fake_pipelines_a:
                    for real_side in ("A", "B"):
                        if real_side == "A":
                            va, vb = pipes_b["source"], pipes_a[fp]
                            pa, pb = "source", fp
                            ca, cb = clip_b, clip_a
                        else:
                            va, vb = pipes_a[fp], pipes_b["source"]
                            pa, pb = fp, "source"
                            ca, cb = clip_a, clip_b

                        pool[f"real_fake_{condition_suffix}"].append({
                            "type": "paired",
                            "condition": f"real_fake_{condition_suffix}",
                            "identity": identity,
                            "emotion": emotion,
                            "clip_id": f"{ca}+{cb}",
                            "clip_a": ca, "clip_b": cb,
                            "video_a": va, "video_b": vb,
                            "pipeline_a": pa, "pipeline_b": pb,
                            "correct_answer": "video_a" if real_side == "A" else "video_b",
                            "real_side": real_side,
                        })

            # ── Fake-Fake pairs: fake from clip_a + fake from clip_b (different pipelines) ──
            fake_a = sorted(p for p in pipes_a if p != "source")
            fake_b = sorted(p for p in pipes_b if p != "source")
            for fp_a in fake_a:
                for fp_b in fake_b:
                    for order in [("ab", clip_a, clip_b, fp_a, fp_b),
                                  ("ba", clip_b, clip_a, fp_b, fp_a)]:
                        _, ca, cb, fpa, fpb = order
                        pool[f"fake_fake_{condition_suffix}"].append({
                            "type": "paired",
                            "condition": f"fake_fake_{condition_suffix}",
                            "identity": identity,
                            "emotion": emotion,
                            "clip_id": f"{ca}+{cb}",
                            "clip_a": ca, "clip_b": cb,
                            "video_a": pipes_a[fpa] if ca == clip_a else pipes_b[fpa],
                            "video_b": pipes_b[fpb] if cb == clip_b else pipes_a[fpb],
                            "pipeline_a": fpa,
                            "pipeline_b": fpb,
                            "correct_answer": "both_fake",
                            "real_side": "none",
                        })

    # ── Single-video trials ──────────────────────────────────────
    pool["single_real_emotional"] = []
    pool["single_real_neutral"] = []
    pool["single_fake_emotional"] = []
    pool["single_fake_neutral"] = []

    for (identity, emotion, clip_id), pipelines in index.items():
        suffix = "emotional" if emotion == "emotional" else "neutral"

        # Real (source) single trials
        if "source" in pipelines:
            pool[f"single_real_{suffix}"].append({
                "type": "single",
                "condition": f"single_real_{suffix}",
                "identity": identity,
                "emotion": emotion,
                "clip_id": clip_id,
                "video_a": pipelines["source"],
                "video_b": "",
                "pipeline_a": "source",
                "pipeline_b": "",
                "correct_answer": "real",
                "real_side": "none",
            })

        # Fake single trials (one per pipeline)
        for pipe, path in pipelines.items():
            if pipe == "source":
                continue
            pool[f"single_fake_{suffix}"].append({
                "type": "single",
                "condition": f"single_fake_{suffix}",
                "identity": identity,
                "emotion": emotion,
                "clip_id": clip_id,
                "video_a": path,
                "video_b": "",
                "pipeline_a": pipe,
                "pipeline_b": "",
                "correct_answer": "fake",
                "real_side": "none",
            })

    return pool


def sample_trials(pool: dict[str, list], trials_per_cond: int) -> list[dict]:
    """Sample balanced trials across conditions."""
    trials = []
    for cond, candidates in pool.items():
        if not candidates:
            continue
        n = min(trials_per_cond, len(candidates))
        # Ensure counterbalancing: for real-fake paired, half A half B
        if cond.startswith("real_fake"):
            side_a = [c for c in candidates if c["real_side"] == "A"]
            side_b = [c for c in candidates if c["real_side"] == "B"]
            n_each = n // 2
            sampled = random.sample(side_a, min(n_each, len(side_a)))
            sampled += random.sample(side_b, min(n - len(sampled), len(side_b)))
        elif cond.startswith("single_"):
            # For single trials, just sample randomly
            sampled = random.sample(candidates, n)
        else:
            sampled = random.sample(candidates, n)
        trials.extend(sampled)

    random.shuffle(trials)
    return trials


# ── HTML ──────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Experimento: Identificación de Videos</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #0f0f1a; color: #e8e8e8; min-height: 100vh; }
.container { max-width: 1100px; margin: 0 auto; padding: 20px; }

/* ── Screens ── */
.screen { display: none; }
.screen.active { display: block; }

/* ── Welcome ── */
#welcome { text-align: center; padding-top: 30px; }
#welcome h1 { font-size: 32px; margin-bottom: 8px;
              background: linear-gradient(135deg, #4a90d9, #64ffda);
              -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
#welcome .sub { color: #888; margin-bottom: 30px; font-size: 14px; }
#welcome p { margin: 10px auto; max-width: 600px; line-height: 1.7; color: #bbb; font-size: 15px; }
.highlight { color: #64ffda; font-weight: 600; }

/* ── Demographics ── */
#demographics { max-width: 500px; margin: 0 auto; padding-top: 20px; }
#demographics h2 { text-align: center; margin-bottom: 20px; color: #64ffda; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; margin-bottom: 6px; color: #aaa; font-size: 14px; }
.form-group input, .form-group select {
    width: 100%; padding: 10px 14px; border: 2px solid #333; border-radius: 8px;
    background: #1a1a2e; color: #eee; font-size: 15px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #4a90d9; }

/* ── Progress ── */
.progress-bar { background: #222; border-radius: 10px; height: 6px; margin: 12px 0; overflow: hidden; }
.progress-fill { background: linear-gradient(90deg, #4a90d9, #64ffda); height: 100%;
                 transition: width 0.4s; border-radius: 10px; }
.progress-text { text-align: center; color: #666; font-size: 13px; }
.condition-tag { text-align: center; margin: 8px 0 12px; }
.condition-tag span { background: #1a2a4e; color: #4a90d9; padding: 4px 14px;
                      border-radius: 20px; font-size: 12px; font-weight: 600;
                      text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Video pair ── */
.video-pair { display: flex; gap: 20px; justify-content: center; margin: 10px 0; }
.video-box { flex: 1; max-width: 500px; }
.video-label { text-align: center; font-size: 18px; font-weight: 700; margin-bottom: 6px;
               letter-spacing: 1px; }
.video-label.a { color: #ff9f43; }
.video-label.b { color: #a29bfe; }
.video-wrap { background: #000; border-radius: 10px; overflow: hidden;
              border: 3px solid #222; transition: border-color 0.2s; }
.video-wrap.selected-a { border-color: #ff9f43; }
.video-wrap.selected-b { border-color: #a29bfe; }
.video-wrap.selected-both { border-color: #64ffda; }
video { width: 100%; display: block; object-fit: contain; }

/* ── Fixation cross overlay ── */
#fixation-cross { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                  background: #000; z-index: 9999; justify-content: center; align-items: center; }
#fixation-cross.visible { display: flex; }
#fixation-cross span { font-size: 72px; color: #fff; font-weight: 300; user-select: none; }

/* ── Emotion question ── */
.emotion-section { text-align: center; margin: 14px 0; }
.emotion-label { color: #888; font-size: 14px; margin-bottom: 8px; }
.emotion-row { display: flex; gap: 12px; justify-content: center; }
.emotion-btn { padding: 8px 24px; border: 2px solid #333; border-radius: 8px;
               background: #16213e; color: #777; cursor: pointer; font-size: 14px;
               transition: all 0.15s; }
.emotion-btn:hover { border-color: #4a90d9; }
.emotion-btn.selected { border-color: #4a90d9; background: #1a2a4e; color: #fff; }

/* ── Playback controls ── */
.playback-info { text-align: center; color: #555; font-size: 12px; margin: 4px 0;
                 min-height: 18px; }
.play-controls { display: flex; gap: 10px; justify-content: center; margin: 8px 0; }
.play-btn { padding: 8px 20px; border: 2px solid #333; border-radius: 8px;
            background: #16213e; color: #aaa; cursor: pointer; font-size: 13px;
            transition: all 0.15s; }
.play-btn:hover { border-color: #4a90d9; color: #fff; }

/* ── Choice buttons ── */
.choices { display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
           max-width: 700px; margin: 16px auto; }
.choice-btn { padding: 16px 12px; border: 3px solid #333; border-radius: 10px;
              background: #12122a; cursor: pointer; text-align: center;
              transition: all 0.2s; font-size: 15px; font-weight: 600; }
.choice-btn:hover { transform: scale(1.02); border-color: #555; }
.choice-btn.sel-a { border-color: #ff9f43; background: #2a1f10; color: #ff9f43; }
.choice-btn.sel-b { border-color: #a29bfe; background: #1a1a3e; color: #a29bfe; }
.choice-btn.sel-both-real { border-color: #2ecc71; background: #0f2a1a; color: #2ecc71; }
.choice-btn.sel-both-fake { border-color: #e74c3c; background: #2a0f0f; color: #e74c3c; }
.choice-btn.sel-real { border-color: #64ffda; background: #0f2a2a; color: #64ffda; }
.choice-btn.sel-fake { border-color: #ff6b6b; background: #2a0f0f; color: #ff6b6b; }

/* ── Confidence ── */
.conf-section { text-align: center; margin: 10px 0; }
.conf-label { color: #555; font-size: 12px; margin-bottom: 6px; }
.conf-row { display: flex; gap: 10px; justify-content: center; }
.conf-btn { padding: 6px 16px; border: 2px solid #333; border-radius: 8px;
            background: #16213e; color: #777; cursor: pointer; font-size: 12px;
            transition: all 0.15s; }
.conf-btn:hover { border-color: #4a90d9; }
.conf-btn.selected { border-color: #4a90d9; background: #1a2a4e; color: #fff; }

/* ── Submit / feedback ── */
.submit-btn { display: block; margin: 12px auto; padding: 12px 50px; border: none;
              border-radius: 8px; background: #4a90d9; color: #fff; font-size: 16px;
              cursor: pointer; font-weight: 600; transition: all 0.2s; }
.submit-btn:hover { background: #357abd; }
.submit-btn:disabled { background: #222; color: #555; cursor: not-allowed; }

.feedback { text-align: center; font-size: 20px; font-weight: 700; margin: 10px 0;
            min-height: 30px; }
.feedback.correct { color: #64ffda; }
.feedback.wrong { color: #ff6b6b; }

/* ── Start / nav buttons ── */
.btn-primary { padding: 14px 50px; border: none; border-radius: 8px;
               background: linear-gradient(135deg, #4a90d9, #64ffda); color: #0f0f1a;
               font-size: 17px; font-weight: 700; cursor: pointer; margin-top: 24px; }
.btn-primary:hover { transform: scale(1.03); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

/* ── Results ── */
#results { padding-top: 20px; }
.score-big { text-align: center; font-size: 64px; font-weight: 800; margin: 16px 0;
             background: linear-gradient(135deg, #4a90d9, #64ffda);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.score-label { text-align: center; color: #888; font-size: 16px; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; }
th { text-align: left; padding: 10px 12px; border-bottom: 2px solid #333; color: #666;
     font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
td { padding: 8px 12px; border-bottom: 1px solid #1a1a2e; font-size: 14px; }
tr:hover td { background: #12122a; }
.bar { display: inline-block; height: 8px; border-radius: 4px; margin-left: 8px;
       vertical-align: middle; }
.bar-good { background: linear-gradient(90deg, #4a90d9, #64ffda); }
.bar-bad { background: linear-gradient(90deg, #e74c3c, #ff6b6b); }
h3 { margin: 22px 0 8px; color: #64ffda; font-size: 15px; }
.insight { background: #1a1a2e; border-left: 3px solid #4a90d9; padding: 12px 16px;
           margin: 12px 0; border-radius: 0 8px 8px 0; font-size: 14px; color: #bbb;
           line-height: 1.6; }

/* ── Responsive ── */
@media (max-width: 768px) {
    .video-pair { flex-direction: column; align-items: center; }
    .video-box { max-width: 100%; }
    .choices { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<!-- Fixation cross overlay -->
<div id="fixation-cross"><span>+</span></div>

<div class="container">

<!-- ════ WELCOME ════ -->
<div id="welcome" class="screen active">
    <h1>Identificación de Videos Reales y Generados</h1>
    <p class="sub">Experimento de percepción — Avatar v2</p>
    <div id="welcome-mixed">
    <p>Verás dos tipos de ensayos:</p>
    <p style="text-align:left; max-width:500px; margin:15px auto;">
        <span class="highlight">Ensayos con 2 videos:</span> Verás dos videos de la misma persona.
        Debes decidir cuál es real, o si ambos son falsos.<br><br>
        <span class="highlight">Ensayos con 1 video:</span> Verás un solo video y debes decidir
        si es <strong>real</strong> o <strong>generado por IA</strong>.
    </p>
    <p style="color:#666; font-size:13px; margin-top:20px;">
        En los ensayos con dos videos, algunos pares contienen un video real y uno generado por IA,
        y otros contienen dos videos generados por IA.<br>
        Después de cada ensayo indicarás tu nivel de confianza y si percibiste emoción.</p>
    </div>
    <div id="welcome-2afc" style="display:none;">
    <p style="max-width:550px; margin:15px auto; line-height:1.7;">
        En cada ensayo verás <span class="highlight">un video corto</span> de una persona hablando.
        Tu tarea es decidir si el video es <strong>real</strong> o <strong>generado por inteligencia artificial</strong>.
    </p>
    <p style="color:#666; font-size:13px; margin-top:20px; max-width:500px; margin-left:auto; margin-right:auto;">
        Algunos videos son grabaciones reales y otros han sido creados con IA.<br>
        Después de cada ensayo indicarás tu nivel de confianza y si percibiste emoción en el video.</p>
    </div>
    <p style="color:#555; font-size:13px;" id="trial-count"></p>
    <button class="btn-primary" onclick="showScreen('consent')">Comenzar</button>
</div>

<!-- ════ CONSENT ════ -->
<div id="consent" class="screen">
    <div style="max-width:600px; margin:0 auto; padding-top:20px;">
        <h2 style="text-align:center; color:#64ffda; margin-bottom:20px;">Consentimiento Informado</h2>

        <div style="background:#1a1a2e; border-radius:10px; padding:20px; margin-bottom:20px;
                    max-height:350px; overflow-y:auto; border:1px solid #333; font-size:14px;
                    line-height:1.8; color:#bbb;">
            <p><strong style="color:#eee;">Título del estudio:</strong> Percepción humana de videos
               generados por inteligencia artificial — Paradigma de identificación real/falso.</p>

            <p><strong style="color:#eee;">Objetivo:</strong> Evaluar la capacidad de las personas para
               distinguir entre videos reales y videos generados por sistemas de inteligencia artificial.</p>

            <p><strong style="color:#eee;">Procedimiento:</strong> Se te presentarán pares de videos cortos
               (~5 segundos) de personas hablando. En cada ensayo, deberás indicar cuál video consideras
               real, o si ambos son reales o falsos. El experimento dura aproximadamente 15-20 minutos.</p>

            <p><strong style="color:#eee;">Riesgos:</strong> Este estudio no presenta riesgos conocidos
               más allá de los asociados con el uso habitual de un ordenador. Algunos videos pueden
               mostrar expresiones emocionales (tristeza, alegría).</p>

            <p><strong style="color:#eee;">Confidencialidad:</strong> Tus respuestas serán almacenadas
               de forma anónima y se utilizarán exclusivamente con fines de investigación académica.
               No se recogerán datos personales identificables más allá de los proporcionados
               voluntariamente (código de participante, edad, género).</p>

            <p><strong style="color:#eee;">Participación voluntaria:</strong> Tu participación es
               completamente voluntaria. Puedes abandonar el estudio en cualquier momento sin
               necesidad de justificación y sin consecuencia alguna.</p>

            <p><strong style="color:#eee;">Contacto:</strong> Para preguntas sobre el estudio,
               contacta al equipo de investigación.</p>
        </div>

        <div style="margin-bottom:16px;">
            <label style="display:flex; align-items:center; gap:10px; cursor:pointer; color:#ccc; font-size:14px;">
                <input type="checkbox" id="consent-1" onchange="validateConsent()"
                       style="width:18px; height:18px; accent-color:#64ffda;">
                He leído y comprendido la información anterior sobre el estudio.
            </label>
        </div>
        <div style="margin-bottom:16px;">
            <label style="display:flex; align-items:center; gap:10px; cursor:pointer; color:#ccc; font-size:14px;">
                <input type="checkbox" id="consent-2" onchange="validateConsent()"
                       style="width:18px; height:18px; accent-color:#64ffda;">
                Acepto participar voluntariamente en este estudio.
            </label>
        </div>
        <div style="margin-bottom:20px;">
            <label style="display:flex; align-items:center; gap:10px; cursor:pointer; color:#ccc; font-size:14px;">
                <input type="checkbox" id="consent-3" onchange="validateConsent()"
                       style="width:18px; height:18px; accent-color:#64ffda;">
                Entiendo que puedo abandonar el estudio en cualquier momento.
            </label>
        </div>

        <div style="text-align:center;">
            <button class="btn-primary" id="btn-consent" onclick="showScreen('demographics')" disabled>
                Acepto participar
            </button>
            <p style="margin-top:12px;">
                <a href="javascript:void(0)" onclick="window.close()"
                   style="color:#666; font-size:13px;">No deseo participar</a>
            </p>
        </div>
    </div>
</div>

<!-- ════ DEMOGRAPHICS ════ -->
<div id="demographics" class="screen">
    <h2>Datos del participante</h2>
    <div class="form-group">
        <label>Identificador (nombre o código)</label>
        <input type="text" id="dem-id" placeholder="Ej: participante_01">
    </div>
    <div class="form-group">
        <label>Edad</label>
        <input type="number" id="dem-age" min="18" max="99" placeholder="25">
    </div>
    <div class="form-group">
        <label>Género</label>
        <select id="dem-gender">
            <option value="">— Seleccionar —</option>
            <option value="male">Masculino</option>
            <option value="female">Femenino</option>
            <option value="non_binary">No binario</option>
            <option value="prefer_not">Prefiero no decir</option>
        </select>
    </div>
    <div class="form-group">
        <label>¿Tienes experiencia con inteligencia artificial o deepfakes?</label>
        <select id="dem-ai-exp">
            <option value="">— Seleccionar —</option>
            <option value="none">Ninguna</option>
            <option value="basic">Básica (he oído hablar)</option>
            <option value="moderate">Moderada (he visto ejemplos)</option>
            <option value="advanced">Avanzada (trabajo con IA)</option>
        </select>
    </div>
    <div style="text-align:center;">
        <button class="btn-primary" id="btn-start-test" onclick="startTest()" disabled>
            Iniciar Experimento
        </button>
    </div>
</div>

<!-- ════ TRIAL ════ -->
<div id="trial" class="screen">
    <div class="progress-bar"><div class="progress-fill" id="pbar"></div></div>
    <p class="progress-text" id="ptxt"></p>

    <!-- Sequential presentation: one video at a time, centered -->
    <div style="max-width:560px; margin:0 auto;">
        <div id="phase-indicator" style="text-align:center; margin:8px 0;">
            <span id="phase-a-dot" style="display:inline-block; width:12px; height:12px; border-radius:50%;
                  background:#ff9f43; margin:0 4px; opacity:0.3;"></span>
            <span id="phase-b-dot" style="display:inline-block; width:12px; height:12px; border-radius:50%;
                  background:#a29bfe; margin:0 4px; opacity:0.3;"></span>
            <span id="phase-decide-dot" style="display:inline-block; width:12px; height:12px; border-radius:50%;
                  background:#64ffda; margin:0 4px; opacity:0.3;"></span>
        </div>

        <!-- Video A phase -->
        <div id="phase-a" style="display:none;">
            <div class="video-label a" style="text-align:center; font-size:20px; margin-bottom:8px;">
                VIDEO A</div>
            <div class="video-wrap" id="wrap-a">
                <video id="vid-a" preload="auto" playsinline></video>
            </div>
            <div class="playback-info" id="play-info-a" style="text-align:center; color:#888;
                 font-size:13px; margin:8px 0; min-height:20px;"></div>
        </div>

        <!-- Video B phase -->
        <div id="phase-b" style="display:none;">
            <div class="video-label b" style="text-align:center; font-size:20px; margin-bottom:8px;">
                VIDEO B</div>
            <div class="video-wrap" id="wrap-b">
                <video id="vid-b" preload="auto" playsinline></video>
            </div>
            <div class="playback-info" id="play-info-b" style="text-align:center; color:#888;
                 font-size:13px; margin:8px 0; min-height:20px;"></div>
        </div>

        <!-- Decision phase: show both thumbnails as stills for reference -->
        <div id="phase-decide" style="display:none;">
            <p style="text-align:center; color:#888; font-size:14px; margin-bottom:12px;">
                Has visto ambos videos. Elige tu respuesta.</p>
            <div class="video-pair" style="display:flex; gap:12px; justify-content:center;">
                <div style="flex:1; text-align:center;">
                    <div class="video-label a" style="font-size:14px; margin-bottom:4px;">VIDEO A</div>
                    <div class="video-wrap" id="wrap-a-thumb" style="border-width:2px; cursor:pointer;"
                         onclick="replayOne('a')">
                        <video id="vid-a-thumb" preload="auto" playsinline muted
                               style="max-height:180px;"></video>
                    </div>
                    <div style="color:#555; font-size:11px; margin-top:4px;">clic para repetir</div>
                </div>
                <div style="flex:1; text-align:center;">
                    <div class="video-label b" style="font-size:14px; margin-bottom:4px;">VIDEO B</div>
                    <div class="video-wrap" id="wrap-b-thumb" style="border-width:2px; cursor:pointer;"
                         onclick="replayOne('b')">
                        <video id="vid-b-thumb" preload="auto" playsinline muted
                               style="max-height:180px;"></video>
                    </div>
                    <div style="color:#555; font-size:11px; margin-top:4px;">clic para repetir</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Play / Next controls (paired trials) -->
    <div class="play-controls" id="play-controls">
        <button class="play-btn" id="btn-play" onclick="playSequential()" style="padding:10px 30px;
                font-size:15px;">&#9654; Reproducir Video A</button>
    </div>

    <!-- Single-video play button -->
    <div id="single-play-controls" style="display:none; text-align:center; margin:8px 0;">
        <button class="play-btn" id="btn-play-single" onclick="playSingleVideo()" style="padding:10px 30px;
                font-size:15px;">&#9654; Reproducir Video</button>
    </div>

    <!-- Choices for PAIRED trials (hidden until both videos watched) -->
    <div id="choices-section" style="display:none;">
        <div class="choices" id="paired-choices">
            <div class="choice-btn" data-choice="video_a" onclick="pick('video_a')">
                El <strong style="color:#ff9f43">Video A</strong> es real
            </div>
            <div class="choice-btn" data-choice="video_b" onclick="pick('video_b')">
                El <strong style="color:#a29bfe">Video B</strong> es real
            </div>
            <div class="choice-btn" data-choice="both_real" onclick="pick('both_real')">
                <strong style="color:#2ecc71">Ambos</strong> son reales
            </div>
            <div class="choice-btn" data-choice="both_fake" onclick="pick('both_fake')">
                <strong style="color:#e74c3c">Ambos</strong> son falsos
            </div>
        </div>

        <!-- Choices for SINGLE trials -->
        <div id="single-choices" style="display:none;">
            <div style="display:flex; gap:20px; justify-content:center; max-width:500px; margin:0 auto;">
                <div class="choice-btn" data-choice="real" onclick="pick('real')"
                     style="flex:1; color:#64ffda;">
                    <strong>REAL</strong><br><span style="font-size:12px; font-weight:400; color:#888;">Video original</span>
                </div>
                <div class="choice-btn" data-choice="fake" onclick="pick('fake')"
                     style="flex:1; color:#ff6b6b;">
                    <strong>GENERADO</strong><br><span style="font-size:12px; font-weight:400; color:#888;">Creado por IA</span>
                </div>
            </div>
        </div>

        <div class="conf-section">
            <div class="conf-label">&#191;Qu&eacute; tan seguro/a est&aacute;s?</div>
            <div class="conf-row">
                <div class="conf-btn" data-c="1" onclick="setConf(1)">Adivinando</div>
                <div class="conf-btn" data-c="2" onclick="setConf(2)">Algo seguro/a</div>
                <div class="conf-btn" data-c="3" onclick="setConf(3)">Muy seguro/a</div>
            </div>
        </div>

        <!-- Emotion perception question (shown with choice+confidence) -->
        <div class="emotion-section" id="emotion-section">
            <div class="emotion-label">&iquest;Percibiste emoci&oacute;n en el v&iacute;deo?</div>
            <div class="emotion-row">
                <div class="emotion-btn" data-emo="neutral" onclick="setEmotion('neutral')">Neutral</div>
                <div class="emotion-btn" data-emo="emotional" onclick="setEmotion('emotional')">Emocional</div>
            </div>
        </div>

        <div class="feedback" id="feedback"></div>
        <button class="submit-btn" id="btn-submit" onclick="submitAnswer()" disabled>
            Confirmar respuesta
        </button>
    </div>
</div>

<!-- ════ RESULTS ════ -->
<div id="results" class="screen">
    <div class="score-label">Tu precisión general</div>
    <div class="score-big" id="score-pct"></div>
    <div id="results-body"></div>
</div>

</div><!-- container -->

<script>
const S = {
    choice: null, confidence: null, emotion_perceived: null,
    idx: 0, total: 0,
    answers: [],
    playCount: 0,
    trialStartTime: 0,
    trialType: 'paired',  // 'paired' or 'single'
};

/* ── Config from server ── */
let CFG = { show_feedback: true, prolific_pid: null, design: '2afc' };

/* ── Adapt UI to design on load ── */
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (CFG.design === '2afc') {
            const el2 = document.getElementById('welcome-2afc');
            const elm = document.getElementById('welcome-mixed');
            if (el2) el2.style.display = 'block';
            if (elm) elm.style.display = 'none';
        }
    }, 50);
});

/* ── Screen management ── */
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    if (id === 'demographics') {
        validateDemographics();
        // Auto-fill Prolific ID from URL if present
        const params = new URLSearchParams(window.location.search);
        const pid = params.get('PROLIFIC_PID') || params.get('participant_id');
        if (pid) {
            document.getElementById('dem-id').value = pid;
            CFG.prolific_pid = pid;
        }
    }
}

/* ── Consent validation ── */
function validateConsent() {
    const ok = document.getElementById('consent-1').checked
            && document.getElementById('consent-2').checked
            && document.getElementById('consent-3').checked;
    document.getElementById('btn-consent').disabled = !ok;
}

/* ── Demographics validation ── */
function validateDemographics() {
    const ok = document.getElementById('dem-id').value.trim()
            && document.getElementById('dem-age').value
            && document.getElementById('dem-gender').value
            && document.getElementById('dem-ai-exp').value;
    document.getElementById('btn-start-test').disabled = !ok;
}
['dem-id','dem-age','dem-gender','dem-ai-exp'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.addEventListener('input', validateDemographics);
              el.addEventListener('change', validateDemographics); }
});

/* ── Choice & confidence ── */
function pick(c) {
    S.choice = c;
    document.querySelectorAll('.choice-btn').forEach(b => {
        b.classList.remove('sel-a','sel-b','sel-both-real','sel-both-fake','sel-real','sel-fake');
    });
    const classes = {
        video_a:'sel-a', video_b:'sel-b', both_real:'sel-both-real', both_fake:'sel-both-fake',
        real:'sel-real', fake:'sel-fake',
    };
    document.querySelector(`[data-choice="${c}"]`).classList.add(classes[c] || '');
    // Highlight thumbnail borders in decision phase (paired only)
    if (S.trialType === 'paired') {
        const wrapA = document.getElementById('wrap-a-thumb');
        const wrapB = document.getElementById('wrap-b-thumb');
        if (wrapA && wrapB) {
            wrapA.className = 'video-wrap' +
                (c === 'video_a' ? ' selected-a' : c === 'both_real' || c === 'both_fake' ? ' selected-both' : '');
            wrapB.className = 'video-wrap' +
                (c === 'video_b' ? ' selected-b' : c === 'both_real' || c === 'both_fake' ? ' selected-both' : '');
        }
    }
    checkReady();
}

function setConf(c) {
    S.confidence = c;
    document.querySelectorAll('.conf-btn').forEach(b => b.classList.remove('selected'));
    document.querySelector(`.conf-btn[data-c="${c}"]`).classList.add('selected');
    checkReady();
}

function checkReady() {
    document.getElementById('btn-submit').disabled = !(S.choice && S.confidence && S.emotion_perceived);
}

function setEmotion(val) {
    S.emotion_perceived = val;
    document.querySelectorAll('.emotion-btn').forEach(b => b.classList.remove('selected'));
    document.querySelector(`.emotion-btn[data-emo="${val}"]`).classList.add('selected');
    checkReady();
}

function showFixation(durationMs) {
    return new Promise(resolve => {
        const el = document.getElementById('fixation-cross');
        el.classList.add('visible');
        setTimeout(() => { el.classList.remove('visible'); resolve(); }, durationMs);
    });
}

/* ── Sequential video playback ── */
// Phase: 'ready' -> 'playing_a' -> 'waiting_b' -> 'playing_b' -> 'deciding'
S.phase = 'ready';
S.bothWatched = false;

function setPhase(phase) {
    S.phase = phase;
    // Update phase dots
    document.getElementById('phase-a-dot').style.opacity =
        (phase === 'playing_a' || phase === 'cross_before_a') ? '1' : '0.3';
    document.getElementById('phase-b-dot').style.opacity =
        (phase === 'playing_b' || phase === 'cross_before_b') ? '1' : '0.3';
    document.getElementById('phase-decide-dot').style.opacity = phase === 'deciding' ? '1' : '0.3';

    // Show/hide video phases
    document.getElementById('phase-a').style.display = (phase === 'playing_a') ? 'block' : 'none';
    document.getElementById('phase-b').style.display = (phase === 'playing_b') ? 'block' : 'none';
    document.getElementById('phase-decide').style.display = (phase === 'deciding') ? 'block' : 'none';

    // Update button
    const btn = document.getElementById('btn-play');
    const controls = document.getElementById('play-controls');
    if (phase === 'ready') {
        controls.style.display = 'flex';
        btn.textContent = '▶ Reproducir Video A';
        btn.onclick = () => playSequential();
    } else if (phase === 'waiting_b') {
        controls.style.display = 'flex';
        btn.textContent = '▶ Reproducir Video B';
        btn.onclick = () => playVideoB();
    } else if (phase === 'deciding') {
        controls.style.display = 'none';
    } else {
        controls.style.display = 'none';
    }
}

async function playSequential() {
    setPhase('cross_before_a');
    await showFixation(500);
    setPhase('playing_a');
    const vidA = document.getElementById('vid-a');
    vidA.currentTime = 0;
    vidA.play();
    S.playCount++;
    document.getElementById('play-info-a').textContent = 'Reproduciendo...';

    vidA.onended = () => {
        document.getElementById('play-info-a').textContent = 'Completado';
        setPhase('waiting_b');
    };
}

async function playVideoB() {
    setPhase('cross_before_b');
    await showFixation(300);
    setPhase('playing_b');
    const vidB = document.getElementById('vid-b');
    vidB.currentTime = 0;
    vidB.play();
    document.getElementById('play-info-b').textContent = 'Reproduciendo...';

    vidB.onended = () => {
        document.getElementById('play-info-b').textContent = 'Completado';
        S.bothWatched = true;
        enterDecisionPhase();
    };
}

/* ── Single-video playback ── */
async function playSingleVideo() {
    document.getElementById('single-play-controls').style.display = 'none';

    // Pre-video fixation (500ms)
    await showFixation(500);

    // Show video A (reuse phase-a container)
    document.getElementById('phase-a').style.display = 'block';
    const vidA = document.getElementById('vid-a');
    vidA.currentTime = 0;
    vidA.play();
    S.playCount++;
    document.getElementById('play-info-a').textContent = 'Reproduciendo...';

    vidA.onended = async () => {
        document.getElementById('play-info-a').textContent = 'Completado';

        // Post-video fixation (300ms)
        await showFixation(300);

        // Hide video, show choices
        document.getElementById('phase-a').style.display = 'none';
        S.decisionStartTime = performance.now();
        document.getElementById('choices-section').style.display = 'block';
    };
}

function enterDecisionPhase() {
    setPhase('deciding');

    // Set thumbnail sources (same as main videos, paused at start)
    const thumbA = document.getElementById('vid-a-thumb');
    const thumbB = document.getElementById('vid-b-thumb');
    thumbA.src = document.getElementById('vid-a').src;
    thumbB.src = document.getElementById('vid-b').src;
    thumbA.currentTime = 0.5;
    thumbB.currentTime = 0.5;

    // Show choices
    document.getElementById('choices-section').style.display = 'block';

    // Start decision timer
    S.decisionStartTime = performance.now();
}

function replayOne(which) {
    // Replay a single video with audio in the decision phase
    const vid = which === 'a' ? document.getElementById('vid-a-thumb')
                               : document.getElementById('vid-b-thumb');
    vid.muted = false;
    vid.currentTime = 0;
    vid.play();
    S.playCount++;
    vid.onended = () => { vid.muted = true; };
}

/* ── API calls ── */
async function startTest() {
    const demo = {
        participant_id: document.getElementById('dem-id').value.trim(),
        age: parseInt(document.getElementById('dem-age').value),
        gender: document.getElementById('dem-gender').value,
        ai_experience: document.getElementById('dem-ai-exp').value,
    };
    const r = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(demo),
    });
    const d = await r.json();
    S.total = d.total;
    S.idx = 0;
    S.answers = [];
    showScreen('trial');
    loadTrial();
}

async function loadTrial() {
    const r = await fetch('/api/next');
    const d = await r.json();
    if (d.done) { showResults(); return; }

    S.idx = d.index;
    S.total = d.total;
    S.playCount = 0;
    S.bothWatched = false;
    S.trialStartTime = performance.now();
    S.trialType = d.type || 'paired';

    const pct = (d.index / d.total * 100).toFixed(0);
    document.getElementById('pbar').style.width = pct + '%';
    document.getElementById('ptxt').textContent = `Ensayo ${d.index + 1} de ${d.total}`;

    // Load videos
    const vidA = document.getElementById('vid-a');
    vidA.src = d.video_a_url;
    vidA.load();
    if (S.trialType === 'paired') {
        const vidB = document.getElementById('vid-b');
        vidB.src = d.video_b_url;
        vidB.load();
    }

    // Reset choice state
    S.choice = null; S.confidence = null; S.emotion_perceived = null;
    document.querySelectorAll('.choice-btn').forEach(b =>
        b.classList.remove('sel-a','sel-b','sel-both-real','sel-both-fake','sel-real','sel-fake'));
    document.querySelectorAll('.conf-btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('btn-submit').disabled = true;
    document.getElementById('btn-submit').style.display = 'block';
    document.getElementById('feedback').textContent = '';
    document.getElementById('feedback').className = 'feedback';

    // Hide choices until video watched
    document.getElementById('choices-section').style.display = 'none';
    document.querySelectorAll('.emotion-btn').forEach(b => b.classList.remove('selected'));

    // Show/hide appropriate choice buttons for trial type
    document.getElementById('paired-choices').style.display = S.trialType === 'paired' ? 'grid' : 'none';
    document.getElementById('single-choices').style.display = S.trialType === 'single' ? 'block' : 'none';

    // Show/hide phase indicator dots
    document.getElementById('phase-indicator').style.display = S.trialType === 'paired' ? 'block' : 'none';

    // Update Video A label depending on trial type
    const labelA = document.querySelector('#phase-a .video-label');
    if (labelA) labelA.textContent = S.trialType === 'single' ? 'VIDEO' : 'VIDEO A';

    if (S.trialType === 'single') {
        // Single-video trial: show single play button, hide paired controls
        document.getElementById('play-controls').style.display = 'none';
        document.getElementById('single-play-controls').style.display = 'block';
        document.getElementById('btn-play-single').textContent = '\u25b6 Reproducir Video';
        document.getElementById('phase-a').style.display = 'none';
        document.getElementById('phase-b').style.display = 'none';
        document.getElementById('phase-decide').style.display = 'none';
    } else {
        // Paired trial: use existing flow
        document.getElementById('single-play-controls').style.display = 'none';
        setPhase('ready');
    }
}

async function submitAnswer() {
    const rt = Math.round(performance.now() - (S.decisionStartTime || S.trialStartTime));

    // Pause all videos
    document.getElementById('vid-a').pause();
    document.getElementById('vid-b').pause();
    document.getElementById('vid-a-thumb').pause();
    document.getElementById('vid-b-thumb').pause();

    // Send all answers at once (choice + confidence + emotion)
    const payload = {
        choice: S.choice,
        confidence: S.confidence,
        emotion_perceived: S.emotion_perceived,
        reaction_time_ms: rt,
        play_count: S.playCount,
    };
    const r = await fetch('/api/answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    });
    const d = await r.json();

    document.getElementById('btn-submit').style.display = 'none';

    // Show feedback only if enabled (pilot mode)
    const fb = document.getElementById('feedback');
    if (CFG.show_feedback) {
        const answerLabels = {
            video_a: 'Video A es real',
            video_b: 'Video B es real',
            both_real: 'Ambos son reales',
            both_fake: 'Ambos son falsos',
            real: 'El video es real',
            fake: 'El video es generado por IA',
        };
        if (d.correct) {
            fb.textContent = '¡Correcto!';
            fb.className = 'feedback correct';
        } else {
            fb.textContent = `Incorrecto — ${answerLabels[d.correct_answer] || d.correct_answer}`;
            fb.className = 'feedback wrong';
        }
    }

    setTimeout(loadTrial, CFG.show_feedback ? 2000 : 800);
}

async function showResults() {
    const r = await fetch('/api/results');
    const d = await r.json();

    document.getElementById('score-pct').textContent = d.accuracy_pct + '%';

    let html = '';

    // By condition
    html += '<h3>Por condición experimental</h3>';
    html += '<table><tr><th>Condición</th><th>Correctas</th><th>Total</th><th>Precisión</th></tr>';
    for (const row of d.by_condition) {
        const w = Math.round(row.pct * 0.8);
        const cls = row.pct >= 50 ? 'bar-good' : 'bar-bad';
        html += `<tr><td>${row.label}</td><td>${row.correct}</td><td>${row.total}</td>` +
                `<td>${row.pct}% <span class="bar ${cls}" style="width:${w}px"></span></td></tr>`;
    }
    html += '</table>';

    // By emotion
    if (d.by_emotion.length) {
        html += '<h3>Por emoción</h3>';
        html += '<table><tr><th>Emoción</th><th>Correctas</th><th>Total</th><th>Precisión</th></tr>';
        for (const row of d.by_emotion) {
            const w = Math.round(row.pct * 0.8);
            const cls = row.pct >= 50 ? 'bar-good' : 'bar-bad';
            html += `<tr><td>${row.label}</td><td>${row.correct}</td><td>${row.total}</td>` +
                    `<td>${row.pct}% <span class="bar ${cls}" style="width:${w}px"></span></td></tr>`;
        }
        html += '</table>';
    }

    // By identity
    if (d.by_identity.length) {
        html += '<h3>Por identidad</h3>';
        html += '<table><tr><th>Actor</th><th>Correctas</th><th>Total</th><th>Precisión</th></tr>';
        for (const row of d.by_identity) {
            const w = Math.round(row.pct * 0.8);
            const cls = row.pct >= 50 ? 'bar-good' : 'bar-bad';
            html += `<tr><td>${row.label}</td><td>${row.correct}</td><td>${row.total}</td>` +
                    `<td>${row.pct}% <span class="bar ${cls}" style="width:${w}px"></span></td></tr>`;
        }
        html += '</table>';
    }

    // Response pattern analysis (paired trials only)
    if (d.response_pattern && d.response_pattern.paired_count > 0) {
        html += '<h3>Patrón de respuestas (ensayos con 2 videos)</h3>';
        html += '<div class="insight">';
        html += `<strong>Sesgo de respuesta:</strong> ${d.response_pattern.bias_description}<br>`;
        html += `<strong>"Ambos reales" seleccionado:</strong> ${d.response_pattern.both_real_count} veces `;
        html += `(${d.response_pattern.both_real_pct}% de ensayos pareados) — nunca es correcto en este diseño<br>`;
        html += `<strong>"Ambos falsos" seleccionado:</strong> ${d.response_pattern.both_fake_count} veces `;
        html += `(correctas: ${d.response_pattern.both_fake_correct}/${d.response_pattern.both_fake_count})`;
        html += '</div>';
    }

    // SDT metrics
    if (d.sdt_paired) {
        html += '<h3>Sensibilidad — Ensayos con 2 videos (pareados)</h3>';
        html += '<div class="insight">';
        html += `<strong>d\' (sensibilidad):</strong> ${d.sdt_paired.d_prime} — `;
        html += d.sdt_paired.d_prime > 1.5 ? 'buena discriminación' :
                d.sdt_paired.d_prime > 0.5 ? 'discriminación moderada' : 'discriminación pobre';
        html += `<br><strong>Criterio (β):</strong> ${d.sdt_paired.criterion} — `;
        html += d.sdt_paired.criterion > 0.3 ? 'sesgo conservador (tiende a decir "fake")' :
                d.sdt_paired.criterion < -0.3 ? 'sesgo liberal (tiende a decir "real")' : 'sin sesgo notable';
        html += '</div>';
    }
    if (d.sdt_single) {
        html += '<h3>Sensibilidad — Ensayos con 1 video (individual)</h3>';
        html += '<div class="insight">';
        html += `<strong>d\' (sensibilidad):</strong> ${d.sdt_single.d_prime} — `;
        html += d.sdt_single.d_prime > 1.5 ? 'buena discriminación' :
                d.sdt_single.d_prime > 0.5 ? 'discriminación moderada' : 'discriminación pobre';
        html += `<br><strong>Criterio (β):</strong> ${d.sdt_single.criterion} — `;
        html += d.sdt_single.criterion > 0.3 ? 'sesgo conservador (tiende a decir "fake")' :
                d.sdt_single.criterion < -0.3 ? 'sesgo liberal (tiende a decir "real")' : 'sin sesgo notable';
        html += '</div>';
    }

    // Confidence analysis
    if (d.confidence_analysis) {
        html += '<h3>Análisis de confianza</h3>';
        html += '<div class="insight">';
        html += `<strong>Confianza media (correctas):</strong> ${d.confidence_analysis.mean_conf_correct}<br>`;
        html += `<strong>Confianza media (incorrectas):</strong> ${d.confidence_analysis.mean_conf_incorrect}<br>`;
        html += d.confidence_analysis.overconfidence ?
            '<em>⚠ Se detecta sobreconfianza: alta confianza en respuestas incorrectas</em>' :
            '<em>La confianza se alinea correctamente con la precisión</em>';
        html += '</div>';
    }

    // Reaction time
    if (d.rt_analysis) {
        html += '<h3>Tiempos de reacción</h3>';
        html += '<div class="insight">';
        html += `<strong>Mediana (correctas):</strong> ${d.rt_analysis.median_rt_correct}s<br>`;
        html += `<strong>Mediana (incorrectas):</strong> ${d.rt_analysis.median_rt_incorrect}s`;
        html += '</div>';
    }

    html += `<p style="color:#555;margin-top:30px;text-align:center;font-size:12px;">` +
            `Sesión guardada — ID: ${d.session_id}</p>`;

    html += '<p style="text-align:center;margin-top:20px;">' +
            '<strong style="color:#64ffda;font-size:18px;">¡Gracias por participar!</strong></p>';

    document.getElementById('results-body').innerHTML = html;
    showScreen('results');

    // Prolific auto-redirect after 5 seconds if configured
    if (CFG.prolific_pid) {
        setTimeout(() => { fetch('/api/completion').then(r => {
            if (r.redirected) window.location.href = r.url;
        }); }, 5000);
    }
}
</script>
</body>
</html>"""


# ── Flask routes ──────────────────────────────────────────────────

APP_CONFIG = {"show_feedback": True, "prolific_completion_url": None}


@app.route("/")
def index():
    # Inject config into HTML
    is_2afc = APP_CONFIG.get("design", "2afc") == "2afc"
    config_script = f"""<script>
    CFG.show_feedback = {'true' if APP_CONFIG['show_feedback'] else 'false'};
    CFG.design = '{'2afc' if is_2afc else 'mixed'}';
    </script>"""
    return HTML.replace("</body>", config_script + "</body>")


@app.route("/api/export-csv")
def export_csv():
    """Export all 4AFC sessions to CSV for statistical analysis."""
    import csv
    import io

    results_dir = RESULTS_DIR
    if not results_dir.exists():
        return "No results yet", 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "session_id", "participant_id", "age", "gender", "ai_experience",
        "trial_type", "trial_index", "condition", "identity", "emotion", "clip_id",
        "pipeline_a", "pipeline_b", "real_side", "correct_answer",
        "participant_choice", "correct", "confidence",
        "reaction_time_ms", "play_count", "emotion_perceived",
    ])

    for jf in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(jf.read_text())
        except Exception:
            continue
        demo = data.get("demographics", {})
        sid = data.get("session_id", jf.stem)
        for ans in data.get("answers", []):
            trial_type = "single" if ans.get("condition", "").startswith("single_") else "paired"
            writer.writerow([
                sid,
                demo.get("participant_id", ""),
                demo.get("age", ""),
                demo.get("gender", ""),
                demo.get("ai_experience", ""),
                trial_type,
                ans.get("index", ""),
                ans.get("condition", ""),
                ans.get("identity", ""),
                ans.get("emotion", ""),
                ans.get("clip_id", ""),
                ans.get("pipeline_a", ""),
                ans.get("pipeline_b", ""),
                ans.get("real_side", ""),
                ans.get("correct_answer", ""),
                ans.get("participant_choice", ""),
                1 if ans.get("correct") else 0,
                ans.get("confidence", ""),
                ans.get("reaction_time_ms", ""),
                ans.get("play_count", ""),
                ans.get("emotion_perceived", ""),
            ])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=4afc_results.csv"},
    )


@app.route("/api/completion")
def completion():
    """Prolific completion redirect."""
    url = APP_CONFIG.get("prolific_completion_url")
    if url:
        from flask import redirect
        return redirect(url)
    return jsonify({"status": "completed"})


@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.json or {}
    session["id"] = str(uuid.uuid4())[:8]
    session["demographics"] = {
        "participant_id": data.get("participant_id", "anonymous"),
        "age": data.get("age"),
        "gender": data.get("gender"),
        "ai_experience": data.get("ai_experience"),
    }
    session["trials"] = [t.copy() for t in TRIALS]
    random.shuffle(session["trials"])
    session["idx"] = 0
    session["answers"] = []
    session["start_time"] = time.time()
    return jsonify({"total": len(session["trials"])})


@app.route("/api/next")
def api_next():
    idx = session.get("idx", 0)
    trials = session.get("trials", [])
    if idx >= len(trials):
        return jsonify({"done": True})
    t = trials[idx]
    resp = {
        "done": False,
        "index": idx,
        "total": len(trials),
        "type": t.get("type", "paired"),
        "video_a_url": f"/video?path={t['video_a']}",
    }
    if t.get("type") != "single":
        resp["video_b_url"] = f"/video?path={t['video_b']}"
    return jsonify(resp)


@app.route("/video")
def serve_video():
    path = request.args.get("path", "")
    if not path:
        return "Not found", 404
    resolved = Path(path).resolve()
    # Only serve files from the normalized data directory
    allowed = Path(__file__).resolve().parent / "data"
    if not str(resolved).startswith(str(allowed)):
        return "Forbidden", 403
    if not resolved.exists() or not resolved.is_file():
        return "Not found", 404
    return send_file(str(resolved), mimetype="video/mp4")


@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.json
    idx = session.get("idx", 0)
    trials = session.get("trials", [])
    if idx >= len(trials):
        return jsonify({"error": "done"}), 400

    t = trials[idx]
    choice = data.get("choice")
    correct_answer = t["correct_answer"]
    is_correct = (choice == correct_answer)

    ans = {
        "index": idx,
        "condition": t["condition"],
        "identity": t["identity"],
        "emotion": t["emotion"],
        "clip_id": t["clip_id"],
        "pipeline_a": t["pipeline_a"],
        "pipeline_b": t["pipeline_b"],
        "real_side": t["real_side"],
        "correct_answer": correct_answer,
        "participant_choice": choice,
        "correct": is_correct,
        "confidence": data.get("confidence", 1),
        "reaction_time_ms": data.get("reaction_time_ms", 0),
        "play_count": data.get("play_count", 0),
        "emotion_perceived": data.get("emotion_perceived"),
    }

    answers = session.get("answers", [])
    answers.append(ans)
    session["answers"] = answers
    session["idx"] = idx + 1

    # Save incrementally after each answer (so partial sessions aren't lost)
    session_id = session.get("id", "unknown")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = RESULTS_DIR / f"{session_id}.json"
    with open(save_path, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "demographics": session.get("demographics", {}),
            "trials_completed": len(answers),
            "trials_total": len(session.get("trials", [])),
            "answers": answers,
        }, f, indent=2, ensure_ascii=False)

    return jsonify({
        "correct": is_correct,
        "correct_answer": correct_answer,
    })


@app.route("/api/results")
def api_results():
    answers = session.get("answers", [])
    if not answers:
        return jsonify({"error": "no answers"}), 400

    total_correct = sum(1 for a in answers if a["correct"])
    accuracy = round(total_correct / len(answers) * 100) if answers else 0

    # ── By condition ──
    by_condition = []
    for cond_key, cond_label in CONDITION_LABELS.items():
        subset = [a for a in answers if a["condition"] == cond_key]
        if subset:
            c = sum(1 for a in subset if a["correct"])
            by_condition.append({
                "label": cond_label, "correct": c, "total": len(subset),
                "pct": round(c / len(subset) * 100),
            })

    # ── By emotion ──
    by_emotion = []
    for emo in sorted(set(a["emotion"] for a in answers)):
        subset = [a for a in answers if a["emotion"] == emo]
        c = sum(1 for a in subset if a["correct"])
        by_emotion.append({
            "label": emo.capitalize(), "correct": c, "total": len(subset),
            "pct": round(c / len(subset) * 100),
        })

    # ── By identity ──
    by_identity = []
    for ident in sorted(set(a["identity"] for a in answers)):
        subset = [a for a in answers if a["identity"] == ident]
        c = sum(1 for a in subset if a["correct"])
        by_identity.append({
            "label": ident, "correct": c, "total": len(subset),
            "pct": round(c / len(subset) * 100),
        })

    # ── Response pattern (paired trials only) ──
    paired_answers = [a for a in answers if a["condition"].startswith(("real_fake", "fake_fake"))]
    choice_counts = {}
    for a in paired_answers:
        choice_counts[a["participant_choice"]] = choice_counts.get(a["participant_choice"], 0) + 1
    most_common = max(choice_counts, key=choice_counts.get) if choice_counts else "none"
    bias_map = {
        "video_a": "Sesgo hacia Video A",
        "video_b": "Sesgo hacia Video B",
        "both_real": "Sesgo hacia 'ambos reales'",
        "both_fake": "Sesgo hacia 'ambos falsos'",
    }
    both_real_answers = [a for a in paired_answers if a["participant_choice"] == "both_real"]
    both_fake_answers = [a for a in paired_answers if a["participant_choice"] == "both_fake"]
    response_pattern = {
        "paired_count": len(paired_answers),
        "bias_description": bias_map.get(most_common, "Sin sesgo claro"),
        "both_real_count": len(both_real_answers),
        "both_real_pct": round(len(both_real_answers) / len(paired_answers) * 100) if paired_answers else 0,
        "both_fake_count": len(both_fake_answers),
        "both_fake_correct": sum(1 for a in both_fake_answers if a["correct"]),
    }

    # ── SDT for paired trials ──
    real_fake_trials = [a for a in answers if a["condition"].startswith("real_fake")]
    fake_fake_trials = [a for a in answers if a["condition"].startswith("fake_fake")]

    from statistics import NormalDist
    nd = NormalDist()

    def compute_sdt(hit_rate_val, fa_rate_val):
        hr = max(0.01, min(0.99, hit_rate_val))
        far = max(0.01, min(0.99, fa_rate_val))
        z_hit = nd.inv_cdf(hr)
        z_fa = nd.inv_cdf(far)
        return {"d_prime": round(z_hit - z_fa, 2), "criterion": round(-0.5 * (z_hit + z_fa), 2)}

    sdt_paired = None
    if real_fake_trials and fake_fake_trials:
        hits = sum(1 for a in real_fake_trials if a["correct"])
        hit_rate = hits / len(real_fake_trials)
        false_alarms = sum(1 for a in fake_fake_trials
                          if a["participant_choice"] in ("video_a", "video_b"))
        fa_rate = false_alarms / len(fake_fake_trials)
        sdt_paired = compute_sdt(hit_rate, fa_rate)

    # ── SDT for single trials ──
    single_real = [a for a in answers if a["condition"].startswith("single_real")]
    single_fake = [a for a in answers if a["condition"].startswith("single_fake")]

    sdt_single = None
    if single_real and single_fake:
        # Hit = correctly say "fake" when it's fake; FA = say "fake" when it's real
        hits_s = sum(1 for a in single_fake if a["participant_choice"] == "fake")
        hit_rate_s = hits_s / len(single_fake)
        fa_s = sum(1 for a in single_real if a["participant_choice"] == "fake")
        fa_rate_s = fa_s / len(single_real)
        sdt_single = compute_sdt(hit_rate_s, fa_rate_s)

    # ── Confidence analysis ──
    correct_confs = [a["confidence"] for a in answers if a["correct"]]
    wrong_confs = [a["confidence"] for a in answers if not a["correct"]]
    confidence_analysis = None
    if correct_confs and wrong_confs:
        mean_cc = round(sum(correct_confs) / len(correct_confs), 2)
        mean_wc = round(sum(wrong_confs) / len(wrong_confs), 2)
        confidence_analysis = {
            "mean_conf_correct": mean_cc,
            "mean_conf_incorrect": mean_wc,
            "overconfidence": mean_wc > mean_cc,
        }

    # ── RT analysis ──
    correct_rts = [a["reaction_time_ms"] / 1000 for a in answers if a["correct"] and a["reaction_time_ms"] > 0]
    wrong_rts = [a["reaction_time_ms"] / 1000 for a in answers if not a["correct"] and a["reaction_time_ms"] > 0]
    rt_analysis = None
    if correct_rts and wrong_rts:
        correct_rts.sort()
        wrong_rts.sort()
        rt_analysis = {
            "median_rt_correct": round(correct_rts[len(correct_rts) // 2], 1),
            "median_rt_incorrect": round(wrong_rts[len(wrong_rts) // 2], 1),
        }

    # ── Save ──
    session_id = session.get("id", "unknown")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = RESULTS_DIR / f"{session_id}.json"
    result_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "duration_sec": round(time.time() - session.get("start_time", time.time())),
        "demographics": session.get("demographics", {}),
        "design": {
            "paradigm": APP_CONFIG.get("design", "mixed"),
            "conditions": list(set(a["condition"] for a in answers)),
            "response_options_paired": ["video_a", "video_b", "both_real", "both_fake"],
            "response_options_single": ["real", "fake"],
        },
        "summary": {
            "total": len(answers),
            "correct": total_correct,
            "accuracy_pct": accuracy,
            "sdt_paired": sdt_paired,
            "sdt_single": sdt_single,
        },
        "answers": answers,
    }
    with open(save_path, "w") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    return jsonify({
        "session_id": session_id,
        "accuracy_pct": accuracy,
        "total": len(answers),
        "correct": total_correct,
        "by_condition": by_condition,
        "by_emotion": by_emotion,
        "by_identity": by_identity,
        "response_pattern": response_pattern,
        "sdt_paired": sdt_paired,
        "sdt_single": sdt_single,
        "confidence_analysis": confidence_analysis,
        "rt_analysis": rt_analysis,
    })


# ── Admin routes ──────────────────────────────────────────────────

ADMIN_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Admin</title>
<style>
body { font-family: -apple-system, sans-serif; background: #0f0f1a; color: #eee;
       max-width: 800px; margin: 40px auto; padding: 20px; }
h1 { color: #64ffda; }
table { width: 100%%; border-collapse: collapse; margin: 20px 0; }
th { text-align: left; padding: 10px; border-bottom: 2px solid #333; color: #888; font-size: 13px; }
td { padding: 8px 10px; border-bottom: 1px solid #1a1a2e; font-size: 14px; }
.btn { display: inline-block; padding: 10px 24px; border: none; border-radius: 8px;
       font-size: 15px; font-weight: 600; cursor: pointer; margin: 6px; text-decoration: none; }
.btn-blue { background: #4a90d9; color: #fff; }
.btn-red { background: #e74c3c; color: #fff; }
.btn:hover { opacity: 0.85; }
.stat { display: inline-block; background: #1a1a2e; padding: 16px 24px; border-radius: 10px;
        margin: 8px; text-align: center; }
.stat-num { font-size: 36px; font-weight: 800; color: #64ffda; }
.stat-label { font-size: 13px; color: #888; margin-top: 4px; }
.warn { background: #2a1010; border: 1px solid #e74c3c; padding: 14px; border-radius: 8px;
        margin: 16px 0; display: none; }
</style></head><body>
<h1>Experiment Admin</h1>
<div>
  <div class="stat"><div class="stat-num">%(total)d</div><div class="stat-label">Total sessions</div></div>
  <div class="stat"><div class="stat-num">%(complete)d</div><div class="stat-label">Completed</div></div>
  <div class="stat"><div class="stat-num">%(in_progress)d</div><div class="stat-label">In progress</div></div>
</div>

%(session_table)s

<div style="margin-top: 30px;">
  <a class="btn btn-blue" href="/admin/export?key=%(key)s">Download CSV</a>
  <button class="btn btn-red" onclick="document.getElementById('warn').style.display='block'">Reset all data</button>
</div>
<div class="warn" id="warn">
  <strong>This will delete ALL results.</strong> Are you sure?<br><br>
  <form method="POST" action="/admin/reset?key=%(key)s" style="display:inline;">
    <button class="btn btn-red" type="submit">Yes, delete everything</button>
  </form>
  <button class="btn btn-blue" onclick="document.getElementById('warn').style.display='none'">Cancel</button>
</div>
</body></html>"""


def _check_admin():
    return request.args.get("key") == ADMIN_KEY


@app.route("/admin")
def admin_dashboard():
    if not _check_admin():
        return "Forbidden — add ?key=YOUR_ADMIN_KEY", 403

    results_dir = RESULTS_DIR
    sessions = []
    if results_dir.exists():
        for jf in sorted(results_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                data = json.loads(jf.read_text())
            except Exception:
                continue
            demo = data.get("demographics", {})
            summary = data.get("summary", {})
            status = data.get("status", "completed" if summary else "in_progress")
            sessions.append({
                "session_id": data.get("session_id", jf.stem),
                "participant": demo.get("participant_id", "—"),
                "trials": f"{data.get('trials_completed', summary.get('total', '?'))}/{data.get('trials_total', summary.get('total', '?'))}",
                "accuracy": f"{summary.get('accuracy_pct', '—')}%" if summary.get("accuracy_pct") is not None else "—",
                "status": status,
                "time": data.get("timestamp", "—")[:16],
            })

    total = len(sessions)
    complete = sum(1 for s in sessions if s["status"] == "completed")
    in_progress = total - complete

    if sessions:
        rows = ""
        for s in sessions:
            rows += f"<tr><td>{s['session_id']}</td><td>{s['participant']}</td>"
            rows += f"<td>{s['trials']}</td><td>{s['accuracy']}</td>"
            rows += f"<td>{s['status']}</td><td>{s['time']}</td></tr>"
        table = ("<table><tr><th>Session</th><th>Participant</th><th>Trials</th>"
                 "<th>Accuracy</th><th>Status</th><th>Time</th></tr>" + rows + "</table>")
    else:
        table = "<p style='color:#666;'>No sessions yet.</p>"

    return ADMIN_HTML % {
        "total": total, "complete": complete, "in_progress": in_progress,
        "session_table": table, "key": ADMIN_KEY,
    }


@app.route("/admin/export")
def admin_export():
    if not _check_admin():
        return "Forbidden", 403
    return export_csv()


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    if not _check_admin():
        return "Forbidden", 403

    results_dir = RESULTS_DIR
    deleted = 0
    if results_dir.exists():
        for jf in results_dir.glob("*.json"):
            jf.unlink()
            deleted += 1

    # Clear flask sessions
    session_dir = app.config.get("SESSION_FILE_DIR", "")
    if session_dir and Path(session_dir).exists():
        shutil.rmtree(session_dir, ignore_errors=True)
        Path(session_dir).mkdir(parents=True, exist_ok=True)

    return (f"<html><body style='background:#0f0f1a;color:#eee;font-family:sans-serif;text-align:center;padding:60px;'>"
            f"<h2 style='color:#64ffda;'>Reset complete</h2>"
            f"<p>Deleted {deleted} session(s).</p>"
            f"<a href='/admin?key={ADMIN_KEY}' style='color:#4a90d9;'>Back to admin</a>"
            f"</body></html>")


def init_trials(normalized_dir="data/normalized", trials_per_cond=8, use_all=False,
                min_duration=3.0, min_volume=-28.0, no_feedback=False,
                prolific_url=None, skip_checks=False, design="2afc",
                curated_dir=None):
    """Initialize trials — called by main() and by gunicorn wsgi.py."""
    global TRIALS

    APP_CONFIG["show_feedback"] = not no_feedback
    APP_CONFIG["design"] = design
    if prolific_url:
        APP_CONFIG["prolific_completion_url"] = prolific_url

    if curated_dir and Path(curated_dir).exists():
        print(f"Using curated videos: {curated_dir}")
        video_index = discover_curated_videos(curated_dir, skip_checks=skip_checks)
        print(f"  Found {len(video_index)} unique clips")
    else:
        if skip_checks:
            print("Discovering videos (skipping ffprobe checks — pre-validated)...")
        else:
            print(f"Discovering videos (min duration: {min_duration}s, min volume: {min_volume}dB)...")
        video_index = discover_videos(normalized_dir, min_duration=min_duration,
                                      min_volume_db=min_volume, skip_checks=skip_checks)
        print(f"  Found {len(video_index)} unique clips across pipelines")

    if design == "2afc":
        print("Building 2AFC trial pool (single-video only)...")
        pool = build_2afc_pool(video_index)
    else:
        print("Building mixed trial pool (paired + single)...")
        pool = build_trial_pool(video_index)

    active_labels = {k: v for k, v in CONDITION_LABELS.items() if k in pool}
    for cond, trials in pool.items():
        label = active_labels.get(cond, cond)
        print(f"  {label}: {len(trials)} possible trials")

    if use_all:
        TRIALS = []
        for t_list in pool.values():
            TRIALS.extend(t_list)
        random.shuffle(TRIALS)
    else:
        TRIALS = sample_trials(pool, trials_per_cond)

    cond_counts = {}
    for t in TRIALS:
        cond_counts[t["condition"]] = cond_counts.get(t["condition"], 0) + 1

    print(f"\nSelected {len(TRIALS)} trials:")
    for cond in pool:
        label = CONDITION_LABELS.get(cond, cond)
        print(f"  {label}: {cond_counts.get(cond, 0)}")

    return TRIALS


def main():
    parser = argparse.ArgumentParser(description="Deepfake Detection Experiment")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--design", choices=["2afc", "mixed"], default="2afc",
                        help="Experiment design: 2afc (single-video only) or mixed (paired + single)")
    parser.add_argument("--curated-dir", default="data/curated",
                        help="Path to curated videos (source/ + fake/) for 2afc design")
    parser.add_argument("--trials-per-cond", type=int, default=8,
                        help="Trials per condition (default: 8)")
    parser.add_argument("--all", action="store_true",
                        help="Use all available trials (no sampling)")
    parser.add_argument("--normalized-dir", default="data/normalized",
                        help="Path to normalized videos directory (for mixed design)")
    parser.add_argument("--min-duration", type=float, default=3.0,
                        help="Minimum video duration in seconds (default: 3.0)")
    parser.add_argument("--min-volume", type=float, default=-28.0,
                        help="Minimum mean audio volume in dB (default: -28.0)")
    parser.add_argument("--no-feedback", action="store_true",
                        help="Disable correctness feedback (use for real experiment)")
    parser.add_argument("--prolific-url", type=str, default=None,
                        help="Prolific completion URL for redirect after experiment")
    args = parser.parse_args()

    init_trials(
        normalized_dir=args.normalized_dir,
        trials_per_cond=args.trials_per_cond,
        use_all=args.all,
        min_duration=args.min_duration,
        min_volume=args.min_volume,
        no_feedback=args.no_feedback,
        prolific_url=args.prolific_url,
        design=args.design,
        curated_dir=args.curated_dir,
    )

    design_label = "2AFC single-video" if args.design == "2afc" else "mixed paired+single"
    print(f"\n{'=' * 55}")
    print(f"  Experiment — http://localhost:{args.port}")
    print(f"  ({len(TRIALS)} trials, {design_label})")
    print(f"{'=' * 55}\n")

    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
