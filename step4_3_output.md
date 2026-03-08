# Step 4.3 Output: Preregistration Draft

Generated: 2026-03-05
Format: AsPredicted (https://aspredicted.org/)

---

## 1. Have any data been collected for this study already?

No. No data have been collected yet. No pilot data exist. This preregistration is being filed before any stimuli are generated or participants recruited.

## 2. What is the main question being asked or hypothesis being tested?

**Primary question:** How does the choice of voice-cloning tool and lip-synchronization tool — and their interaction — affect the perceived quality of talking-head videos, and does this effect differ between neutral and emotional speech?

**Primary hypothesis (H3):** The quality of combined voice-cloning + lip-sync pipelines shows a significant interaction effect — specific tool pairings produce significantly different quality than predicted by main effects alone (i.e., quality is not simply additive).

**Secondary hypotheses:**
- H1: The choice of voice-cloning system significantly affects perceived talking-head video quality.
- H2: The choice of lip-sync system significantly affects perceived talking-head video quality.
- H4: Both computational metrics and human-perceived quality are significantly lower for emotional speech than for neutral speech, across all pipeline combinations.
- H5: The magnitude of quality degradation from neutral to emotional speech differs across pipeline combinations (emotion × tool interaction).
- H6: Standard computational metrics (LSE-C, LSE-D, FID) show weak-to-moderate correlation (|ρ| < 0.5) with human quality ratings for combined pipelines.

## 3. Describe the key dependent variable(s) specifying how they will be measured.

### Computational metrics (automated, applied to all 640 generated videos):
- **LSE-C** (lip-sync confidence) and **LSE-D** (lip-sync distance): Computed using pretrained SyncNet model
- **AVSu** (unimodal AV synchronization): Computed using AV-HuBERT model
- **FID** (Fréchet Inception Distance): Computed per-condition against source video frames using InceptionV3 features
- **SSIM** (Structural Similarity Index): Per-frame, averaged over video
- **WER** (Word Error Rate): Extracted from generated video audio using Whisper ASR, compared to source transcript
- **WavLM cosine similarity**: Speaker embedding similarity between source and cloned audio using WavLM model
- **Mel spectrogram cosine similarity**: Spectral similarity between source and cloned audio

### Human ratings (collected from N ≈ 30 participants):
- **Overall quality** (5-point MOS: 1=very poor, 5=excellent)
- **Lip synchronization** (5-point MOS: 1=completely out of sync, 5=perfectly synchronized)
- **Voice naturalness** (5-point MOS: 1=robotic/distorted, 5=indistinguishable from natural)
- **Visual naturalness** (5-point MOS: 1=clearly artificial, 5=indistinguishable from real)

All human ratings use a 5-point Mean Opinion Score scale with labeled anchors at each point.

### Derived measure:
- **Spearman rank correlation (ρ)** between each computational metric and average human overall-quality MOS across all 32 conditions, with 95% CI via bootstrapping (n = 10,000 resamples).

## 4. How many and which conditions will participants be assigned to?

**Design:** 4 (voice-cloning systems) × 4 (lip-sync systems) × 2 (speech conditions: neutral vs. emotional) = **32 conditions**, fully crossed factorial.

**Within-subjects:** All participants rate stimuli from all 32 conditions. Presentation order is randomized per participant.

**Voice-cloning systems (4 levels):**
1. XTTS-v2 (Coqui)
2. OuteTTS
3. WhisperSpeech
4. SpeechT5 (Microsoft)

**Lip-sync systems (4 levels):**
1. Wav2Lip
2. SadTalker
3. VideoReTalking
4. MuseTalk

**Speech conditions (2 levels):**
1. Neutral
2. Emotional (anger, happiness, or sadness — one emotion per source clip, balanced across identities)

**Source material:** 5 speaker identities from the MEAD dataset (2 male, 2 female, 1 additional), each with 2 sentences per speech condition.

**Stimuli per participant:** Each participant rates 64 videos (32 conditions × 2 identities, counterbalanced).

**Additional stimuli (not part of factorial analysis):**
- 4 ground-truth (unmodified) videos as reference/upper-bound
- 4 attention-check videos (mismatched audio) as quality-control

## 5. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

### Primary analysis (H3 — interaction effect):
A **linear mixed model (LMM)** predicting human MOS (overall quality) from:

```
Overall_MOS ~ VC_tool * Lipsync_tool * Speech_condition + (1|participant) + (1|source_identity)
```

where `VC_tool * Lipsync_tool * Speech_condition` expands to all main effects, two-way interactions, and the three-way interaction. `(1|participant)` and `(1|source_identity)` are random intercepts.

The primary test is the **VC_tool × Lipsync_tool interaction term** (F-test, α = 0.05).

### Secondary analyses:
- **H1 and H2:** Main effects of VC_tool and Lipsync_tool from the same LMM.
- **H4:** Main effect of Speech_condition from the same LMM.
- **H5:** VC_tool × Lipsync_tool × Speech_condition three-way interaction from the same LMM.
- **H6:** Spearman rank correlation between each computational metric and average overall MOS across all 32 conditions. Report ρ with bootstrapped 95% CI.

### Post-hoc comparisons:
For any significant main effect (α < 0.05), conduct pairwise comparisons using estimated marginal means with **Benjamini-Hochberg FDR correction** (α_FDR = 0.05).

### Same LMM repeated for each human rating dimension:
- Lip synchronization MOS
- Voice naturalness MOS
- Visual naturalness MOS

### For computational metrics:
Run the same 4 × 4 × 2 factorial ANOVA per metric (no random participant effect since these are automated). Report effect sizes (η²) for all terms.

### Effect sizes:
- **η² (partial)** for all ANOVA/LMM effects
- **Cohen's d** for pairwise comparisons
- **Marginal and conditional R²** for LMMs
- **Spearman ρ** for metric-human correlations

### Software:
- R: `lme4::lmer()` for LMMs, `emmeans` for post-hoc, `effectsize` for effect sizes
- Or Python: `pymer4` or `statsmodels.MixedLM`

## 6. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

### Participant-level exclusion (applied before analysis):
1. **Attention check failure:** Exclude participants who rate ≥50% of attention-check videos (mismatched audio) with an overall quality score ≥ 4/5.
2. **Flat responding:** Exclude participants who give the same rating (any single value) to >90% of all stimuli.
3. **Non-completion:** Exclude participants who complete <80% of the total stimuli.

### Trial-level exclusion:
1. **Response time:** Exclude individual ratings where response time < 1 second (likely random clicking) or > 60 seconds (likely distracted/AFK).

### Stimulus-level exclusion:
1. **Generation failure:** If a VC or lipsync system produces corrupted, empty, or zero-length output for a specific input, exclude that cell. Document which system failed and on which input.

### Handling:
- Report the number and reason for all exclusions.
- Run primary analysis on the exclusion-applied dataset.
- Run a sensitivity analysis on the full dataset (all participants, all trials) and report whether conclusions change.
- Do NOT replace excluded data with imputed values.

## 7. How many observations will be collected or what will determine sample size?

### Computational metrics:
- **640 generated videos** (4 VC × 4 lipsync × 2 emotions × 5 identities × 2 sentences)
- All videos are evaluated by all computational metrics (no sampling)

### Human evaluation:
- **Target: N = 30 participants**
- **Justification:** For a within-subjects design with 32 conditions, medium effect size (Cohen's f = 0.25), α = 0.05, and power = 0.80, G*Power is needed to compute the exact N. The estimate of 30 provides a buffer for ~5 exclusions and targets power ≈ 0.90.
- **Literature precedent:** ICIP 2024 used N = 15 for 4 conditions; THEval collected 3,519 total ratings; we have 32 conditions requiring more power.
- **Stopping rule:** Data collection stops when 30 valid participants (after exclusions) have completed the study. If the exclusion rate exceeds 20%, recruit additional participants in batches of 5 until 30 valid are reached, up to a maximum of 40 total.

### Per participant:
- 64 experimental trials (32 conditions × 2 identities) + 4 ground truth + 4 attention checks = **72 total trials**
- Estimated session duration: 25–30 minutes

## 8. Anything else you would like to pre-register?

### Exploratory analyses (not confirmatory):
1. Per-emotion breakdown: If emotional stimuli include multiple emotions (anger, happiness, sadness), analyze each emotion separately. This is exploratory due to reduced power per emotion.
2. Individual VC × lipsync cell analysis: Identify specific tool pairings with notably good or bad performance (post-hoc exploratory).
3. Gender effects: Check if source speaker gender moderates any effects.
4. Language: If multilingual stimuli are included, check language as a covariate.

### Transparency:
- All code for stimulus generation, metric computation, and statistical analysis will be made publicly available.
- Raw human rating data (anonymized) will be deposited in a public repository (OSF or Zenodo).
- The generated video stimuli will be made available for reproducibility.

### Deviations from preregistration:
- Any deviations from this plan will be documented and clearly labeled as such in the final paper.
- Additional analyses not described here will be explicitly labeled as exploratory/post-hoc.

---

## Filing instructions

**File this preregistration BEFORE generating stimuli or collecting data.**

Options:
1. **AsPredicted** (https://aspredicted.org/) — simple 8-question format, timestamped, free
2. **OSF Registries** (https://osf.io/registries) — more detailed, links to project, free

After filing, save the confirmation URL/DOI and include it in the manuscript's Methods section.

---

## Output for Step 4.4

Preregistration draft complete. Proceed to implementation planning.
