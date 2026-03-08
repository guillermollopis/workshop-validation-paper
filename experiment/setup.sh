#!/bin/bash
# ============================================================
# Setup script: install all dependencies for the experiment
# Run: bash setup.sh
# ============================================================
set -e

echo "============================================================"
echo "Setting up Voice Cloning × Lipsync Benchmark"
echo "============================================================"

# --- Python packages ---
echo ""
echo "[1/5] Installing Python packages..."
pip install --quiet \
    pyyaml \
    pandas \
    matplotlib \
    seaborn \
    scipy \
    scikit-learn \
    statsmodels \
    librosa \
    soundfile \
    opencv-python-headless \
    flask \
    tqdm \
    Pillow \
    pymer4 2>/dev/null || true

# --- VC system packages ---
echo ""
echo "[2/5] Installing Voice Cloning packages..."
pip install --quiet TTS 2>/dev/null || echo "  [WARN] TTS (XTTS-v2) install failed — install manually: pip install TTS"
pip install --quiet whisperspeech 2>/dev/null || echo "  [WARN] WhisperSpeech install failed — install manually"
pip install --quiet outetts 2>/dev/null || echo "  [WARN] OuteTTS install failed — install manually"
# kNN-VC uses torch.hub (bshall/knn-vc) — downloaded automatically on first use

# --- Metrics packages ---
echo ""
echo "[3/5] Installing metrics packages..."
pip install --quiet \
    openai-whisper 2>/dev/null || pip install --quiet whisper 2>/dev/null || echo "  [WARN] Whisper install failed"
pip install --quiet dlib 2>/dev/null || echo "  [WARN] dlib install failed — needed for LMD metric"
pip install --quiet pytorch-fid 2>/dev/null || echo "  [WARN] pytorch-fid install failed"

# --- Lipsync repos (clone if not present) ---
echo ""
echo "[4/5] Cloning lipsync repositories..."
TOOLS_DIR="tools/repos"
mkdir -p "$TOOLS_DIR"

if [ ! -d "$TOOLS_DIR/Wav2Lip" ]; then
    git clone --depth 1 https://github.com/Rudrabha/Wav2Lip.git "$TOOLS_DIR/Wav2Lip" 2>/dev/null || echo "  [WARN] Wav2Lip clone failed"
fi

if [ ! -d "$TOOLS_DIR/SadTalker" ]; then
    git clone --depth 1 https://github.com/OpenTalker/SadTalker.git "$TOOLS_DIR/SadTalker" 2>/dev/null || echo "  [WARN] SadTalker clone failed"
fi

if [ ! -d "$TOOLS_DIR/video-retalking" ]; then
    git clone --depth 1 https://github.com/OpenTalker/video-retalking.git "$TOOLS_DIR/video-retalking" 2>/dev/null || echo "  [WARN] VideoReTalking clone failed"
fi

if [ ! -d "$TOOLS_DIR/MuseTalk" ]; then
    git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git "$TOOLS_DIR/MuseTalk" 2>/dev/null || echo "  [WARN] MuseTalk clone failed"
fi

# --- Directory structure ---
echo ""
echo "[5/5] Creating directory structure..."
mkdir -p data/{source,vc_output,generated,reference}
mkdir -p results
mkdir -p figures
mkdir -p templates

echo ""
echo "============================================================"
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  1. Download MEAD dataset (or place custom videos in data/source/)"
echo "     python3 01_prepare_data.py --help"
echo "  2. Download lipsync model checkpoints:"
echo "     - Wav2Lip: download wav2lip_gan.pth to tools/repos/Wav2Lip/checkpoints/"
echo "     - SadTalker: cd tools/repos/SadTalker && bash scripts/download_models.sh"
echo "     - VideoReTalking: follow tools/repos/video-retalking/README.md"
echo "     - MuseTalk: follow tools/repos/MuseTalk/README.md"
echo "  3. Run the pipeline:"
echo "     python3 01_prepare_data.py"
echo "     python3 02_generate_vc.py"
echo "     python3 03_generate_lipsync.py"
echo "     python3 04_compute_metrics.py"
echo "     python3 05_run_analysis.py"
echo "============================================================"
