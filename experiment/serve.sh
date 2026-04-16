#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
#  Serve the experiment with gunicorn (production server)
# ──────────────────────────────────────────────────────────
#
#  Pilot testing (feedback ON, 4 trials/condition = 32 total):
#    ./serve.sh
#
#  Real experiment (feedback OFF, 8 trials/condition = 64 total):
#    ./serve.sh --no-feedback --trials 8
#
#  Custom port:
#    ./serve.sh --port 8080
#
#  Then share: http://<your-ip>:<port>

set -euo pipefail
cd "$(dirname "$0")"

PORT=5001
TRIALS=8
NO_FEEDBACK="1"
DESIGN="mixed"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)       PORT="$2"; shift 2 ;;
        --trials)     TRIALS="$2"; shift 2 ;;
        --no-feedback) NO_FEEDBACK=1; shift ;;
        --design)     DESIGN="$2"; shift 2 ;;
        -h|--help)
            head -15 "$0" | tail -12
            exit 0 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [ "$DESIGN" = "2afc" ]; then
    TOTAL=$((TRIALS * 4))
else
    TOTAL=$((TRIALS * 8))
fi
MODE="PILOT (feedback ON)"
[ -n "$NO_FEEDBACK" ] && MODE="EXPERIMENT (feedback OFF)"

# Get local IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   Deepfake Detection Experiment          ║"
echo "  ╠══════════════════════════════════════════╣"
CONDS=4; [ "$DESIGN" = "mixed" ] && CONDS=8
echo "  ║  Mode:   $MODE"
echo "  ║  Design: $DESIGN"
echo "  ║  Trials: $TOTAL ($TRIALS per condition × $CONDS)"
echo "  ║  Port:   $PORT"
echo "  ║                                          ║"
echo "  ║  Share this link with colleagues:        ║"
echo "  ║  http://$LOCAL_IP:$PORT"
echo "  ╚══════════════════════════════════════════╝"
echo ""

export TRIALS_PER_COND="$TRIALS"
export NO_FEEDBACK="${NO_FEEDBACK:-}"
export DESIGN="$DESIGN"
export CURATED_DIR="data/curated"
export NORMALIZED_DIR="data/normalized"

exec gunicorn wsgi:app \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --preload
