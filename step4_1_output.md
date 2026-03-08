# Step 4.1 Output: Goal and Hypotheses

Generated: 2026-03-05

---

## Research Goal

Determine how the choice of voice-cloning tool, lipsync tool, and their combination affects the perceived quality of talking-head videos, and whether this effect differs between neutral and emotional speech.

## Input Summary

**Research question (from Step 2.5):**
How does the choice of voice-cloning tool and lipsync tool — and their interaction — affect the perceived quality of talking-head videos, and does this effect differ between neutral and emotional speech?

**Standard metrics from literature (from Step 3.2):**
- Lip sync: LSE-C, LSE-D (standard but poorly correlated with humans, ρ = -0.164 and -0.269), LMD, AVSu/AVSm/AVSv (proposed replacements based on AV-HuBERT), WER
- Visual quality: FID (ρ = 0.210 with human preference), SSIM, PSNR, LPIPS, CPBD
- Voice quality: WavLM cosine similarity (speaker embedding), mel spectrogram similarity, pitch similarity
- THEval composite score achieves ρ = 0.870 with human preference (best validated)

**Typical sample sizes (from Step 3.2):**
- THEval: 17 models, 85,000 videos, 3,519 human ratings
- ICIP 2024: 4 methods, 15 participants, 2,700 human annotations (2AFC)
- ClonEval: 5 VC models, neutral + 6 emotions

**Existing datasets:**
- THEval (5,011 source videos, 1080p, multilingual)
- HDTF, VoxCeleb, LRS2/LRS3 (lip sync)
- MEAD, CREMA-D, RAVDESS (emotional speech)

---

## Hypotheses

### H1 — Main Effect of Voice Cloning Tool (VC main effect)
**Hypothesis:** The choice of voice-cloning system significantly affects the perceived quality of the final talking-head video, as measured by both computational metrics (speaker similarity, WER, mel spectrogram similarity) and human ratings.

**Rationale:** ClonEval (2025) showed large performance differences between 5 VC systems (e.g., WavLM cosine similarity ranges from 0.7170 for OuteTTS to 0.8226 for XTTS-v2). These quality differences in the audio should propagate to the final video.

### H2 — Main Effect of Lipsync Tool (Lipsync main effect)
**Hypothesis:** The choice of lipsync system significantly affects the perceived quality of the final talking-head video, as measured by both computational metrics (lip sync metrics, visual quality) and human ratings.

**Rationale:** THEval (2025) showed large performance variation across 17 lipsync models on multiple dimensions (quality, naturalness, synchronization).

### H3 — Interaction Effect (VC × Lipsync interaction) — PRIMARY
**Hypothesis:** The quality of combined VC + lipsync pipelines is not simply additive — specific tool pairings will show significant interaction effects. That is, a VC tool that works well with one lipsync tool may perform poorly with another.

**Rationale:** No prior work has tested this. The audio characteristics of different VC systems (prosody, spectral profile, artifacts) may interact with lipsync models differently — e.g., a lipsync model trained on clean speech may fail on VC output with artifacts, while another may be robust. AV-Deepfake1M++ used the factorial combination but never analyzed interaction effects.

### H4 — Emotion Degradation (Speech condition effect)
**Hypothesis:** Both computational metrics and human-perceived quality will be significantly lower for emotional speech than for neutral speech, across all VC × lipsync combinations.

**Rationale:** ClonEval found all 5 VC models were "most effective at cloning the neutral state" and "least effective at cloning highly expressive emotions such as fear, anger, and disgust" (WavLM similarity: neutral 0.7370–0.8480 vs fear 0.6953–0.7996). SyncNet is documented to be biased toward neutral faces (ECCV 2024). This degradation should compound across the pipeline.

### H5 — Emotion × Tool Interaction
**Hypothesis:** The magnitude of quality degradation from neutral to emotional speech differs across VC × lipsync combinations — some pipelines are more robust to emotional content than others.

**Rationale:** If VC systems differ in how well they preserve emotion (ClonEval showed this) and lipsync systems differ in how they handle emotional prosody, the interaction with speech condition should be non-uniform.

### H6 — Metric Validity (Computational vs. human correlation)
**Hypothesis:** Standard computational metrics (LSE-C, LSE-D, FID) will show weak-to-moderate correlation with human quality ratings for combined VC + lipsync pipelines, consistent with findings for lipsync-only systems (THEval: LSE-C ρ = -0.164, LSE-D ρ = -0.269, FID ρ = 0.210).

**Rationale:** THEval and ICIP 2024 documented poor correlation for lipsync-only evaluation. For combined pipelines with additional audio artifacts, the correlation may be even weaker. Newer metrics (AVSu/AVSm/AVSv, THEval composite) should correlate better.

---

## What a Positive Result Looks Like

1. **H3 confirmed (interaction):** A significant VC × lipsync interaction effect, meaning the "best" pipeline depends on the specific tool pairing, not just the individual tool quality. This is the primary novel contribution — it proves that benchmarking tools in isolation is insufficient.

2. **H4 confirmed (emotion degradation):** Emotional speech produces significantly lower quality than neutral speech. This validates Gap 3 and has direct practical implications for dubbing/avatar applications that require emotional expressiveness.

3. **H6 confirmed (metric validity):** Weak metric-human correlation for combined pipelines. This strengthens the argument that human evaluation is essential and that new composite metrics (like THEval's) should be adopted.

## What a Negative Result Would Mean

1. **H3 not confirmed (no interaction):** Quality is purely additive — the best VC + the best lipsync always produces the best result. **Still publishable:** This is the first empirical evidence of additivity, which simplifies tool selection for practitioners. The factorial benchmark itself is the contribution regardless of whether interaction exists.

2. **H4 not confirmed (no emotion degradation):** Modern tools handle emotional and neutral speech equally well. **Still publishable:** This contradicts ClonEval's findings and suggests rapid improvement in the field. Important for practitioners who can now trust these tools with emotional content.

3. **H6 not confirmed (metrics correlate well):** Standard metrics work fine for combined pipelines. **Still publishable:** This is good news for the field — automated evaluation is reliable and human studies may be unnecessary for routine benchmarking.

**Bottom line:** The factorial benchmark design ensures publishability regardless of which hypotheses are confirmed or rejected. The contribution is the benchmark itself; the specific findings are secondary.

---

## Priority Ordering

| Priority | Hypothesis | Novelty | Publishable if null? |
|----------|-----------|---------|---------------------|
| 1 (primary) | H3: VC × Lipsync interaction | Highest — never tested | Yes |
| 2 | H4: Emotion degradation | Medium — partially known for VC only | Yes |
| 3 | H1 + H2: Main effects | Expected — confirms prior work in new context | Yes |
| 4 | H5: Emotion × Tool interaction | High — never tested | Yes |
| 5 | H6: Metric validity | Medium — extends ICIP 2024 to combined pipelines | Yes |

---

## Output for Step 4.2

Hypotheses H1-H6 ready for operationalization into variables, conditions, and statistical tests.
