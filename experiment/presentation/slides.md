---
marp: true
theme: default
class: lead
paginate: true
math: katex
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  :root {
    --bg-dark: #1a1a2e;
    --bg-mid: #16213e;
    --bg-light: #0f3460;
    --accent-red: #e94560;
    --accent-gold: #f0a500;
    --accent-blue: #53d8fb;
    --text-main: #e8e8e8;
    --text-muted: #8892b0;
    --card-bg: rgba(255,255,255,0.07);
    --card-border: rgba(255,255,255,0.12);
  }
  section {
    background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-mid) 50%, var(--bg-light) 100%);
    color: var(--text-main);
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 25px;
    padding: 45px 55px;
  }
  section.lead {
    display: flex; flex-direction: column; justify-content: center; text-align: center;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  }
  section.lead h1 { font-size: 40px; color: #fff; text-shadow: 0 2px 10px rgba(0,0,0,0.3); margin-bottom: 15px; }
  section.lead h2 { font-size: 20px; color: var(--accent-blue); font-weight: 400; }
  section.lead p { color: var(--text-muted); font-size: 16px; }
  section.divider {
    display: flex; flex-direction: column; justify-content: center; text-align: center;
    background: linear-gradient(135deg, #e94560 0%, #c0392b 100%);
  }
  section.divider h1 { font-size: 48px; color: #fff; font-weight: 700; letter-spacing: 2px; border: none; }
  section.divider p { color: rgba(255,255,255,0.8); font-size: 20px; }
  h1 { color: var(--accent-red); font-size: 33px; font-weight: 700; border-bottom: 3px solid var(--accent-red); padding-bottom: 8px; margin-bottom: 20px; }
  h2 { color: var(--accent-blue); font-size: 26px; font-weight: 600; }
  h3 { color: var(--accent-gold); font-size: 22px; }
  strong { color: var(--accent-gold); }
  em { color: var(--accent-blue); font-style: normal; }
  a { color: var(--accent-blue); }
  /* ---- Table overrides (force dark theme on all tables) ---- */
  table { width: 100%; border-collapse: collapse; font-size: 18px; background: transparent !important; }
  thead, tbody, tr { background: transparent !important; }
  th { background: rgba(233,69,96,0.3) !important; color: #fff !important; font-weight: 700; padding: 8px 10px; border-bottom: 2px solid var(--accent-red); text-align: left; }
  td { padding: 6px 10px; border-bottom: 1px solid var(--card-border); color: var(--text-main) !important; background: transparent !important; }
  tr:nth-child(even) td { background: rgba(255,255,255,0.04) !important; }
  /* ---- End table overrides ---- */
  blockquote { background: var(--card-bg); border-left: 4px solid var(--accent-gold); border-radius: 0 8px 8px 0; padding: 12px 18px; margin: 12px 0; font-size: 21px; }
  blockquote p { margin: 0; }
  li::marker { color: var(--accent-red); }
  li { margin-bottom: 6px; }
  img { border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
  code { background: rgba(255,255,255,0.1); padding: 2px 5px; border-radius: 4px; color: var(--accent-gold); font-size: 0.85em; }
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
  .highlight-box { background: linear-gradient(135deg, rgba(233,69,96,0.15), rgba(240,165,0,0.15)); border: 1px solid var(--accent-red); border-radius: 10px; padding: 15px 20px; text-align: center; margin: 10px 0; }
  .stat-big { font-size: 52px; font-weight: 700; line-height: 1.1; }
  .stat-label { font-size: 16px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
  .badge { display: inline-block; background: var(--accent-red); color: white; padding: 2px 10px; border-radius: 12px; font-size: 14px; font-weight: 600; }
  .badge-blue { background: var(--accent-blue); color: #1a1a2e; }
  .badge-gold { background: var(--accent-gold); color: #1a1a2e; }
---

<!-- _class: lead -->

# A Factorial Benchmark of Voice Cloning and Lip Synchronization Pipelines

## for Spanish-Language Talking Head Generation

**Author Names** | Institution
Conference Name, 2026

---

<!-- _class: divider -->

# THE GAP

Why we need factorial benchmarks

---

# Motivation

Talking head generation combines two AI components:

<div class="columns">
<div>

### Voice Cloning (VC)
Generate speech in a target speaker's voice

- XTTS-v2, kNN-VC, OpenVoice, CosyVoice...
- Evaluated in isolation (ClonEval, RVCBench)

</div>
<div>

### Lip Synchronization
Animate face to match audio

- Wav2Lip, SadTalker, VideoReTalking...
- Evaluated in isolation (THEval: 17 models)

</div>
</div>

> **The problem:** No benchmark evaluates them *together* in a factorial design.
> Practitioners must combine components but have no evidence about interactions.

---

# What Exists vs. What's Missing

| Benchmark | VC | Lipsync | **Factorial?** | Purpose |
|-----------|:--:|:-------:|:--------------:|---------|
| THEval (2025) | 0 | 17 | No | Lipsync quality |
| ClonEval (2025) | 5 | 0 | No | VC quality |
| RVCBench (2026) | 11 | 0 | No | VC robustness |
| AV-Deepfake1M++ (2025) | 5 | 3 | **Yes** | Deepfake *detection* |
| **This work** | **4** | **3** | **Yes** | **Quality assessment** |

<div class="highlight-box">

**First factorial VC × Lipsync quality benchmark on same stimuli**

</div>

---

# Research Questions

<div class="columns">
<div>

### Hypotheses

**H1** VC system affects audio quality
**H2** Lipsync system affects visual quality
**H3** VC × Lipsync interaction exists
**H4** Emotion degrades quality
**H5** Emotion × Tool interaction
**H6** Metrics correlate with human ratings

</div>
<div>

### Design

$4 \text{ VC} \times 3 \text{ Lipsync} \times 2 \text{ Emotions}$

- 5 Spanish-speaking actors
- 2 clips per condition (5s each)
- 10 computational metrics
- <span class="badge">PLACEHOLDER</span> Human eval (N=30)

</div>
</div>

---

<!-- _class: divider -->

# METHOD

4 VC × 3 Lipsync × 2 Emotions × 5 Actors

---

# Source Material

<style scoped>
h1 { margin-bottom: 12px; }
h3 { margin-bottom: 6px; margin-top: 10px; }
li { margin-bottom: 4px; }
</style>

### 5 Actors, 2 Conditions

| Actor | Gender | Neutral condition | Emotional condition |
|-------|--------|-------------------|---------------------|
| **George** | M | Reading instructions | Dramatic monologue |
| **Jordi** | M | Reading instructions | Dramatic monologue |
| **Lisset** | F | Reading instructions | Dramatic monologue |
| **Maisa** | F | Reading instructions | Dramatic monologue |
| **Selene** | F | Reading instructions | Dramatic monologue |

### Processing Pipeline
1. **Extract** 2 clips × 5s from each ~60s video → **20 source clips**
2. **Face crop** to 512×512 via MediaPipe (two-pass: detect → smooth 7-frame → crop 1.5× padding)
3. **Extract audio** at 16 kHz mono | **Language:** Spanish

---

# Voice Cloning Systems

| System | Approach | Input | Language | Output |
|--------|----------|-------|----------|--------|
| **XTTS-v2** | Text re-synthesis | Whisper ASR → TTS | Spanish (explicit) | Multi-rate |
| **kNN-VC** | kNN feature matching | Audio → audio | Agnostic | 16 kHz |
| **OpenVoice V2** | Tone color transfer | Audio → audio | Agnostic | Multi-rate |
| **CosyVoice 2** | Zero-shot TTS | Whisper ASR → TTS | Spanish (native) | 22 kHz |

- **Text-based** (XTTS-v2, CosyVoice): transcribe source → re-synthesize with reference voice
- **Audio-based** (kNN-VC, OpenVoice): directly convert voice timbre

**Result:** 20 clips × 4 VC = **80 VC outputs** (100% success)

---

# Lip Synchronization Systems

| System | Input type | Method |
|--------|-----------|--------|
| **Wav2Lip** | Video + audio | Modify mouth region of input frames |
| **SadTalker** | Still image + audio | Generate from 3D motion coefficients |
| **VideoReTalking** | Video + audio | DNet + LNet + ENet pipeline |
| ~~MuseTalk~~ | ~~Video + audio~~ | *Disabled: mmpose ↔ Python 3.13* |

**Result:** 80 VC × 3 lipsync = 240 planned → **232 generated** (96.7%)
- 8 failures: SadTalker face detection errors

All outputs standardized: **512×512, 25 fps, H.264**

---

# Evaluation Metrics (10)

<div class="columns">
<div>

### Synchronization (5)
| Metric | Measures |
|--------|----------|
| **LSE-C** | Sync confidence (SyncNet proxy) |
| **LSE-D** | Sync distance (SyncNet proxy) |
| **AVSu** | AV sync, utterance (AV-HuBERT proxy) |
| **AVSm** | AV sync, matched vs GT |
| **LMD** | Lip landmark distance vs GT |

</div>
<div>

### Visual (2) + Audio (3)
| Metric | Measures |
|--------|----------|
| **SSIM** | Structural similarity vs GT |
| **CPBD** | Sharpness (Laplacian variance) |
| **WavLM sim** | Speaker embedding similarity |
| **Mel sim** | Spectral similarity |
| **WER** | Word error rate (Whisper) |

</div>
</div>

**Statistical test:** One-way ANOVA per metric × factor, BH FDR at $\alpha = 0.05$

---

<!-- _class: divider -->

# RESULTS

232 videos, 10 metrics, 30 ANOVA tests

---

# The Big Picture: Clean Factorization

<div class="highlight-box">

VC system controls **audio** quality &nbsp;&nbsp;|&nbsp;&nbsp; Lipsync system controls **visual** quality &nbsp;&nbsp;|&nbsp;&nbsp; Emotion = **no effect**

</div>

| Factor | Significant effects | Metrics affected | $\eta^2$ range |
|--------|:-------------------:|-----------------|:-------------:|
| **VC system** | 5 / 10 | WavLM, Mel, WER, LSE-C, LSE-D | 0.20 – **0.73** |
| **Lipsync system** | 6 / 10 | SSIM, LMD, CPBD, LSE-C, LSE-D, AVSm | 0.04 – **0.85** |
| **Emotion** | 0 / 10 | None | < 0.01 |

**11 out of 30** tests significant after FDR correction
All in expected directions: VC → audio, Lipsync → visual

---

# H1: VC System Dominates Audio Metrics

<div class="columns">
<div>

| Metric | $F$ | $p$ | $\eta^2$ |
|--------|----:|----:|--------:|
| **WavLM sim** | 204.98 | <.001 | **.730** |
| **Mel sim** | 57.69 | <.001 | **.432** |
| **LSE-C** | 42.44 | <.001 | .358 |
| **LSE-D** | 41.93 | <.001 | .356 |
| **WER** | 17.58 | <.001 | .196 |

VC explains **43–73%** of variance
in audio quality metrics

</div>
<div>

### Speaker Similarity by VC
| System | WavLM sim |
|--------|----------:|
| **OpenVoice V2** | **0.934** |
| kNN-VC | 0.918 |
| XTTS-v2 | 0.895 |
| CosyVoice 2 | 0.673 |

OpenVoice V2 (audio-to-audio) preserves speaker identity best

</div>
</div>

---

# H2: Lipsync System Dominates Visual Metrics

<style scoped>
section { font-size: 22px; }
table { font-size: 16px; }
th, td { padding: 5px 8px; }
h1 { margin-bottom: 14px; }
h3 { margin-top: 8px; margin-bottom: 6px; }
p { margin: 4px 0; }
</style>

<div class="columns">
<div>

### ANOVA Results

| Metric | $F$ | $p$ | $\eta^2$ |
|--------|----:|----:|--------:|
| **SSIM** | 623.44 | <.001 | **.845** |
| **LMD** | 282.64 | <.001 | **.712** |
| **CPBD** | 18.38 | <.001 | .138 |

Lipsync explains **71–85%** of variance
in visual quality metrics

</div>
<div>

### Visual Quality by Lipsync System

| System | SSIM | LMD ↓ | CPBD |
|--------|-----:|------:|-----:|
| **Wav2Lip** | **0.920** | **4.65** | 91.8 |
| **VideoReTalking** | 0.916 | 8.46 | 109.7 |
| SadTalker | 0.510 | 30.87 | 66.9 |

Wav2Lip & VideoReTalking preserve visual structure; SadTalker (image-based) diverges

</div>
</div>

---

# H4: Emotion Has No Effect

<style scoped>
section { font-size: 22px; }
table { font-size: 16px; }
th, td { padding: 5px 8px; }
</style>

<div class="highlight-box">

Emotion condition (neutral vs. emotional) had **no significant effect** on any of the 10 metrics

</div>

| Metric | $F$ | $p$ | $\eta^2$ | Significant? |
|--------|----:|----:|--------:|:------------:|
| WavLM | 3.29 | .071 | .014 | No |
| LMD | 2.87 | .092 | .012 | No |
| LSE-D | 2.33 | .129 | .010 | No |
| Mel sim | 1.19 | .276 | .005 | No |
| LSE-C | 1.19 | .276 | .005 | No |
| SSIM | 0.69 | .407 | .003 | No |
| AVSm | 0.55 | .460 | .002 | No |
| WER | 0.15 | .700 | .001 | No |
| AVSu | 0.03 | .852 | <.001 | No |
| CPBD | 0.03 | .853 | <.001 | No |

---

# H4: Why No Emotion Effect?

<div class="highlight-box">

All 10 metrics: $p > .05$, max $\eta^2 = 0.014$ (WavLM)

</div>

**Three possibilities:**

1. **Dramatic monologue ≠ discrete emotions** — unlike ClonEval's categorical emotions (happy, sad, angry), our stimuli use continuous emotional speech
2. **Five-second clips too short** — emotion effects may need longer durations to accumulate measurable degradation
3. **Computational metrics insensitive** — metrics may be genuinely blind to emotion quality; human evaluation needed

> This makes **H6** (metric validity via human correlation) especially important as a next step.

---

# Heatmaps: VC × Lipsync Interaction

![w:950 center](../figures/fig2_heatmaps.png)

Rows = VC systems, Columns = Lipsync systems. Audio metrics vary by row (VC), visual metrics vary by column (Lipsync).

---

# VC System Comparison

![w:1000 center](../figures/fig3_vc_system_comparison.png)

---

# Lipsync System Comparison

![w:1000 center](../figures/fig3_lipsync_system_comparison.png)

---

# Emotion Comparison

![w:1000 center](../figures/fig4_emotion_comparison.png)

---

<!-- _class: divider -->

# DISCUSSION

What this means for practitioners

---

# Key Takeaways

<div class="columns">
<div>

### Independence

VC and lipsync affect **non-overlapping** metric domains:
- VC → audio ($\eta^2$ = 0.20–0.73)
- Lipsync → visual ($\eta^2$ = 0.14–0.85)
- Cross-domain: $\eta^2$ < 0.001

**Practical implication:**
Select each component independently based on domain-specific needs

</div>
<div>

### Metric Insights

- **LSE-C/D** primarily reflect audio, not visual sync
  - Consistent with Zhang et al. (ICIP 2024)
  - SyncNet bias documented by Yaman et al. (ECCV 2024)
- **AVSu** showed no sensitivity to any factor
- **SSIM** is the most discriminative visual metric ($\eta^2$ = 0.85)


</div>
</div>

---

# Comparison with Literature

<style scoped>
table { font-size: 16px; }
th, td { padding: 5px 8px; }
</style>

| Finding | Prior work | Our result |
|---------|-----------|------------|
| LSE-C/D correlate with sync quality | Zhang (ICIP '24): **poor correlation** | Confirmed: LSE-C/D track VC choice, not lipsync |
| SyncNet biased toward neutral | Yaman (ECCV '24): yes | No emotion effect at all in our metrics |
| Emotional speech degrades VC | ClonEval: partial degradation | **No effect** in our 5s clips |
| Combined pipeline = interaction | AV-Deepfake1M++: implied | **Largely additive** at metric level |

> The factorial design reveals what component-level benchmarks cannot: **independence, not interaction, is the dominant pattern.**

---

# Limitations & Future Work

<style scoped>
section { font-size: 22px; }
li { margin-bottom: 4px; }
</style>

<div class="columns">
<div>

### Limitations

- **Small pool:** 5 actors, Spanish only
- **MuseTalk disabled** (Python 3.13 / mmpose)
- **8 SadTalker failures** (non-random)
- **High WER** across all systems (mean 1.12)
- **Proxy metrics**, not full SyncNet/AV-HuBERT
- **No human evaluation** yet

</div>
<div>

### Next Steps

- <span class="badge">PLACEHOLDER</span> **Human evaluation** (N=30, 4 MOS dimensions)
  - Design ready, Flask app built
- Include MuseTalk when mmpose updated
- Test additional languages
- Longer clips (>5s)
- Full metric implementations
- VC × Lipsync interaction in human perception

</div>
</div>

---

# Human Evaluation Design <span class="badge">PLANNED</span>

<style scoped>
section { font-size: 22px; }
li { margin-bottom: 4px; }
</style>

<div class="columns">
<div>

### Protocol

- **N = 30** participants
- 2 identities per participant
- 32 conditions each (4 VC × 4 LS × 2 emo)
- **64 ratings** per participant

### 4 MOS Dimensions (1–5)
1. Overall quality
2. Lip synchronization
3. Voice naturalness
4. Visual naturalness

</div>
<div>

### Statistical Analysis

**LMM:**
$$\text{MOS} \sim \text{VC} \times \text{LS} \times \text{Emo} + (1|\text{part.}) + (1|\text{id})$$

**H6: Metric validity**
Spearman $\rho$ between computational metrics and human MOS
- Bootstrap 95% CI (10k iterations)
- Compare with THEval's $\rho = 0.870$

</div>
</div>

---

# H1–H3: Human Ratings by System <span class="badge">PLACEHOLDER</span>

<style scoped>
section { font-size: 21px; }
table { font-size: 15px; }
th, td { padding: 4px 8px; }
</style>

<div class="columns">
<div>

### MOS by VC System (H1)
| VC System | Overall | Lip sync | Voice nat. | Visual nat. |
|-----------|:-------:|:--------:|:----------:|:-----------:|
| XTTS-v2 | — | — | — | — |
| kNN-VC | — | — | — | — |
| OpenVoice V2 | — | — | — | — |
| CosyVoice 2 | — | — | — | — |

### MOS by Lipsync System (H2)
| Lipsync | Overall | Lip sync | Voice nat. | Visual nat. |
|---------|:-------:|:--------:|:----------:|:-----------:|
| Wav2Lip | — | — | — | — |
| SadTalker | — | — | — | — |
| VideoReTalking | — | — | — | — |

</div>
<div>

### LMM Results (H1–H3)
| Effect | MOS dim. | $F$ | $p$ | $\eta^2_p$ |
|--------|----------|----:|----:|-----------:|
| VC (H1) | Overall | — | — | — |
| VC (H1) | Voice nat. | — | — | — |
| LS (H2) | Overall | — | — | — |
| LS (H2) | Lip sync | — | — | — |
| VC×LS (H3) | Overall | — | — | — |
| VC×LS (H3) | Lip sync | — | — | — |

> *Fill with LMM output after running `05_run_analysis.py` on human data*

</div>
</div>

---

# H4–H5: Emotion in Human Perception <span class="badge">PLACEHOLDER</span>

<div class="columns">
<div>

### MOS by Emotion (H4)
| Condition | Overall | Lip sync | Voice nat. | Visual nat. |
|-----------|:-------:|:--------:|:----------:|:-----------:|
| Neutral | — | — | — | — |
| Emotional | — | — | — | — |
| **Difference** | — | — | — | — |

### LMM: Emotion Effects
| Effect | MOS dim. | $F$ | $p$ | $\eta^2_p$ |
|--------|----------|----:|----:|-----------:|
| Emotion (H4) | Overall | — | — | — |
| Emo×VC (H5) | Overall | — | — | — |
| Emo×LS (H5) | Lip sync | — | — | — |

</div>
<div>

### Key Question

Do human judges detect emotion effects that **computational metrics missed**?

- Computational: 0/10 metrics significant for emotion
- Human: <span class="badge">PLACEHOLDER</span> — / 4 MOS dimensions significant

> *If humans detect differences that metrics don't → strong case for human evaluation in talking head benchmarks*

</div>
</div>

---

# H6: Metric Validity <span class="badge">PLACEHOLDER</span>

<style scoped>
table { font-size: 16px; }
th, td { padding: 5px 8px; }
</style>

### Spearman $\rho$ : Computational Metrics vs. Human MOS

| Metric | vs. Overall | vs. Lip sync | vs. Voice nat. | vs. Visual nat. |
|--------|:----------:|:------------:|:--------------:|:---------------:|
| LSE-C | — | — | — | — |
| LSE-D | — | — | — | — |
| SSIM | — | — | — | — |
| LMD | — | — | — | — |
| CPBD | — | — | — | — |
| WavLM sim | — | — | — | — |
| Mel sim | — | — | — | — |
| WER | — | — | — | — |

> Bootstrap 95% CI (10k iterations). Compare with THEval's best: $\rho = 0.870$

*[Insert scatter plot: best metric vs. human MOS — `figures/fig_metric_validity.png`]*

---

<!-- _class: lead -->

# Thank You

## A Factorial Benchmark of Voice Cloning and Lip Synchronization Pipelines

<br>

**4 VC** × **3 Lipsync** × **2 Emotions** × **5 Actors** = **232 stimulus videos**

VC controls audio ($\eta^2$ = 0.73) &nbsp;|&nbsp; Lipsync controls visual ($\eta^2$ = 0.85) &nbsp;|&nbsp; Emotion = no effect

<br>

Code & data: <span class="badge">PLACEHOLDER</span> GitHub / OSF
Contact: author@institution.edu
