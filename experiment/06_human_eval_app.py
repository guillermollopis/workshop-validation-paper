#!/usr/bin/env python3
"""
Phase 4: Human evaluation web application.

Flask-based MOS rating interface. Participants watch videos and rate them
on 4 dimensions: overall quality, lip sync, voice naturalness, visual naturalness.

Usage:
  python3 06_human_eval_app.py                     # start server on port 5000
  python3 06_human_eval_app.py --port 8080
  python3 06_human_eval_app.py --demo              # load demo data for testing
"""

import argparse
import csv
import json
import os
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global state
CONFIG = {}
STIMULI = []
RATINGS_DIR = Path("results/human_ratings")


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def load_stimuli(config: dict) -> list[dict]:
    """Load stimulus manifest and prepare evaluation order."""
    manifest_path = Path(config["generation"]["output_dir"]) / "stimulus_manifest.csv"
    if not manifest_path.exists():
        print(f"WARN: Stimulus manifest not found: {manifest_path}")
        return []

    with open(manifest_path) as f:
        stimuli = list(csv.DictReader(f))

    # Filter to existing videos
    return [s for s in stimuli if Path(s["output_video"]).exists()]


def create_attention_checks(config: dict) -> list[dict]:
    """Create attention check stimuli (clearly bad videos)."""
    ref_dir = Path(config["generation"]["reference_dir"])
    checks = []
    for f in ref_dir.glob("attention_*.mp4"):
        checks.append({
            "identity": "attention_check",
            "emotion": "neutral",
            "sentence_id": f.stem,
            "vc_system": "attention_check",
            "lipsync_system": "attention_check",
            "output_video": str(f),
            "is_attention_check": True,
        })
    return checks


def assign_stimuli_to_participant(stimuli: list, config: dict) -> list:
    """Assign a subset of stimuli to a participant (counterbalanced)."""
    n_identities = config["human_eval"]["identities_per_participant"]

    # Get all unique identities
    identities = list(set(s["identity"] for s in stimuli if s.get("identity") != "attention_check"))

    if len(identities) <= n_identities:
        selected_identities = identities
    else:
        selected_identities = random.sample(identities, n_identities)

    # Filter stimuli to selected identities
    assigned = [s for s in stimuli if s["identity"] in selected_identities]

    # Add attention checks
    attention = [s for s in stimuli if s.get("is_attention_check")]
    assigned.extend(attention)

    # Randomize order
    random.shuffle(assigned)

    return assigned


@app.route("/")
def index():
    return render_template("eval.html")


@app.route("/api/start", methods=["POST"])
def start_session():
    """Initialize a new evaluation session."""
    data = request.json or {}
    participant_id = str(uuid.uuid4())[:8]

    assigned = assign_stimuli_to_participant(STIMULI, CONFIG)

    session["participant_id"] = participant_id
    session["stimuli"] = assigned
    session["current_index"] = 0
    session["start_time"] = time.time()
    session["demographics"] = data.get("demographics", {})

    return jsonify({
        "participant_id": participant_id,
        "total_stimuli": len(assigned),
    })


@app.route("/api/next", methods=["GET"])
def next_stimulus():
    """Get the next stimulus to rate."""
    idx = session.get("current_index", 0)
    stimuli = session.get("stimuli", [])

    if idx >= len(stimuli):
        return jsonify({"done": True, "message": "All stimuli rated. Thank you!"})

    stim = stimuli[idx]
    # Serve video path relative to static
    video_url = f"/video?path={stim['output_video']}"

    return jsonify({
        "done": False,
        "index": idx,
        "total": len(stimuli),
        "video_url": video_url,
        "stimulus_id": f"{stim.get('vc_system', 'unknown')}_{stim.get('lipsync_system', 'unknown')}_{stim.get('identity', 'unknown')}_{stim.get('emotion', 'unknown')}_{stim.get('sentence_id', 'unknown')}",
    })


@app.route("/video")
def serve_video():
    """Serve a video file."""
    from flask import send_file
    path = request.args.get("path", "")
    if Path(path).exists():
        return send_file(path, mimetype="video/mp4")
    return "Video not found", 404


@app.route("/api/rate", methods=["POST"])
def submit_rating():
    """Submit rating for current stimulus."""
    data = request.json
    idx = session.get("current_index", 0)
    stimuli = session.get("stimuli", [])

    if idx >= len(stimuli):
        return jsonify({"error": "No more stimuli"}), 400

    stim = stimuli[idx]

    rating = {
        "participant_id": session.get("participant_id"),
        "timestamp": datetime.now().isoformat(),
        "stimulus_index": idx,
        "identity": stim.get("identity"),
        "emotion": stim.get("emotion"),
        "sentence_id": stim.get("sentence_id"),
        "vc_system": stim.get("vc_system"),
        "lipsync_system": stim.get("lipsync_system"),
        "is_attention_check": stim.get("is_attention_check", False),
        "overall_quality": data.get("overall_quality"),
        "lip_sync": data.get("lip_sync"),
        "voice_naturalness": data.get("voice_naturalness"),
        "visual_naturalness": data.get("visual_naturalness"),
        "response_time_ms": data.get("response_time_ms"),
    }

    # Save rating
    _save_rating(rating)

    session["current_index"] = idx + 1

    return jsonify({"success": True, "remaining": len(stimuli) - idx - 1})


def _save_rating(rating: dict):
    """Append a rating to the participant's file."""
    RATINGS_DIR.mkdir(parents=True, exist_ok=True)
    pid = rating["participant_id"]
    filepath = RATINGS_DIR / f"{pid}.jsonl"
    with open(filepath, "a") as f:
        f.write(json.dumps(rating) + "\n")


@app.route("/api/export", methods=["GET"])
def export_ratings():
    """Export all ratings as a single CSV."""
    all_ratings = []
    for f in RATINGS_DIR.glob("*.jsonl"):
        with open(f) as fh:
            for line in fh:
                all_ratings.append(json.loads(line))

    if not all_ratings:
        return jsonify({"error": "No ratings collected yet"}), 404

    # Save as CSV
    csv_path = Path("results") / "human_ratings.csv"
    keys = all_ratings[0].keys()
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_ratings)

    return jsonify({
        "exported": len(all_ratings),
        "path": str(csv_path),
        "participants": len(list(RATINGS_DIR.glob("*.jsonl"))),
    })


def main():
    parser = argparse.ArgumentParser(description="Human evaluation web app")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--demo", action="store_true", help="Use demo data")
    args = parser.parse_args()

    global CONFIG, STIMULI
    CONFIG = load_config()
    STIMULI = load_stimuli(CONFIG)

    if args.demo and not STIMULI:
        # Create minimal demo stimuli
        print("Creating demo stimuli list...")
        STIMULI = [
            {
                "identity": f"demo_{i}",
                "emotion": "neutral" if i % 2 == 0 else "emotional",
                "sentence_id": "s01",
                "vc_system": f"vc_{i % 4}",
                "lipsync_system": f"ls_{i % 4}",
                "output_video": "data/source/demo_neutral_s01.mp4",
            }
            for i in range(32)
        ]

    print(f"\n{'=' * 60}")
    print(f"Human Evaluation Server")
    print(f"{'=' * 60}")
    print(f"Stimuli loaded: {len(STIMULI)}")
    print(f"Server: http://localhost:{args.port}")
    print(f"Export endpoint: http://localhost:{args.port}/api/export")
    print(f"{'=' * 60}\n")

    app.run(host="0.0.0.0", port=args.port, debug=True)


if __name__ == "__main__":
    main()
