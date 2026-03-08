# Step 2.3 Output: Methods and Metrics Extraction

Generated: 2026-03-03

**Source:** Abstracts via Semantic Scholar API + detailed notes from Step 2.1 output.
**Note:** This extraction is abstract-level. Rows marked with (!) need verification against the full PDF once imported into Zotero. The pipeline recommends reading these 7 papers in full.

---

## Comparison Table

| Paper (author, year) | Publication status | Method/approach | Dataset | Computational metrics | Effect sizes reported | Human evaluation method | Sample size | Key finding |
|---|---|---|---|---|---|---|---|---|
| **A1.** Quignon et al., 2025 (THEval) | arXiv preprint | Evaluation framework: 8 metrics across quality, naturalness, synchronization. Benchmarks 17 SOTA talking head models. | Custom curated real dataset (bias-mitigated); 85,000 generated videos | Quality (FID, CPBD), naturalness (head motion, eyebrow dynamics), sync (LSE-C/LSE-D + proposed metrics) | 0.870 Spearman correlation between composite metric and human ratings | User study (details in paper) (!) | 85,000 videos, 17 models | Many algorithms excel in lip sync but struggle with expressiveness and artifact-free details. Proposed composite metric achieves high human alignment. |
| **B1.** Christop et al., 2025 (ClonEval) | arXiv preprint | Open benchmark for voice cloning TTS: evaluation protocol + open-source library + leaderboard. Tests 5 VC systems. | Neutral + emotional speech datasets (!) | WavLM cosine similarity (speaker), per-emotion accuracy, WER (!) | Not in abstract — check paper (!) | Not mentioned in abstract (!) | 5 models (XTTS-v2, SpeechT5, VALL-E X, WhisperSpeech, OuteTTS) | Standardized VC benchmark; finds emotion degrades cloning quality. Limited to 5 models and quality-centric metrics (limitation noted by RVCBench). |
| **C1.** Zhang et al., 2024 (ICIP 2024) | IEEE ICIP 2024 | Comparative study: tests correlation between computational metrics and human perception for talking head videos. | Videos from 4 generative methods (!) | LSE-C, LSE-D, FID, SSIM, PSNR, LPIPS + others (!) | Correlation coefficients between metrics and human scores (!) | Controlled psychophysical experiments on: visual quality, lip-audio sync, head movement naturalness | 4 methods compared (!) | LSE-C/LSE-D correlate poorly with human preferences. Identifies metrics that align better with human opinion. Code/data released. |
| **D1.** Yaman et al., 2023/2024 (ECCV 2024) | ECCV 2024 | Stabilized synchronization loss + AVSyncNet. Silent-lip generator to fix lip leaking from identity reference. Proposes improved training loss for lip sync. | Not specified in abstract — likely VoxCeleb/HDTF (!) | SyncNet scores, proposed stabilized sync loss, visual quality metrics (!) | Not in abstract (!) | Not mentioned in abstract — ablation study validates contributions (!) | Not specified (!) | SyncNet is biased toward neutral faces. Standard lip-sync loss causes training instability. Proposed stabilized loss + AVSyncNet outperform SOTA in visual quality and lip sync. |
| **F1.** Cai et al., 2025 (AV-Deepfake1M++) | ACM MM 2025 | Large-scale dataset generation: combines 5 TTS + 3 lipsync tools with audio-visual perturbations for deepfake detection benchmark. | AV-Deepfake1M extension; 2M video clips | Detection metrics (AUC, accuracy) — not generation quality metrics (!) | Not in abstract (!) | Not mentioned — focus is on detection benchmarking (!) | 2M video clips, 5 TTS systems, 3 lipsync methods | Closest to your pipeline design (factorial TTS x lipsync). But goal is detection, not quality evaluation. Perturbation strategies simulate real-world degradation. |
| **I2.** Jang et al., 2024 (CVPR 2024) | CVPR 2024 | Unified framework: jointly generates talking face + speech from text. Motion sampler via conditional flow matching. Novel TTS conditioning using motion-removed features. | Not specified in abstract (!) | Not specified in abstract — likely FID, sync metrics, speech quality (!) | Not in abstract (!) | Not mentioned in abstract (!) | Generalizes to unseen identities (!) | First multimodal synthesis system jointly generating face video + speech from text. Evidence the field is moving toward integration but lacks benchmarks. |
| **I3.** Yaman et al., 2024 (CVPR 2024W) | IEEE CVPRW 2024 | Uses AV-HuBERT (audio-visual speech representation expert) as loss function during training AND as basis for 3 new evaluation metrics (AVSu, AVSm, AVSv). | Not specified in abstract (!) | AVSu (sync utterance), AVSm (sync mouth), AVSv (sync viseme) — proposed to replace SyncNet-based LSE-C/LSE-D | Not in abstract (!) | Not mentioned in abstract (!) | Not specified (!) | AV-HuBERT features improve lip sync training and provide more robust evaluation metrics than SyncNet. Ablation study validates effectiveness. |

---

## Summary of Standard Practices Across Papers

### Metrics commonly used
- **Lip sync:** LSE-C, LSE-D (standard but poorly correlated with humans), AVSu/AVSm/AVSv (proposed replacement), PEAVS (best validated)
- **Visual quality:** FID (standard but misses local artifacts), SSIM, PSNR, LPIPS, CPBD
- **Voice quality:** WavLM cosine sim, WER, MCD, PESQ
- **Emotion:** AccEmo, E-FID, EMO-SIM, per-emotion accuracy
- **Identity:** CSIM (ArcFace cosine sim)

### Datasets commonly used
- VoxCeleb, HDTF, LRS2/LRS3 (lip sync)
- MEAD, CREMA-D, RAVDESS (emotional)
- Custom curated datasets (THEval, AV-Deepfake1M++)

### Human evaluation approaches
- MOS (mean opinion score) — standard but expensive
- Controlled psychophysical experiments (C1)
- User studies with specific criteria (lip sync, naturalness, expressiveness)
- A/B preference tests

### Typical sample sizes
- 4-17 models compared per study
- Thousands to millions of generated videos for automated metrics
- Human studies: specific N not found in abstracts — needs PDF verification (!)

### Key gap confirmed
No paper benchmarks multiple VC tools x multiple lipsync tools as a factorial quality comparison on the same stimuli. F1 does the factorial combination but measures detection, not quality. A1 benchmarks 17 lipsync models but with no VC component. B1 benchmarks 5 VC models but with no lipsync component.

---

## Items requiring full-PDF verification

The following were not extractable from abstracts alone. Read the PDFs in Zotero to complete:

1. **B1 (ClonEval):** Exact datasets used, full metric list, whether human evaluation was included
2. **C1 (ICIP 2024):** Which 4 generative methods, exact correlation values, sample sizes
3. **D1 (Stabilized Sync Loss):** Dataset used, specific metrics reported, quantitative results
4. **F1 (AV-Deepfake1M++):** Which 5 TTS and 3 lipsync tools specifically, any quality metrics beyond detection
5. **I2 (Faces that Speak):** Datasets, metrics, quantitative results
6. **I3 (AV-HuBERT):** Dataset, quantitative comparison of AVS metrics vs. SyncNet metrics
7. **All papers:** Exact human study sample sizes, effect sizes, statistical tests used
