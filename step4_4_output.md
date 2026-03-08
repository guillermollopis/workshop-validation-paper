# Step 4.4 Output: Implementation Task List

Generated: 2026-03-05

---

## System Description

The experiment requires:
1. A **stimulus generation pipeline** that runs 4 VC systems × 4 lipsync systems × 2 emotions × 5 identities × 2 sentences = 640 videos
2. A **computational metrics pipeline** that evaluates all 640 videos with 11 metrics
3. A **human evaluation platform** (web-based survey) for 30 participants to rate 72 videos each
4. A **statistical analysis pipeline** that runs the preregistered LMM and produces all tables/figures

---

## Task List

### Phase 1: Data Preparation

#### Task 1.1: Download and prepare source dataset
- **Input:** MEAD dataset (or CREMA-D/RAVDESS as fallback)
- **Process:**
  - Download MEAD dataset (https://wywu.github.io/projects/MEAD/MEAD.html)
  - Select 5 speaker identities (2M, 2F, 1 additional) with both neutral and emotional recordings
  - Select 2 sentences per condition (neutral × 2, emotional × 2) per identity = 20 source clips
  - Extract audio from each clip (wav format, 16kHz mono)
  - Store source video frames for lipsync input
  - Standardize: 25fps, consistent resolution, 5-10s clips
- **Output:** `data/source/` directory with 20 video clips + 20 extracted audio files + metadata CSV
- **Dependencies:** None

#### Task 1.2: Set up VC systems
- **Input:** None (installation)
- **Process:**
  - Install XTTS-v2 (Coqui TTS): `pip install TTS`
  - Install OuteTTS: clone repo + install deps
  - Install WhisperSpeech: `pip install whisperspeech`
  - Install SpeechT5: via HuggingFace transformers
  - Write a wrapper script that takes (source_audio, reference_audio) → cloned_audio for each system
  - Test each system on one sample to verify it works
- **Output:** `tools/vc/` directory with wrapper scripts, one per system
- **Dependencies:** None

#### Task 1.3: Set up lipsync systems
- **Input:** None (installation)
- **Process:**
  - Install Wav2Lip: clone repo + download pretrained model
  - Install SadTalker: clone repo + download checkpoints
  - Install VideoReTalking: clone repo + download models
  - Install MuseTalk: clone repo + install deps
  - Write a wrapper script that takes (source_video/image, driving_audio) → output_video for each system
  - Test each system on one sample to verify it works
- **Output:** `tools/lipsync/` directory with wrapper scripts, one per system
- **Dependencies:** None

### Phase 2: Stimulus Generation

#### Task 2.1: Generate cloned audio (VC step)
- **Input:** 20 source audio files from Task 1.1, 4 VC wrappers from Task 1.2
- **Process:**
  - For each source audio (20) × each VC system (4):
    - Run VC wrapper → cloned audio
    - Save as `data/vc_output/{vc_system}/{identity}_{emotion}_{sentence}.wav`
  - Total: 20 × 4 = 80 cloned audio files
  - Log any failures (system + input that failed)
- **Output:** `data/vc_output/` with 80 audio files + generation log
- **Dependencies:** Tasks 1.1, 1.2

#### Task 2.2: Generate talking-head videos (lipsync step)
- **Input:** 80 cloned audio files from Task 2.1, source videos from Task 1.1, 4 lipsync wrappers from Task 1.3
- **Process:**
  - For each cloned audio (80) × each lipsync system (4):
    - Run lipsync wrapper(source_video, cloned_audio) → output_video
    - Save as `data/generated/{vc_system}/{lipsync_system}/{identity}_{emotion}_{sentence}.mp4`
  - Total: 80 × 4 = 320 videos... wait, each audio is already per-VC, so: 20 sources × 4 VC × 4 lipsync = 320
  - Correction: 5 identities × 2 sentences × 2 emotions × 4 VC × 4 lipsync = 640 videos
  - Standardize all output: same resolution, frame rate, codec (H.264), duration
  - Log any failures
- **Output:** `data/generated/` with 640 video files + generation log
- **Dependencies:** Tasks 1.1, 1.3, 2.1

#### Task 2.3: Prepare ground truth and attention checks
- **Input:** Source videos from Task 1.1
- **Process:**
  - Copy 4 original source videos as ground-truth reference stimuli
  - Create 4 attention-check videos (mismatch audio from different identity onto a face)
  - Standardize format to match generated videos
- **Output:** `data/reference/` with 4 GT + 4 attention-check videos
- **Dependencies:** Task 1.1

### Phase 3: Computational Evaluation

#### Task 3.1: Compute lip-sync metrics
- **Input:** 640 generated videos from Task 2.2, source videos from Task 1.1
- **Process:**
  - For each generated video, compute:
    - LSE-C, LSE-D (SyncNet pretrained model)
    - AVSu (AV-HuBERT, unimodal mode)
    - AVSm (AV-HuBERT, multimodal with GT reference)
    - LMD (Dlib facial landmarks vs GT)
  - Save per-video results to CSV
- **Output:** `results/metrics_sync.csv` (640 rows × 5 metric columns)
- **Dependencies:** Task 2.2
- **Note:** Install SyncNet, AV-HuBERT, Dlib as separate dependencies

#### Task 3.2: Compute visual quality metrics
- **Input:** 640 generated videos from Task 2.2, source videos from Task 1.1
- **Process:**
  - For each generated video, compute:
    - FID (per-condition, InceptionV3 features vs source frames)
    - SSIM (per-frame, averaged)
    - CPBD (per-frame, averaged)
  - Save per-video results to CSV
- **Output:** `results/metrics_visual.csv` (640 rows × 3 metric columns)
- **Dependencies:** Task 2.2

#### Task 3.3: Compute audio quality metrics
- **Input:** 80 cloned audio files from Task 2.1, 20 source audio files from Task 1.1
- **Process:**
  - For each cloned audio, compute:
    - WavLM cosine similarity (speaker embedding vs source)
    - Mel spectrogram cosine similarity (vs source)
    - WER (Whisper ASR transcription vs source transcript)
  - Save per-audio results to CSV
  - Note: Audio metrics are per-VC-system only (not per-lipsync), but propagate to all lipsync combinations
- **Output:** `results/metrics_audio.csv` (80 rows × 3 metric columns)
- **Dependencies:** Task 2.1

#### Task 3.4: Merge all metrics
- **Input:** CSVs from Tasks 3.1, 3.2, 3.3
- **Process:**
  - Merge all metrics into a single master CSV with columns: `identity, emotion, sentence, vc_system, lipsync_system, LSE_C, LSE_D, AVSu, AVSm, LMD, FID, SSIM, CPBD, WavLM_sim, mel_sim, WER`
  - Add condition labels for factorial analysis
- **Output:** `results/all_metrics.csv` (640 rows × all metrics)
- **Dependencies:** Tasks 3.1, 3.2, 3.3

### Phase 4: Human Evaluation

#### Task 4.1: Build evaluation web interface
- **Input:** 640 generated videos + 4 GT + 4 attention-check videos
- **Process:**
  - Build a web app (e.g., Flask/Django or Streamlit) that:
    - Shows one video at a time
    - Collects 4 MOS ratings per video (overall, lip sync, voice, visual)
    - Randomizes presentation order per participant
    - Assigns 2 identities per participant (counterbalanced)
    - Records response time per trial
    - Includes demographic questionnaire (age, hearing/vision)
    - Stores results to database or CSV
  - Serve videos from local storage or CDN
  - Deploy locally or on institutional server (for controlled lab) or online (for remote)
- **Output:** Running web app with evaluation interface
- **Dependencies:** Task 2.2, Task 2.3

#### Task 4.2: Run pilot study
- **Input:** Evaluation platform from Task 4.1
- **Process:**
  - Recruit N = 5 pilot participants
  - Run the full evaluation session
  - Check: (a) session duration is ~25-30 min, (b) data format is correct, (c) attention checks work, (d) ratings show variance (not all same)
  - Fix any UI/UX issues
  - Verify exclusion criteria catch problems
- **Output:** Pilot data + list of fixes needed
- **Dependencies:** Task 4.1

#### Task 4.3: Run full study
- **Input:** Fixed evaluation platform from Task 4.2
- **Process:**
  - Recruit N = 30-40 participants (target 30 valid after exclusions)
  - Run evaluation sessions
  - Apply exclusion criteria from preregistration
  - Export final dataset
- **Output:** `results/human_ratings.csv` (N_valid × 72 trials × 5 columns: 4 MOS + response_time)
- **Dependencies:** Task 4.2, IRB approval (Step 4.3b)

### Phase 5: Statistical Analysis

#### Task 5.1: Apply exclusion criteria and prepare analysis dataset
- **Input:** `results/human_ratings.csv` from Task 4.3
- **Process:**
  - Apply participant-level exclusions (attention check, flat responding, completion)
  - Apply trial-level exclusions (response time)
  - Log exclusion counts and reasons
  - Merge human ratings with computational metrics (from Task 3.4)
- **Output:** `results/analysis_dataset.csv` + exclusion report
- **Dependencies:** Tasks 3.4, 4.3

#### Task 5.2: Run primary analysis (LMM)
- **Input:** `results/analysis_dataset.csv`
- **Process:**
  - Fit LMM: `Overall_MOS ~ VC_tool * Lipsync_tool * Emotion + (1|participant) + (1|identity)`
  - Extract: F-tests for all main effects and interactions, p-values, η²
  - Post-hoc: Pairwise comparisons with BH FDR correction for significant effects
  - Compute Cohen's d for pairwise comparisons
  - Report marginal and conditional R²
  - Repeat for each MOS dimension (lip sync, voice, visual)
- **Output:** `results/lmm_results.txt` + summary tables
- **Dependencies:** Task 5.1

#### Task 5.3: Run metric validation analysis (H6)
- **Input:** `results/all_metrics.csv` + condition-level average human MOS
- **Process:**
  - Average human MOS per condition (32 conditions)
  - Compute Spearman ρ between each computational metric and average MOS
  - Bootstrap 95% CI (n = 10,000)
  - Create correlation comparison table (like THEval Table 3)
- **Output:** `results/metric_validation.csv` + correlation table
- **Dependencies:** Tasks 5.1, 3.4

#### Task 5.4: Run computational-only factorial analysis
- **Input:** `results/all_metrics.csv`
- **Process:**
  - For each computational metric: run 4 × 4 × 2 factorial ANOVA
  - Report F-values, p-values, η² for all terms
  - Compare which metrics show the same pattern as human ratings
- **Output:** `results/computational_anova.txt` + summary tables
- **Dependencies:** Task 3.4

#### Task 5.5: Generate figures and tables
- **Input:** All results from Tasks 5.2-5.4
- **Process:**
  - **Figure 1:** Methodology pipeline diagram (for Step 7)
  - **Figure 2:** Interaction plot — mean MOS by VC × Lipsync (4×4 grid, colored by emotion)
  - **Figure 3:** Heatmap — 4×4 VC × Lipsync matrix showing mean overall MOS per cell
  - **Figure 4:** Emotion degradation — neutral vs emotional MOS per pipeline (paired bar chart)
  - **Figure 5:** Metric-human correlation — bar chart of Spearman ρ per metric with CI whiskers
  - **Table 1:** Condition means and SDs for all MOS dimensions
  - **Table 2:** LMM ANOVA table (F, df, p, η²) for all effects
  - **Table 3:** Metric-human correlations (compare to THEval's Table)
  - **Table 4:** Post-hoc pairwise comparisons with effect sizes
- **Output:** `figures/` directory with publication-ready plots + `tables/` directory
- **Dependencies:** Tasks 5.2, 5.3, 5.4

---

## Task Dependency Graph

```
Phase 1 (setup):           1.1 ─────────────┬──────────────┐
                           1.2 ──┐           │              │
                           1.3 ──┼───┐       │              │
                                 │   │       │              │
Phase 2 (generation):     2.1 ◄──┘   │       │              │
                           │         │       │              │
                          2.2 ◄──────┘───────┘              │
                           │                                │
                          2.3 ◄─────────────────────────────┘
                           │
Phase 3 (metrics):   3.1 ◄─┤  3.2 ◄─┤  3.3 ◄─(from 2.1)
                           │        │        │
                          3.4 ◄─────┴────────┘
                           │
Phase 4 (human):     4.1 ◄─┤ (from 2.2, 2.3)
                           │
                     4.2 ◄─┘
                           │
                     4.3 ◄─┘ (+ IRB approval)
                           │
Phase 5 (analysis):  5.1 ◄─┤ (from 3.4, 4.3)
                           │
               5.2 ◄───────┤
               5.3 ◄───────┤
               5.4 ◄───────┘ (from 3.4 only)
                           │
               5.5 ◄───────┘ (from 5.2, 5.3, 5.4)
```

---

## Estimated Effort

| Phase | Tasks | Estimated time | Notes |
|-------|-------|---------------|-------|
| Phase 1: Setup | 1.1–1.3 | 1–2 days | Install tools, prepare data |
| Phase 2: Generation | 2.1–2.3 | 1–3 days | GPU-dependent; can parallelize across systems |
| Phase 3: Metrics | 3.1–3.4 | 1–2 days | GPU for SyncNet/AV-HuBERT; CPU for rest |
| Phase 4: Human eval | 4.1–4.3 | 2–4 weeks | Building platform + recruitment + running |
| Phase 5: Analysis | 5.1–5.5 | 2–3 days | Mostly automated scripts |

**Critical path:** Phase 4 (human evaluation) is the bottleneck. Phases 2-3 can run in parallel with Phase 4 platform development.

---

## Output for Step 5

18 concrete coding tasks, each with defined inputs, outputs, and dependencies. Tasks 1.1–3.4 form the automated pipeline (Steps 5 coding). Tasks 4.1–4.3 require human recruitment. Tasks 5.1–5.5 are the analysis scripts.
