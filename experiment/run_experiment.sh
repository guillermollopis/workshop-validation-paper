#!/usr/bin/env bash
# ============================================================
# run_experiment.sh — Master script for the VC × Lipsync
# factorial benchmark experiment.
#
# Phases:
#   0  Install dependencies, clone repos, download checkpoints
#   1  Prepare source data (split clips, face-crop)
#   2  Generate voice-cloned audio
#   3  Generate lipsync videos
#   4  Compute computational metrics
#   5  Run statistical analysis
#
# Usage:
#   bash run_experiment.sh               # full run from phase 0
#   bash run_experiment.sh --phase 2     # resume from phase 2
#   bash run_experiment.sh --dry-run     # preview what each phase does
#   bash run_experiment.sh --skip-install # skip phase 0
# ============================================================

set -euo pipefail

# ---------- Defaults ----------
START_PHASE=0
DRY_RUN=false
SKIP_INSTALL=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/experiment_${TIMESTAMP}.log"
REPOS_DIR="${SCRIPT_DIR}/tools/repos"
MODELS_DIR="${SCRIPT_DIR}/tools/models"

# ---------- Parse arguments ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --phase)
            START_PHASE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        -h|--help)
            head -24 "$0" | tail -20
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# ---------- Logging ----------
mkdir -p "$LOG_DIR"

log() {
    local msg="[$(date '+%H:%M:%S')] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

run() {
    # Run a command, logging stdout+stderr
    log "CMD: $*"
    if $DRY_RUN; then
        log "[DRY RUN] Would execute: $*"
        return 0
    fi
    "$@" 2>&1 | tee -a "$LOG_FILE"
    return "${PIPESTATUS[0]}"
}

phase_banner() {
    local phase_num="$1"
    local phase_name="$2"
    log ""
    log "============================================================"
    log "  PHASE ${phase_num}: ${phase_name}"
    log "============================================================"
    log ""
}

check_gpu() {
    if command -v nvidia-smi &>/dev/null; then
        log "GPU detected:"
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1 | tee -a "$LOG_FILE"
        return 0
    else
        log "[WARN] No NVIDIA GPU detected. Some tools may be slow or fail."
        return 1
    fi
}

# ---------- PHASE 0: Install dependencies ----------
phase_0() {
    phase_banner 0 "Install dependencies, clone repos, download checkpoints"

    if $SKIP_INSTALL; then
        log "Skipping Phase 0 (--skip-install)"
        return 0
    fi

    # -- GPU check --
    check_gpu || true

    # -- Python packages --
    log "Installing Python packages..."
    run pip install --quiet \
        coqui-tts \
        transformers \
        torch torchaudio torchvision \
        soundfile librosa \
        opencv-python-headless \
        mediapipe \
        scikit-learn scikit-image \
        scipy \
        pandas matplotlib seaborn \
        flask \
        pyyaml \
        openai-whisper \
        gdown \
        pytorch-fid \
        dlib \
        huggingface_hub \
        2>&1 || log "[WARN] Some pip packages may have failed"

    # -- Clone repositories --
    mkdir -p "$REPOS_DIR"

    clone_if_missing() {
        local url="$1"
        local dir="$2"
        if [ -d "$dir/.git" ]; then
            log "Repo already cloned: $dir"
        else
            log "Cloning $url -> $dir"
            run git clone --depth 1 "$url" "$dir"
        fi
    }

    clone_if_missing "https://github.com/Rudrabha/Wav2Lip.git" \
                     "${REPOS_DIR}/Wav2Lip"

    clone_if_missing "https://github.com/OpenTalker/SadTalker.git" \
                     "${REPOS_DIR}/SadTalker"

    clone_if_missing "https://github.com/OpenTalker/video-retalking.git" \
                     "${REPOS_DIR}/video-retalking"

    clone_if_missing "https://github.com/TMElyralab/MuseTalk.git" \
                     "${REPOS_DIR}/MuseTalk"

    # CosyVoice (VC system — zero-shot TTS with Spanish support)
    clone_if_missing "https://github.com/FunAudioLLM/CosyVoice.git" \
                     "${REPOS_DIR}/CosyVoice"
    # Install CosyVoice dependencies
    if [ -f "${REPOS_DIR}/CosyVoice/requirements.txt" ]; then
        log "Installing CosyVoice dependencies..."
        run pip install --quiet -r "${REPOS_DIR}/CosyVoice/requirements.txt" \
            2>&1 || log "[WARN] Some CosyVoice deps may have failed"
    fi

    # -- Download checkpoints --
    mkdir -p "$MODELS_DIR"

    # Wav2Lip checkpoints
    local wav2lip_ckpt="${REPOS_DIR}/Wav2Lip/checkpoints"
    mkdir -p "$wav2lip_ckpt"
    if [ ! -f "${wav2lip_ckpt}/wav2lip_gan.pth" ]; then
        log "Downloading Wav2Lip GAN checkpoint..."
        run gdown "https://drive.google.com/uc?id=1qjTMiIgYCnQdUA2zRV0iA-FZGCr3SbKr" \
            -O "${wav2lip_ckpt}/wav2lip_gan.pth" \
            2>&1 || log "[WARN] Wav2Lip checkpoint download failed — download manually"
    fi

    local wav2lip_fd="${REPOS_DIR}/Wav2Lip/face_detection/detection/sfd"
    mkdir -p "$wav2lip_fd"
    if [ ! -f "${wav2lip_fd}/s3fd.pth" ]; then
        log "Downloading Wav2Lip face detection model (s3fd)..."
        run wget -q "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth" \
            -O "${wav2lip_fd}/s3fd.pth" \
            2>&1 || log "[WARN] s3fd download failed"
    fi

    # SadTalker checkpoints
    local sadtalker_ckpt="${REPOS_DIR}/SadTalker/checkpoints"
    mkdir -p "$sadtalker_ckpt"
    if [ ! -f "${sadtalker_ckpt}/SadTalker_V0.0.2_512.safetensors" ]; then
        log "Downloading SadTalker checkpoints..."
        run wget -q "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors" \
            -O "${sadtalker_ckpt}/SadTalker_V0.0.2_512.safetensors" \
            2>&1 || log "[WARN] SadTalker safetensors download failed"
        run wget -q "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar" \
            -O "${sadtalker_ckpt}/mapping_00229-model.pth.tar" \
            2>&1 || log "[WARN] SadTalker mapping download failed"
        run wget -q "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar" \
            -O "${sadtalker_ckpt}/mapping_00109-model.pth.tar" \
            2>&1 || log "[WARN] SadTalker mapping download failed"
    fi

    # VideoReTalking checkpoints
    local vrt_ckpt="${REPOS_DIR}/video-retalking/checkpoints"
    mkdir -p "$vrt_ckpt"
    if [ ! -f "${vrt_ckpt}/DNet.pt" ]; then
        log "Downloading VideoReTalking checkpoints (Google Drive folder)..."
        run gdown --folder "https://drive.google.com/drive/folders/18rhjMpxK8LVVxf7PI6XwOidt8Vouv_H0" \
            -O "$vrt_ckpt" \
            2>&1 || log "[WARN] VideoReTalking checkpoint download failed — download manually"
    fi

    # MuseTalk checkpoints (uses huggingface-cli)
    if command -v huggingface-cli &>/dev/null; then
        log "Downloading MuseTalk model weights..."
        run huggingface-cli download TMElyralab/MuseTalk \
            --local-dir "${REPOS_DIR}/MuseTalk/models" \
            2>&1 || log "[WARN] MuseTalk download failed"
    else
        log "[WARN] huggingface-cli not found. Install with: pip install huggingface_hub[cli]"
    fi

    # CosyVoice 2 model (zero-shot TTS with Spanish support)
    local cosyvoice_model="${REPOS_DIR}/CosyVoice/pretrained_models/CosyVoice2-0.5B"
    if [ ! -d "$cosyvoice_model" ]; then
        log "Downloading CosyVoice2-0.5B model..."
        mkdir -p "${REPOS_DIR}/CosyVoice/pretrained_models"
        if command -v huggingface-cli &>/dev/null; then
            run huggingface-cli download FunAudioLLM/CosyVoice2-0.5B \
                --local-dir "$cosyvoice_model" \
                2>&1 || log "[WARN] CosyVoice model download failed"
        else
            log "[WARN] huggingface-cli not found for CosyVoice download"
        fi
    fi

    # dlib shape predictor
    if [ ! -f "${MODELS_DIR}/shape_predictor_68_face_landmarks.dat" ]; then
        log "Downloading dlib shape predictor..."
        run wget -q "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2" \
            -O "${MODELS_DIR}/shape_predictor_68_face_landmarks.dat.bz2"
        run bzip2 -d "${MODELS_DIR}/shape_predictor_68_face_landmarks.dat.bz2"
    fi

    log "Phase 0 complete."
}


# ---------- PHASE 1: Prepare data ----------
phase_1() {
    phase_banner 1 "Prepare source data (split clips, face-crop)"

    local manifest="${SCRIPT_DIR}/data/source/manifest.csv"
    if [ -f "$manifest" ]; then
        local count
        count=$(tail -n +2 "$manifest" | wc -l)
        log "Manifest already exists with ${count} clips."
        log "Delete ${manifest} to regenerate."
        return 0
    fi

    cd "$SCRIPT_DIR"

    if $DRY_RUN; then
        log "[DRY RUN] Would run: python3 01_prepare_data.py"
        log "  Expected output: 20 clips (5 actors x 2 emotions x 2 clips)"
        return 0
    fi

    run python3 01_prepare_data.py
}


# ---------- PHASE 2: Voice cloning ----------
phase_2() {
    phase_banner 2 "Generate voice-cloned audio (4 VC systems x 20 clips = 80 outputs)"

    cd "$SCRIPT_DIR"

    if $DRY_RUN; then
        run python3 02_generate_vc.py --dry-run
        return 0
    fi

    run python3 02_generate_vc.py
}


# ---------- PHASE 3: Lipsync ----------
phase_3() {
    phase_banner 3 "Generate lipsync videos (4 lipsync x 80 VC audios = 320 videos)"

    cd "$SCRIPT_DIR"

    if $DRY_RUN; then
        run python3 03_generate_lipsync.py --dry-run
        return 0
    fi

    run python3 03_generate_lipsync.py
}


# ---------- PHASE 4: Metrics ----------
phase_4() {
    phase_banner 4 "Compute computational metrics (11 metrics x 320 videos)"

    cd "$SCRIPT_DIR"

    if $DRY_RUN; then
        run python3 04_compute_metrics.py --dry-run
        return 0
    fi

    run python3 04_compute_metrics.py
}


# ---------- PHASE 5: Analysis ----------
phase_5() {
    phase_banner 5 "Run statistical analysis (ANOVA + post-hoc + figures)"

    cd "$SCRIPT_DIR"

    if $DRY_RUN; then
        log "[DRY RUN] Would run: python3 05_run_analysis.py --computational-only"
        return 0
    fi

    run python3 05_run_analysis.py --computational-only
}


# ============================================================
# MAIN
# ============================================================

log "============================================================"
log "  VC x Lipsync Factorial Benchmark"
log "  Started: $(date)"
log "  Start phase: ${START_PHASE}"
log "  Dry run: ${DRY_RUN}"
log "  Skip install: ${SKIP_INSTALL}"
log "  Log: ${LOG_FILE}"
log "============================================================"

cd "$SCRIPT_DIR"

PHASES=(phase_0 phase_1 phase_2 phase_3 phase_4 phase_5)

for i in "${!PHASES[@]}"; do
    if [ "$i" -ge "$START_PHASE" ]; then
        ${PHASES[$i]}
        log ""
        log "Phase ${i} finished at $(date '+%H:%M:%S')"
        log ""
    fi
done

log "============================================================"
log "  ALL PHASES COMPLETE"
log "  Finished: $(date)"
log "  Log: ${LOG_FILE}"
log "============================================================"
