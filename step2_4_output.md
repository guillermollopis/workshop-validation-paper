# Step 2.4 Output: Citation Context and Limitations

Generated: 2026-03-03 14:16

---

## A1: THEval (2025)

**Why top 5:** Benchmarks 17 lipsync models with 8 metrics, 0.870 Spearman with human ratings

**Total citations:** 1

**Citations analyzed:** 1

**Influential citations:** 0


### Limitations and criticisms (0 citing papers)

No critical/contrastive citations found.

---

## B1: ClonEval (2025)

**Why top 5:** Benchmarks 5 VC systems on neutral + emotional datasets

**Total citations:** 2

**Citations analyzed:** 2

**Influential citations:** 1


### Limitations and criticisms (1 citing papers)

- **RVCBench: Benchmarking the Robustness of Voice Cloning Across Modern Audio Generation Models** (2026) arXiv:2602.00443
  - *Influential citation*
  - > "(1) VC benchmarks (e.g., CloneEval (Christop et al., 2025; Manku et al., 2025)) standardize comparisons of VC models, but are largely quality-centric under clean settings, with limited model coverage and metrics that prioritize utility over robustness failure modes (e.g., audio/text shifts or…"
  - > "(1) VC benchmarks (e.g., CloneEval (Christop et al., 2025; Manku et al., 2025)) standardize comparisons of VC models, but are largely quality-centric under clean settings, with limited model coverage and metrics that prioritize utility over robustness failure modes (e.g., audio/text shifts or long-form identity drift)."
  - > "VC and speech-synthesis benchmarks (e.g., CloneEval (Christop et al., 2025), EmergentTTS-Eval (Manku et al., 2025)) standardize mostly curated, quality-centric evaluation; CloneEval cov-2 ers limited VC models and metrics, while EmergentTTS-Eval targets TTS prompt-following rather than reference-conditioned identity preservation."

---

## C1: Perceptual Quality Metrics for TH Videos (ICIP 2024)

**Why top 5:** Shows LSE-C/LSE-D correlate poorly with human preferences

**Total citations:** 8

**Citations analyzed:** 8

**Influential citations:** 0


### Limitations and criticisms (1 citing papers)

- **Comparative Study of Digital Sibling Video AI Platform** (2025) DOI:10.1109/MetaCom65502.2025.00012
  - > "The first study by Zhang et al. focuses on the limitations of evaluating Artificial Intelligence Generated Content (AIGC), particularly for audio-driven talking head or portrait animation video generation [10]."

---

## D1: Stabilized Sync Loss (ECCV 2024)

**Why top 5:** Documents SyncNet bias toward neutral faces

**Total citations:** 14

**Citations analyzed:** 14

**Influential citations:** 2


### Limitations and criticisms (3 citing papers)

- **A Lightweight Pipeline for Noisy Speech Voice Cloning and Accurate Lip Sync Synthesis** (2025) DOI:10.48550/arXiv.2509.12831
  - > "…are standardized measures of evaluation used in speech synthesis and audio-visual dubbing research, which includes metrics such as Mean Opinion Score (MOS)[5] and SyncNet-based lip-sync confidence scoring [13], although we did not compute formal MOS because our study only elements a single subject."

- **Mask-Free Audio-driven Talking Face Generation for Enhanced Visual Quality and Identity Preservation** (2025) DOI:10.48550/arXiv.2507.20953
  - *Influential citation*
  - > "(3) The identity reference can undesirably influence the model, leading to issues like lip leaking [12, 63, 94], where the model occasionally copies the lip shape of the identity reference although it is unaligned with the audio, both in training and inference."

- **FaceEditTalker: Controllable Talking Head Generation with Facial Attribute Editing** (2025) arXiv:2505.22141
  - > "However, most existing approaches primarily focus on lip synchronization [1]–[3], [10], [11] and emotional expression [12]–[17], while largely overlooking the important functionality of controllable facial attribute editing."

---

## F1: AV-Deepfake1M++ (ACM MM 2025)

**Why top 5:** Uses 5 TTS + 3 lipsync tools — closest to your pipeline design

**Total citations:** 7

**Citations analyzed:** 7

**Influential citations:** 1


### Limitations and criticisms (1 citing papers)

- **SGS: Segmentation-Guided Scoring for Global Scene Inconsistencies** (2025) DOI:10.48550/arXiv.2509.26039
  - > "AV-Deepfake++ [2] and MFND [17] on the other hand introduced audiovisual components to enable the detection of deepfakes that manipulate both video and sound, in addition to expanded fake news detection scenarios."


### Future work mentions (1 citing papers)

- **LayLens: Improving Deepfake Understanding through Simplified Explanations** (2025)
  - > "As a future work, we will develop an open-source, efficient and explainable model for large-scale audio-visual deepfakes [3] and further, extend it to incorporate multi-lingual, code-switched videos [6]."

---

## Summary for Step 2.5

### Consolidated limitations

- **About ClonEval (2025)** (from RVCBench: Benchmarking the Robustness of Voice Cloning Across Modern Audio Generation Models, 2026):
  > "(1) VC benchmarks (e.g., CloneEval (Christop et al., 2025; Manku et al., 2025)) standardize comparisons of VC models, but are largely quality-centric under clean settings, with limited model coverage and metrics that prioritize utility over robustness failure modes (e.g., audio/text shifts or…"

- **About ClonEval (2025)** (from RVCBench: Benchmarking the Robustness of Voice Cloning Across Modern Audio Generation Models, 2026):
  > "VC and speech-synthesis benchmarks (e.g., CloneEval (Christop et al., 2025), EmergentTTS-Eval (Manku et al., 2025)) standardize mostly curated, quality-centric evaluation; CloneEval cov-2 ers limited VC models and metrics, while EmergentTTS-Eval targets TTS prompt-following rather than reference-con"

- **About ClonEval (2025)** (from RVCBench: Benchmarking the Robustness of Voice Cloning Across Modern Audio Generation Models, 2026):
  > "CloneEval (Christop et al., 2025), for example, reports results for a small set of open-weight VC systems (five models: OuteTTS, SpeechT5, VALL-E X, WhisperSpeech, and XTTS-v2) and ranks them primarily using cosine similarity between WavLM speaker embeddings, with auxiliary analysis based on cosine "

- **About Perceptual Quality Metrics for TH Videos (ICIP 2024)** (from Comparative Study of Digital Sibling Video AI Platform, 2025):
  > "The first study by Zhang et al. focuses on the limitations of evaluating Artificial Intelligence Generated Content (AIGC), particularly for audio-driven talking head or portrait animation video generation [10]."

- **About Stabilized Sync Loss (ECCV 2024)** (from A Lightweight Pipeline for Noisy Speech Voice Cloning and Accurate Lip Sync Synthesis, 2025):
  > "…are standardized measures of evaluation used in speech synthesis and audio-visual dubbing research, which includes metrics such as Mean Opinion Score (MOS)[5] and SyncNet-based lip-sync confidence scoring [13], although we did not compute formal MOS because our study only elements a single subject."

- **About Stabilized Sync Loss (ECCV 2024)** (from Mask-Free Audio-driven Talking Face Generation for Enhanced Visual Quality and Identity Preservation, 2025):
  > "(3) The identity reference can undesirably influence the model, leading to issues like lip leaking [12, 63, 94], where the model occasionally copies the lip shape of the identity reference although it is unaligned with the audio, both in training and inference."

- **About Stabilized Sync Loss (ECCV 2024)** (from FaceEditTalker: Controllable Talking Head Generation with Facial Attribute Editing, 2025):
  > "However, most existing approaches primarily focus on lip synchronization [1]–[3], [10], [11] and emotional expression [12]–[17], while largely overlooking the important functionality of controllable facial attribute editing."

- **About AV-Deepfake1M++ (ACM MM 2025)** (from SGS: Segmentation-Guided Scoring for Global Scene Inconsistencies, 2025):
  > "AV-Deepfake++ [2] and MFND [17] on the other hand introduced audiovisual components to enable the detection of deepfakes that manipulate both video and sound, in addition to expanded fake news detection scenarios."

### New papers discovered (add to collection)

No new highly-cited papers found via citation analysis.
