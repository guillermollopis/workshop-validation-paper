#!/usr/bin/env python3
"""
Stimulus Screening Tool — manually curate generated videos.

Shows each generated video alongside its source (real) video.
Rate each as: KEEP / REJECT / MAYBE
Exports a filtered stimulus set for the experiment.

Usage:
  python3 09_screen_stimuli.py                    # screen all generated videos
  python3 09_screen_stimuli.py --port 5002
  python3 09_screen_stimuli.py --resume            # resume from where you left off
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template_string

app = Flask(__name__)
app.secret_key = os.urandom(24)

STIMULI = []
SCREENING_FILE = Path("results/screening.json")

# ── Discover stimuli ──────────────────────────────────────────

def discover_stimuli(normalized_dir: str) -> list[dict]:
    ndir = Path(normalized_dir)
    source_dir = ndir / "source"
    stimuli = []

    # Build source lookup: {filename: path}
    sources = {}
    if source_dir.exists():
        for mp4 in source_dir.glob("*.mp4"):
            sources[mp4.name] = str(mp4.resolve())

    # Find all generated videos
    for vc_dir in sorted(ndir.iterdir()):
        if not vc_dir.is_dir() or vc_dir.name == "source":
            continue
        for ls_dir in sorted(vc_dir.iterdir()):
            if not ls_dir.is_dir():
                continue
            pipeline = f"{vc_dir.name}/{ls_dir.name}"
            for mp4 in sorted(ls_dir.glob("*.mp4")):
                parts = mp4.stem.split("_")
                source_path = sources.get(mp4.name, "")
                stimuli.append({
                    "id": f"{pipeline}/{mp4.stem}",
                    "path": str(mp4.resolve()),
                    "source_path": source_path,
                    "pipeline": pipeline,
                    "vc_system": vc_dir.name,
                    "lipsync_system": ls_dir.name,
                    "identity": parts[0] if len(parts) >= 1 else "unknown",
                    "emotion": parts[1] if len(parts) >= 2 else "unknown",
                    "clip_id": parts[2] if len(parts) >= 3 else "unknown",
                    "filename": mp4.name,
                })
    return stimuli


def load_screening() -> dict:
    if SCREENING_FILE.exists():
        return json.loads(SCREENING_FILE.read_text())
    return {"ratings": {}, "started": datetime.now().isoformat()}


def save_screening(data: dict):
    SCREENING_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    SCREENING_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── HTML ──────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stimulus Screening</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, sans-serif; background: #0f0f1a; color: #eee;
       min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
h1 { text-align: center; margin: 10px 0; font-size: 24px;
     background: linear-gradient(135deg, #4a90d9, #64ffda);
     -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* Progress */
.progress-bar { background: #222; border-radius: 10px; height: 8px; margin: 12px 0; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 10px; transition: width 0.3s; }
.progress-fill.good { background: linear-gradient(90deg, #4a90d9, #64ffda); }
.stats { display: flex; gap: 20px; justify-content: center; margin: 10px 0; font-size: 13px; }
.stat { color: #888; }
.stat strong { color: #eee; }
.stat.keep strong { color: #64ffda; }
.stat.reject strong { color: #ff6b6b; }
.stat.maybe strong { color: #f0c040; }

/* Video pair */
.video-pair { display: flex; gap: 20px; justify-content: center; margin: 16px 0; }
.video-box { flex: 1; max-width: 520px; }
.video-label { text-align: center; font-size: 16px; font-weight: 700; margin-bottom: 6px;
               letter-spacing: 1px; }
.video-label.source { color: #64ffda; }
.video-label.generated { color: #ff9f43; }
.video-wrap { background: #000; border-radius: 10px; overflow: hidden;
              border: 3px solid #222; }
video { width: 100%; display: block; }

/* Info bar */
.info { text-align: center; margin: 8px 0; }
.info-tag { display: inline-block; background: #1a1a2e; padding: 4px 14px;
            border-radius: 20px; font-size: 12px; color: #888; margin: 3px; }
.info-tag strong { color: #ccc; }

/* Controls */
.controls { display: flex; gap: 16px; justify-content: center; margin: 20px 0; }
.rate-btn { padding: 16px 40px; border: 3px solid #333; border-radius: 12px;
            background: #12122a; cursor: pointer; font-size: 18px; font-weight: 700;
            transition: all 0.15s; min-width: 140px; text-align: center; }
.rate-btn:hover { transform: scale(1.04); }
.rate-btn.keep { color: #64ffda; }
.rate-btn.keep:hover, .rate-btn.keep.active { border-color: #64ffda; background: #0f2a2a; }
.rate-btn.reject { color: #ff6b6b; }
.rate-btn.reject:hover, .rate-btn.reject.active { border-color: #ff6b6b; background: #2a0f0f; }
.rate-btn.maybe { color: #f0c040; }
.rate-btn.maybe:hover, .rate-btn.maybe.active { border-color: #f0c040; background: #2a2a0f; }

.nav-row { display: flex; gap: 12px; justify-content: center; margin: 10px 0; }
.nav-btn { padding: 8px 24px; border: 2px solid #333; border-radius: 8px;
           background: #16213e; color: #aaa; cursor: pointer; font-size: 14px; }
.nav-btn:hover { border-color: #4a90d9; color: #fff; }

/* Playback */
.play-row { display: flex; gap: 10px; justify-content: center; margin: 10px 0; }
.play-btn { padding: 8px 20px; border: 2px solid #333; border-radius: 8px;
            background: #16213e; color: #aaa; cursor: pointer; font-size: 13px; }
.play-btn:hover { border-color: #4a90d9; color: #fff; }

/* Summary */
#summary { display: none; text-align: center; padding-top: 40px; }
.summary-stat { display: inline-block; background: #1a1a2e; padding: 20px 30px;
                border-radius: 12px; margin: 10px; text-align: center; }
.summary-num { font-size: 48px; font-weight: 800; }
.summary-label { font-size: 13px; color: #888; margin-top: 4px; }
.export-btn { padding: 14px 50px; border: none; border-radius: 8px;
              background: linear-gradient(135deg, #4a90d9, #64ffda); color: #0f0f1a;
              font-size: 17px; font-weight: 700; cursor: pointer; margin-top: 24px; }

/* Keyboard hints */
.keys { text-align: center; color: #444; font-size: 12px; margin: 8px 0; }
kbd { background: #1a1a2e; border: 1px solid #333; border-radius: 4px;
      padding: 2px 8px; font-size: 12px; color: #888; }

/* Filter tabs */
.filter-tabs { display: flex; gap: 8px; justify-content: center; margin: 12px 0; }
.filter-tab { padding: 6px 16px; border: 2px solid #333; border-radius: 20px;
              background: #12122a; color: #666; cursor: pointer; font-size: 12px; }
.filter-tab:hover { border-color: #4a90d9; }
.filter-tab.active { border-color: #4a90d9; color: #fff; background: #1a2a4e; }
</style>
</head>
<body>
<div class="container">
<h1>Stimulus Screening</h1>

<div class="progress-bar"><div class="progress-fill good" id="pbar"></div></div>
<div class="stats">
    <div class="stat" id="stat-progress">0 / 0</div>
    <div class="stat keep" id="stat-keep">Keep: <strong>0</strong></div>
    <div class="stat reject" id="stat-reject">Reject: <strong>0</strong></div>
    <div class="stat maybe" id="stat-maybe">Maybe: <strong>0</strong></div>
</div>

<div class="filter-tabs">
    <div class="filter-tab active" data-filter="all" onclick="setFilter('all')">All</div>
    <div class="filter-tab" data-filter="unrated" onclick="setFilter('unrated')">Unrated</div>
    <div class="filter-tab" data-filter="keep" onclick="setFilter('keep')">Keep</div>
    <div class="filter-tab" data-filter="reject" onclick="setFilter('reject')">Reject</div>
    <div class="filter-tab" data-filter="maybe" onclick="setFilter('maybe')">Maybe</div>
</div>

<div id="screening">
    <div class="info" id="info"></div>

    <div class="video-pair">
        <div class="video-box">
            <div class="video-label source">SOURCE (real)</div>
            <div class="video-wrap"><video id="vid-source" controls preload="auto"></video></div>
        </div>
        <div class="video-box">
            <div class="video-label generated">GENERATED</div>
            <div class="video-wrap"><video id="vid-gen" controls preload="auto"></video></div>
        </div>
    </div>

    <div class="play-row">
        <button class="play-btn" onclick="playBoth()">&#9654; Play both</button>
        <button class="play-btn" onclick="loopBoth()">&#128257; Loop both</button>
        <button class="play-btn" onclick="stopBoth()">&#9632; Stop</button>
    </div>

    <div class="controls">
        <div class="rate-btn keep" onclick="rate('keep')">&#10003; KEEP</div>
        <div class="rate-btn maybe" onclick="rate('maybe')">? MAYBE</div>
        <div class="rate-btn reject" onclick="rate('reject')">&#10007; REJECT</div>
    </div>

    <div class="keys">
        Keyboard: <kbd>1</kbd> Keep &nbsp; <kbd>2</kbd> Maybe &nbsp; <kbd>3</kbd> Reject &nbsp;
        <kbd>&larr;</kbd> Prev &nbsp; <kbd>&rarr;</kbd> Next &nbsp; <kbd>Space</kbd> Play both
    </div>

    <div class="nav-row">
        <button class="nav-btn" onclick="go(-1)">&larr; Previous</button>
        <button class="nav-btn" onclick="go(1)">Next &rarr;</button>
        <button class="nav-btn" onclick="showSummary()">Finish &amp; Export</button>
    </div>
</div>

<div id="summary">
    <h2 style="color:#64ffda; margin-bottom:20px;">Screening Complete</h2>
    <div id="summary-stats"></div>
    <div id="summary-pipelines"></div>
    <button class="export-btn" onclick="exportResults()">Download screening.json</button>
    <p style="color:#555; margin-top:16px; font-size:13px;">
        Results also auto-saved to results/screening.json</p>
</div>

</div>

<script>
let S = { stimuli: [], ratings: {}, idx: 0, filter: 'all', filtered: [] };

async function init() {
    const r = await fetch('/api/stimuli');
    const d = await r.json();
    S.stimuli = d.stimuli;
    S.ratings = d.ratings || {};
    applyFilter();
    show();
}

function applyFilter() {
    if (S.filter === 'all') {
        S.filtered = S.stimuli.map((_, i) => i);
    } else if (S.filter === 'unrated') {
        S.filtered = S.stimuli.map((s, i) => !S.ratings[s.id] ? i : -1).filter(i => i >= 0);
    } else {
        S.filtered = S.stimuli.map((s, i) => S.ratings[s.id] === S.filter ? i : -1).filter(i => i >= 0);
    }
    if (S.idx >= S.filtered.length) S.idx = Math.max(0, S.filtered.length - 1);
}

function setFilter(f) {
    S.filter = f;
    document.querySelectorAll('.filter-tab').forEach(t =>
        t.classList.toggle('active', t.dataset.filter === f));
    applyFilter();
    S.idx = 0;
    show();
}

function show() {
    updateStats();
    if (S.filtered.length === 0) {
        document.getElementById('info').innerHTML =
            '<p style="color:#666; margin:40px;">No videos match this filter.</p>';
        return;
    }

    const realIdx = S.filtered[S.idx];
    const s = S.stimuli[realIdx];
    const rating = S.ratings[s.id] || null;

    // Info
    document.getElementById('info').innerHTML =
        `<span class="info-tag"><strong>${s.identity}</strong></span>` +
        `<span class="info-tag">${s.emotion}</span>` +
        `<span class="info-tag">${s.clip_id}</span>` +
        `<span class="info-tag"><strong>${s.pipeline}</strong></span>` +
        `<span class="info-tag">${S.idx + 1} / ${S.filtered.length}</span>`;

    // Videos
    const vidS = document.getElementById('vid-source');
    const vidG = document.getElementById('vid-gen');
    vidS.src = '/video?path=' + encodeURIComponent(s.source_path);
    vidG.src = '/video?path=' + encodeURIComponent(s.path);
    vidS.load(); vidG.load();

    // Highlight current rating
    document.querySelectorAll('.rate-btn').forEach(b => b.classList.remove('active'));
    if (rating) {
        document.querySelector(`.rate-btn.${rating}`)?.classList.add('active');
    }
}

function updateStats() {
    const total = S.stimuli.length;
    const rated = Object.keys(S.ratings).length;
    const keep = Object.values(S.ratings).filter(r => r === 'keep').length;
    const reject = Object.values(S.ratings).filter(r => r === 'reject').length;
    const maybe = Object.values(S.ratings).filter(r => r === 'maybe').length;

    document.getElementById('pbar').style.width = (rated / total * 100) + '%';
    document.getElementById('stat-progress').textContent = `${rated} / ${total} rated`;
    document.getElementById('stat-keep').innerHTML = `Keep: <strong>${keep}</strong>`;
    document.getElementById('stat-reject').innerHTML = `Reject: <strong>${reject}</strong>`;
    document.getElementById('stat-maybe').innerHTML = `Maybe: <strong>${maybe}</strong>`;
}

async function rate(r) {
    if (S.filtered.length === 0) return;
    const realIdx = S.filtered[S.idx];
    const s = S.stimuli[realIdx];
    S.ratings[s.id] = r;

    // Highlight
    document.querySelectorAll('.rate-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.rate-btn.${r}`)?.classList.add('active');

    // Save
    await fetch('/api/rate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: s.id, rating: r}),
    });

    updateStats();

    // Auto-advance after short delay
    setTimeout(() => {
        if (S.idx < S.filtered.length - 1) {
            S.idx++;
            show();
        }
    }, 300);
}

function go(delta) {
    const newIdx = S.idx + delta;
    if (newIdx >= 0 && newIdx < S.filtered.length) {
        S.idx = newIdx;
        show();
    }
}

function playBoth() {
    const vs = document.getElementById('vid-source');
    const vg = document.getElementById('vid-gen');
    vs.currentTime = 0; vg.currentTime = 0;
    vs.play(); vg.play();
}

function loopBoth() {
    const vs = document.getElementById('vid-source');
    const vg = document.getElementById('vid-gen');
    vs.loop = true; vg.loop = true;
    vs.currentTime = 0; vg.currentTime = 0;
    vs.play(); vg.play();
}

function stopBoth() {
    const vs = document.getElementById('vid-source');
    const vg = document.getElementById('vid-gen');
    vs.pause(); vg.pause();
    vs.loop = false; vg.loop = false;
}

function showSummary() {
    document.getElementById('screening').style.display = 'none';
    document.getElementById('summary').style.display = 'block';

    const keep = Object.values(S.ratings).filter(r => r === 'keep').length;
    const reject = Object.values(S.ratings).filter(r => r === 'reject').length;
    const maybe = Object.values(S.ratings).filter(r => r === 'maybe').length;
    const unrated = S.stimuli.length - Object.keys(S.ratings).length;

    document.getElementById('summary-stats').innerHTML =
        `<div class="summary-stat"><div class="summary-num" style="color:#64ffda">${keep}</div><div class="summary-label">Keep</div></div>` +
        `<div class="summary-stat"><div class="summary-num" style="color:#f0c040">${maybe}</div><div class="summary-label">Maybe</div></div>` +
        `<div class="summary-stat"><div class="summary-num" style="color:#ff6b6b">${reject}</div><div class="summary-label">Reject</div></div>` +
        `<div class="summary-stat"><div class="summary-num" style="color:#666">${unrated}</div><div class="summary-label">Unrated</div></div>`;

    // By pipeline
    const byPipeline = {};
    for (const s of S.stimuli) {
        if (!byPipeline[s.pipeline]) byPipeline[s.pipeline] = {keep:0, reject:0, maybe:0, total:0};
        byPipeline[s.pipeline].total++;
        const r = S.ratings[s.id];
        if (r) byPipeline[s.pipeline][r]++;
    }
    let html = '<h3 style="color:#64ffda; margin:20px 0 10px;">By Pipeline</h3>';
    html += '<table style="width:100%;max-width:600px;margin:0 auto;border-collapse:collapse;">';
    html += '<tr><th style="text-align:left;padding:8px;border-bottom:2px solid #333;color:#888;">Pipeline</th>' +
            '<th style="padding:8px;border-bottom:2px solid #333;color:#64ffda;">Keep</th>' +
            '<th style="padding:8px;border-bottom:2px solid #333;color:#f0c040;">Maybe</th>' +
            '<th style="padding:8px;border-bottom:2px solid #333;color:#ff6b6b;">Reject</th>' +
            '<th style="padding:8px;border-bottom:2px solid #333;color:#888;">Total</th></tr>';
    for (const [p, c] of Object.entries(byPipeline).sort()) {
        html += `<tr><td style="padding:6px 8px;border-bottom:1px solid #1a1a2e;">${p}</td>` +
                `<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #1a1a2e;color:#64ffda;">${c.keep}</td>` +
                `<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #1a1a2e;color:#f0c040;">${c.maybe}</td>` +
                `<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #1a1a2e;color:#ff6b6b;">${c.reject}</td>` +
                `<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #1a1a2e;color:#888;">${c.total}</td></tr>`;
    }
    html += '</table>';
    document.getElementById('summary-pipelines').innerHTML = html;
}

function exportResults() {
    const data = JSON.stringify({ratings: S.ratings, stimuli: S.stimuli}, null, 2);
    const blob = new Blob([data], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'screening.json';
    a.click();
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === '1') rate('keep');
    else if (e.key === '2') rate('maybe');
    else if (e.key === '3') rate('reject');
    else if (e.key === 'ArrowLeft') go(-1);
    else if (e.key === 'ArrowRight') go(1);
    else if (e.key === ' ') { e.preventDefault(); playBoth(); }
});

init();
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/video")
def serve_video():
    path = request.args.get("path", "")
    if not path:
        return "Not found", 404
    resolved = Path(path).resolve()
    allowed = Path(__file__).resolve().parent / "data"
    if not str(resolved).startswith(str(allowed)):
        return "Forbidden", 403
    if not resolved.exists() or not resolved.is_file():
        return "Not found", 404
    return send_file(str(resolved), mimetype="video/mp4")


@app.route("/api/stimuli")
def api_stimuli():
    screening = load_screening()
    return jsonify({
        "stimuli": STIMULI,
        "ratings": screening.get("ratings", {}),
    })


@app.route("/api/rate", methods=["POST"])
def api_rate():
    data = request.json
    screening = load_screening()
    screening["ratings"][data["id"]] = data["rating"]
    save_screening(screening)
    return jsonify({"ok": True})


def main():
    parser = argparse.ArgumentParser(description="Stimulus Screening Tool")
    parser.add_argument("--port", type=int, default=5002)
    parser.add_argument("--normalized-dir", default="data/normalized")
    args = parser.parse_args()

    import random
    global STIMULI
    STIMULI = discover_stimuli(args.normalized_dir)
    random.seed(12345)  # fixed seed so order is consistent across restarts
    random.shuffle(STIMULI)

    print(f"Found {len(STIMULI)} generated videos to screen")
    pipelines = {}
    for s in STIMULI:
        pipelines[s["pipeline"]] = pipelines.get(s["pipeline"], 0) + 1
    for p, n in sorted(pipelines.items()):
        print(f"  {p}: {n}")

    if SCREENING_FILE.exists():
        screening = load_screening()
        rated = len(screening.get("ratings", {}))
        print(f"\nResuming: {rated}/{len(STIMULI)} already rated")

    print(f"\n  http://localhost:{args.port}")
    print(f"  Keyboard: 1=Keep, 2=Maybe, 3=Reject, Space=Play, Arrows=Navigate\n")

    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
