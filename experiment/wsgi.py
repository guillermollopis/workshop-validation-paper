"""WSGI entry point for gunicorn / Railway.

Environment variables:
  TRIALS_PER_COND  — trials per condition (default: 4 for pilot, use 8 for real)
  NO_FEEDBACK      — set to "1" to disable feedback (real experiment mode)
  DESIGN           — experiment design: "2afc" (default) or "mixed"
  CURATED_DIR      — path to curated videos (default: data/curated) for 2afc design
  NORMALIZED_DIR   — path to video directory (default: data/normalized) for mixed design
  ADMIN_KEY        — password for /admin panel (default: pilot2026)
  RESULTS_DIR      — where to save results JSON (default: results/4afc_tests)
  SESSION_DIR      — server-side session storage (default: /tmp)
  SECRET_KEY       — Flask secret key (auto-generated if not set)
  PROLIFIC_URL     — Prolific completion redirect URL (optional)
"""
import importlib
import os

# Configure via environment variables
TRIALS_PER_COND = int(os.environ.get("TRIALS_PER_COND", "8"))
NO_FEEDBACK = os.environ.get("NO_FEEDBACK", "").lower() in ("1", "true", "yes")
DESIGN = os.environ.get("DESIGN", "mixed")
CURATED_DIR = os.environ.get("CURATED_DIR", "data/curated")
NORMALIZED_DIR = os.environ.get("NORMALIZED_DIR", "data/normalized")
PROLIFIC_URL = os.environ.get("PROLIFIC_URL", None)

# Import the module (filename starts with a number, so use importlib)
mod = importlib.import_module("08_4afc_experiment")
app = mod.app

import sys
print(f"[wsgi] Starting init_trials: design={DESIGN}, curated={CURATED_DIR}, "
      f"normalized={NORMALIZED_DIR}, trials={TRIALS_PER_COND}, no_feedback={NO_FEEDBACK}", flush=True)

try:
    mod.init_trials(
        normalized_dir=NORMALIZED_DIR,
        trials_per_cond=TRIALS_PER_COND,
        no_feedback=NO_FEEDBACK,
        prolific_url=PROLIFIC_URL,
        skip_checks=True,
        design=DESIGN,
        curated_dir=CURATED_DIR,
    )
    print(f"[wsgi] init_trials OK, {len(mod.TRIALS)} trials loaded", flush=True)
except Exception as e:
    print(f"[wsgi] FATAL: init_trials failed: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc()

# Health check that bypasses sessions
@app.route("/health")
def health():
    return f"ok - {len(mod.TRIALS)} trials loaded"
