# Step 2.1 Output: Validated Gaps + Paper Collection

## Validated Gaps

### PRIMARY GAP (Gap 1) — OPEN
**Question:** "Has anyone systematically benchmarked multiple voice-cloning tools combined with multiple lipsync tools as end-to-end pipelines on the same stimuli?"

**Status:** OPEN. No paper benchmarks N voice-cloning x M lipsync tools as a factorial comparison. Lipsync and voice cloning are benchmarked separately. The closest paper (AV-Deepfake1M++) combines both but for detection purposes, not quality evaluation.

**Consensus confirmation (March 2026):** Confirmed OPEN. Consensus synthesized 20 sources and concluded: "A systematic, factorial benchmark that tests multiple voice-cloning tools combined with multiple lipsync tools on exactly the same audio-video stimuli with shared metrics does not appear in current research." A 2025 pipeline paper (arXiv 2509.12831) explicitly states that "very few works integrate voice cloning and lip-sync in a single pipeline."

### SECONDARY GAP A (Gap 3) — PARTIALLY FILLED
**Question:** "Has anyone systematically measured whether lipsync and voice-cloning pipelines produce lower-quality output for emotional speech compared to neutral speech, using the same systems and stimuli?"

**Status:** PARTIALLY FILLED. Voice cloning side partially covered by ClonEval (2025). Lipsync side has scattered incidental evidence but no dedicated study. SyncNet is documented to be biased toward neutral faces (ECCV 2024).

### SECONDARY GAP B (Gap 5) — PARTIALLY FILLED (leaning OPEN)
**Question:** "Has anyone tested whether humans can detect mismatches between the emotion conveyed by a cloned voice and the emotion shown by generated facial expressions in talking-head videos?"

**Status:** PARTIALLY FILLED leaning OPEN. Adjacent work exists from 2008-2009 (simple animations) and in automated detection (Mittal et al. 2020), but the specific intersection of cloned voice + generated face + human emotion mismatch perception has not been tested.

### SUPPORTING ANGLE (Gap 2) — NOT A STANDALONE GAP
**Question:** "Do computational quality metrics predict human-perceived realism across combined voice-cloning + lipsync pipelines?"

**Status:** The basic question (metrics vs. human judgment) is PARTIALLY FILLED to CLOSED for lipsync-only systems. But no study validates metric rankings for *combined* VC + lipsync pipelines. Use this as a secondary contribution within Gap 1, not as a main gap.

---

## Paper Collection

### A. Papers about lipsync benchmarking (for methodology + metrics)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| A1 | THEval: Evaluation Framework for Talking Head Video Generation | 2025 | arXiv 2511.04520 | Benchmarks 17 models, defines 8 evaluation metrics, achieves 0.870 Spearman with human ratings. **Use for: choosing which computational metrics to adopt.** |
| A2 | OmniSync / AIGC-LipSync Benchmark | 2025 | NeurIPS 2025 Spotlight (arXiv 2505.21448) | Establishes a lipsync benchmark on AI-generated content. **Use for: benchmark methodology reference.** |
| A3 | "Wild West" of Evaluating Speech-Driven 3D Facial Animation | 2025 | Computer Graphics Forum (DOI: 10.1111/cgf.70073) | Shows model rankings don't generalize across datasets, subjective vs. objective metrics diverge. **Use for: motivating the need for human evaluation.** |
| A4 | MuseTalk | 2024 | arXiv 2410.10122 | Benchmarks against Wav2Lip, VideoReTalking, TalkLip, DINet. **Use for: comparison methodology and as a candidate lipsync tool.** |
| A5 | LatentSync | 2024 | arXiv 2412.09262 | Benchmarks against Wav2Lip, VideoReTalking, DINet, MuseTalk. **Use for: comparison methodology and as a candidate lipsync tool.** |
| A6 | "All's Well That FID's Well?" | 2025 | Electronics 14(17):3487 | Shows FID fails to capture local artifacts in lipsync. **Use for: justifying why you need human evaluation beyond metrics.** |

### B. Papers about voice cloning benchmarking (for methodology + metrics)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| B1 | ClonEval: An Open Voice Cloning Benchmark | 2025 | arXiv 2504.20581 | Benchmarks 5 VC systems (XTTS-v2, SpeechT5, VALL-E X, WhisperSpeech, OuteTTS) on neutral + emotional datasets. **Use for: VC benchmark methodology, emotional vs. neutral data, and as reference for VC tool selection.** |
| B2 | RVCBench: Benchmarking Robustness of Voice Cloning | 2026 | arXiv 2602.00443 | 11 VC models across 10 robustness tasks. Notes emotion degrades cloning. **Use for: VC robustness context and tool selection.** |
| B3 | EmergentTTS-Eval | 2025 | NeurIPS 2025 (arXiv 2505.23009) | Benchmarks 12+ TTS systems on 6 dimensions including emotions. **Use for: audio evaluation methodology, emotion-specific metrics.** |

### C. Papers about metrics vs. human perception (for supporting angle)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| C1 | Comparative Study of Perceptual Quality Metrics for Talking Head Videos | 2024 | IEEE ICIP 2024 (arXiv 2403.06421) | Finds LSE-C/LSE-D correlate poorly with human preferences. **Use for: motivating human evaluation, citing known metric limitations.** |
| C2 | PEAVS: Perceptual Evaluation of Audio-Visual Synchrony | 2024 | ECCV 2024 (arXiv 2404.07336) | Reference-free metric achieving 0.79 Pearson with human labels. **Use for: potentially adopting PEAVS as one of your computational metrics.** |
| C3 | THQA: Perceptual Quality Assessment Database for Talking Heads | 2024 | ICIP 2024 (arXiv 2404.09003) | 800 videos, 8 methods, human annotations. **Use for: methodology reference for human evaluation design.** |

### D. Papers about emotional talking heads (for Gap 3 context)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| D1 | Stabilized Synchronization Loss (ECCV 2024) | 2024 | ECCV 2024 (arXiv 2307.09368) | Documents SyncNet's bias toward neutral faces. **Critical: explains why standard lipsync metrics may unfairly penalize emotional content.** |
| D2 | MEAD: Large-Scale AV Dataset for Emotional Talking-Face | 2020 | ECCV 2020 | 60 actors, 8 emotions, 3 intensities. **Use for: potential reference dataset, emotional speech stimuli context.** |
| D3 | EAT: Efficient Emotional Adaptation (ICCV 2023) | 2023 | ICCV 2023 | Emotion adapters for talking heads, eval on MEAD with lipsync and emotion accuracy. **Use for: related work on emotional talking heads.** |
| D4 | EDTalk (ECCV 2024 Oral) | 2024 | ECCV 2024 | Disentangled emotional talking heads, multi-system comparison on MEAD. **Use for: related work, comparison methodology.** |
| D5 | EmoTalker (ACCV 2024) | 2024 | ACCV 2024 | Audio-driven emotion-aware generation evaluated on MEAD. **Use for: related work.** |
| D6 | EmoKnob (EMNLP 2024) | 2024 | EMNLP 2024 (arXiv 2410.00316) | Shows WER/similarity degrade with emotion intensity in VC. **Use for: supporting evidence for Gap 3 motivation.** |
| D7 | EmoDubber (CVPR 2025) | 2024 | CVPR 2025 (arXiv 2412.08988) | Emotion-controllable dubbing with neutral vs. emotional comparisons. **Use for: related work on emotional AV content.** |

### E. Papers about emotion congruence / cross-modal perception (for Gap 5 context)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| E1 | Mittal et al. "Emotions Don't Lie" | 2020 | ACM MM 2020 (arXiv 2003.06711) | Automated detection via AV emotion mismatch. 73.2% of fakes have mismatched emotion. **Use for: motivating that emotion mismatch exists in synthetic AV content.** |
| E2 | Mower et al. | 2008/2009 | IEEE ICME 2008, IEEE TMM 2009 | Human perception of conflicting AV emotion in synthetic characters. Audio dominates during conflict. **Use for: theoretical grounding of the congruence question.** |
| E3 | Zhang et al. "Emotionally Controllable Talking Face" | 2022 | MDPI Applied Sciences 2022 | Includes small user study with mismatched AV emotion videos. **Use for: closest prior work to cite and extend.** |
| E4 | Lee "Detecting Deepfakes Through Emotion?" | 2025 | Applied Cognitive Psychology 2025 | Deepfakes show lower emotional intensity, affects credibility. **Use for: related work on emotion in deepfake perception.** |
| E5 | Salehi et al. "From Flat to Feeling" | 2025 | Frontiers in Computer Science 2025 | Human study (N=70) on dynamic emotions in AI avatars. **Use for: methodology reference for human evaluation of emotional AV content.** |

### F. Papers about combined pipelines (closest to Gap 1)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| F1 | AV-Deepfake1M++ | 2025 | ACM MM 2025 (arXiv 2507.20579) | Uses 5 TTS + 3 lipsync tools to create detection dataset. **Closest existing work to your design — cite and differentiate (their goal is detection, yours is quality).** |
| F2 | Lightweight Pipeline (Tortoise + Wav2Lip) | 2025 | arXiv 2509.12831 | Single combined pipeline for noisy environments. **Use for: related work showing combined pipelines exist but aren't benchmarked.** |
| F3 | Real-Time Lip-Sync with AI-Driven Voice Cloning | 2025 | IEEE (DOI: 10.1109/11167849) | Single integrated system for Arabic video translation. **Use for: related work.** |
| F4 | Face-Dubbing++: Lip-Synchronous, Voice Preserving Translation of Videos | 2022 | IEEE ICASSP 2023 | Voice-preserving video translation with integrated lipsync. Single architecture, user study. **Use for: related work, another combined pipeline example.** |
| F5 | VisualTTS: TTS with Accurate Lip-Speech Synchronization for Automatic Voice Over | 2021 | ICASSP 2022 | TTS model designed for lip-speech sync in voice-over. **Use for: related work on joint audio-visual synthesis.** |

### G. Surveys (for Introduction / Related Work context)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| G1 | Advancing Talking Head Generation: A Comprehensive Survey | 2025 | arXiv 2507.02900 | Spans 2017-2025, 10 THG paradigms. **Use for: Introduction, situating your work in the broader field.** |
| G2 | Voice Cloning: Comprehensive Survey | 2025 | arXiv 2505.00579 | Surveys VC methods and evaluation. **Use for: Introduction, VC landscape.** |
| G3 | From Pixels to Portraits (talking head survey) | 2023 | arXiv 2308.16041 | Comprehensive survey of THG techniques. **Use for: related work.** |
| G4 | A Survey of Audio Synthesis and Lip-syncing for Synthetic Video Generation | 2021 | EAI Endorsed Trans. Creative Technologies | Reviews both VC and lipsync methods, notes they are studied separately. **Use for: related work, citable evidence of the fragmentation.** |
| G5 | Deepfake Generation and Detection: A Benchmark and Survey | 2024 | arXiv 2403.17881 | Covers face swapping, reenactment, talking face, attribute editing + detection. Unified metrics. **Use for: broader context in Introduction.** |
| G6 | Audio-Driven Facial Animation with Deep Learning: A Survey | 2024 | MDPI Information 15(11):675 | Identifies "disentangling lip sync and emotions" as a key open challenge. **Use for: Gap 3 motivation, metrics reference (LSE-D, LVE, LRA).** |
| G7 | Multilingual Video Dubbing: A Technology Review and Current Challenges | 2023 | Frontiers in Signal Processing (DOI: 10.3389/frsip.2023.1230755) | Taxonomizes the full dubbing pipeline (ASR→MT→TTS→VC→lipsync). Notes voice actors must portray emotional range. **Use for: related work, pipeline context.** |

### H. Candidate lipsync/VC tools (from Consensus results — useful for your pipeline selection in Step 4)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| H1 | Wav2Lip: A Lip Sync Expert Is All You Need | 2020 | ACM MM 2020 | 1012 citations. Dominant lipsync baseline. **Candidate for your pipeline.** |
| H2 | Diff2Lip: Audio Conditioned Diffusion Models for Lip-Sync | 2023 | WACV 2024 | Diffusion-based lipsync, outperforms Wav2Lip. **Candidate for your pipeline.** |
| H3 | StyleSync: High-Fidelity Generalized Lip Sync | 2023 | CVPR 2023 | Style-based lipsync, 96 citations. **Candidate for your pipeline.** |
| H4 | FluentLip: Phonemes-Based Two-stage Lip Synthesis | 2025 | arXiv 2025 | Recent lipsync with optical flow consistency. **Candidate for your pipeline.** |
| H5 | M2VoC: Multi-Speaker Multi-Style Voice Cloning Challenge | 2021 | ICASSP 2021 | Voice cloning challenge with standardized evaluation. **Use for: VC evaluation methodology.** |

### I. Papers found via terminology expansion (Step 2.2 Part A)

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| I1 | VOX-DUB: AI Dubbing Benchmark | 2025 | Toloka (HuggingFace: toloka/VOX-DUB) | First open human-evaluated dubbing benchmark. 30,240 human judgments on 4 commercial systems. Finds expressiveness introduces audio artifacts. **Use for: Gap 3 evidence (audio side), human eval methodology.** |
| I2 | Faces that Speak: Jointly Synthesising Talking Face and Speech from Text | 2024 | CVPR 2024 (arXiv 2405.10272) | First unified framework jointly generating face video + speech from text. **Use for: closest prior work to combined synthesis, cite as evidence the field is moving toward integration but lacks benchmarks.** |
| I3 | AV-HuBERT Expert for Enhanced THG Evaluation | 2024 | CVPR 2024 Workshop (arXiv 2405.04327) | Proposes AVSu, AVSm, AVSv metrics to replace SyncNet-based LSE-C/LSE-D. **Use for: potentially better lipsync metrics for your benchmark.** |
| I4 | EMO: Emote Portrait Alive | 2024 | ECCV 2024 (arXiv 2402.17485) | Introduces E-FID (Expression-FID) metric, now widely adopted. **Use for: E-FID as a computational metric for expressiveness.** |
| I5 | VASA-1: Lifelike Audio-Driven Talking Faces | 2024 | NeurIPS 2024 Oral (arXiv 2404.10667) | Introduces CAPP metric (audio-pose alignment). **Use for: novel metric for your benchmark.** |
| I6 | Loopy: Taming Audio-Driven Portrait Avatar | 2025 | ICLR 2025 Oral (arXiv 2409.02634) | Tested on RAVDESS (emotional). User study includes "audio-emotion matching" criterion. **Use for: Gap 5 partial evidence, user study methodology.** |
| I7 | MoEE: Mixture of Emotion Experts | 2025 | arXiv 2501.01808 | Decouples 6 emotions for compound emotional states. New dataset DH-FaceEmoVid-150. **Use for: Gap 5 context, multi-modal emotion alignment.** |
| I8 | DeepDubber-V1 | 2025 | arXiv 2503.23660 | Multimodal LLM-guided dubbing. Introduces EMO-SIM and SPK-SIM metrics. **Use for: metrics for emotion and speaker similarity.** |
| I9 | AUHead: Realistic Emotional Talking Head via Action Units | 2026 | arXiv 2602.09534 | Most recent. Benchmarks 10+ methods on MEAD and CREMA. Uses ACCemo metric. **Use for: latest MEAD benchmark comparison, related work.** |
| I10 | FlowVQTalker: Emotional Talking Face via Normalizing Flow | 2024 | CVPR 2024 (arXiv 2403.06375) | Introduces AccEmo metric. Compares 9 methods on MEAD. **Use for: AccEmo metric, MEAD comparison methodology.** |
| I11 | DisFlowEm: One-Shot Emotional Talking Head | 2025 | WACV 2025 | Disentangled optical flow for emotion. Tested on MEAD + CREMA-D. **Use for: cross-dataset emotional evaluation reference.** |

### J. Papers found via citation graphs (Step 2.2 Part B — Inciteful)

| # | Paper | Year | Venue | Seed paper | Why it matters for your work |
|---|---|---|---|---|---|
| J1 | MagicTalk: Implicit and Explicit Correlation Learning for Diffusion-based Emotional Talking Face Generation | 2025 | Computational Visual Media 11(4):763-779 | Stabilized Sync Loss | Emotional talking face via diffusion. Models both implicit (emotion style) and explicit (lip-audio) correlations. Compares against EAMM, PD-FGC, EVP. **Use for: Gap 3 related work, diffusion-based emotional generation.** |
| J2 | ReSyncer: Rewiring Style-based Generator for Unified Audio-Visually Synced Facial Performer | 2024 | ECCV 2024 (arXiv 2408.03284) | ICIP 2024 metric comparison | Unified StyleGAN-based lipsync framework supporting lip-sync, style transfer, and face swapping. Trained on HDTF + VoxCeleb2. **Use for: lipsync comparison reference, related work.** |
| J3 | SyncTalk: The Devil is in the Synchronization for Talking Head Synthesis | 2024 | CVPR 2024 (arXiv 2311.17590) | Stabilized Sync Loss | NeRF-based talking head focusing on sync across face, head, and portrait. Outperforms SoTA in synchronization. **Use for: related work on sync-focused generation.** |
| J4 | F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching | 2025 | ACL 2025 (arXiv 2410.06885) | AV-Deepfake1M++ | Non-autoregressive TTS via flow matching + DiT. Zero-shot voice cloning capable. **Use for: potential VC tool candidate, related TTS work.** |

**Note:** THEval and ClonEval had no Inciteful graphs (too new, 0 citations indexed). AV-Deepfake1M++ graph was mostly deepfake detection papers.

### G (continued). Surveys found via citation graphs

| # | Paper | Year | Venue | Why it matters for your work |
|---|---|---|---|---|
| G8 | Deep Learning for Visual Speech Analysis: A Survey | 2024 | IEEE TPAMI (arXiv 2205.10839) | Covers visual speech recognition and generation as dual problems. Comprehensive benchmark datasets and method taxonomy. **Use for: Introduction, broader field context.** |
| G9 | Talking Human Face Generation: A Survey (Toshpulatov et al.) | 2023 | Expert Systems with Applications 219:119678 | Covers CNNs, GANs, NeRF for talking face. ~178 citations. **Use for: Introduction, well-cited survey for situating your work.** |

---

## Consolidated Metrics Inventory

Based on all papers found, here are the computational metrics relevant to your benchmark, organized by what they measure:

### Voice / Audio Quality
| Metric | What it measures | Source paper | Notes |
|---|---|---|---|
| MOS (human) | Subjective naturalness/quality | Standard | Gold standard but expensive |
| WER | Word error rate / intelligibility | Standard | Via ASR system on generated audio |
| MCD | Mel Cepstral Distortion | EmoDubber (2025) | Lower = closer to reference audio |
| PESQ | Perceptual speech quality | ITU standard | Telecom-originated, widely used |
| SPK-SIM / SECS | Speaker identity similarity | DeepDubber-V1, EmoDubber | Cosine similarity of speaker embeddings |
| WavLM cosine sim | Speaker identity preservation | ClonEval (2025) | More robust than older speaker encoders |

### Emotion in Voice
| Metric | What it measures | Source paper | Notes |
|---|---|---|---|
| EMO-SIM | Emotion similarity to reference | DeepDubber-V1 (2025) | Cosine similarity of emotion embeddings |
| Per-emotion accuracy | Emotion classification accuracy on cloned audio | ClonEval (2025) | Using pre-trained emotion classifier |

### Lipsync Quality
| Metric | What it measures | Source paper | Notes |
|---|---|---|---|
| LSE-C / LSE-D | Audio-lip sync confidence/distance | Wav2Lip (2020), standard | **Known to correlate poorly with human judgment (ICIP 2024). Biased toward neutral faces (ECCV 2024).** |
| AVSu / AVSm / AVSv | AV sync via AV-HuBERT | Yaman et al. (CVPR 2024W) | Proposed replacement for SyncNet-based metrics |
| PEAVS | Perceptual AV synchrony (1-5 scale) | ECCV 2024 | 0.79 Pearson with human labels. Best validated sync metric. |
| M-LMD / F-LMD | Mouth/face landmark distance to ground truth | Standard | Measures geometric accuracy of lip shape |

### Visual Quality
| Metric | What it measures | Source paper | Notes |
|---|---|---|---|
| FID | Image distribution quality | Standard | **Known to miss local lipsync artifacts ("All's Well That FID's Well", 2025)** |
| FVD | Video distribution quality | Standard | Temporal extension of FID |
| SSIM / PSNR | Pixel-level quality | Standard | Basic quality, doesn't capture perceptual quality well |
| LPIPS | Perceptual image similarity | Standard | Better than SSIM for perceptual quality |
| CPBD | Cumulative probability of blur detection | FlowVQTalker (2024) | Detects blurriness in generated faces |
| CSIM | Identity preservation (cosine sim of face embeddings) | Standard | Via ArcFace or similar |

### Emotion in Face
| Metric | What it measures | Source paper | Notes |
|---|---|---|---|
| AccEmo | Emotion classification accuracy on generated face | FlowVQTalker (2024), AUHead (2026) | Pre-trained emotion classifier on generated frames |
| E-FID | Expression-FID, expressiveness quality | EMO (ECCV 2024) | Now widely adopted for expressive talking heads |

### Combined / Cross-modal
| Metric | What it measures | Source paper | Notes |
|---|---|---|---|
| CAPP | Audio-pose alignment (CLIP-inspired) | VASA-1 (NeurIPS 2024) | Novel, measures how well head motion matches audio |
| THEval composite | Combined 8-metric score | THEval (2025) | 0.870 Spearman with human ratings across 17 models |

### Key warnings about metrics
- **LSE-C/LSE-D:** Still widely reported but correlate poorly with human perception and are biased toward neutral speech. Report them for comparability but don't rely on them alone.
- **FID:** Fails to capture local lipsync artifacts. Useful for global image quality but not lipsync-specific.
- **PEAVS:** Best validated perceptual sync metric. Consider adopting.
- **AVSu/AVSm/AVSv:** Newer, AV-HuBERT-based alternatives to SyncNet. Worth evaluating.

---

## Total: ~55 unique papers

- Papers to read in full (most critical): A1, B1, C1, D1, F1, I2, I3 (7 papers)
- Papers to read abstract/methods: A2-A6, B2-B3, C2-C3, D2-D7, E1-E5, F4-F5, I1, I4-I11, J1-J3 (~33 papers)
- Papers to skim/cite: F2-F3, G1-G9 (~11 papers)
- Tool candidates to check: H1-H5, J4 (for pipeline selection later)
