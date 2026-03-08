# Step 3.2: NotebookLM Questions

## Setup

1. Go to https://notebooklm.google/
2. Create a new notebook called "Workshop Validation Paper"
3. Upload PDFs of these 7 "read in full" papers (from Zotero):
   - A1: THEval (arXiv 2511.04520)
   - B1: ClonEval (arXiv 2504.20581)
   - C1: Perceptual Quality Metrics (arXiv 2403.06421)
   - D1: Stabilized Sync Loss (arXiv 2307.09368)
   - F1: AV-Deepfake1M++ (arXiv 2507.20579)
   - I2: Faces that Speak (arXiv 2405.10272)
   - I3: AV-HuBERT metrics (arXiv 2405.04327)
4. Also upload `step2_3_output.md` (your comparison table)

## Questions to ask (copy-paste these one by one)

### For Step 4 — Experimental Design

```
What exact computational metrics did each of these papers use to evaluate lip synchronization quality? List every metric name, what it measures, and which paper used it.
```

```
What exact computational metrics did each of these papers use to evaluate voice/audio quality? List every metric name, what it measures, and which paper used it.
```

```
What human evaluation methods did these papers use? For each paper that included a human study: what was the study design (MOS, A/B preference, Likert scale, etc.), how many participants, and what did they ask participants to judge?
```

```
What datasets did each paper use for evaluation? For each dataset mentioned: how many samples, what types of speech (neutral, emotional, multilingual), and what video characteristics (resolution, length, number of speakers)?
```

```
What sample sizes were used in each paper's experiments? This means: how many models compared, how many video clips generated, how many stimuli per condition, and how many human evaluators (if applicable)?
```

```
Did any of these papers report effect sizes, confidence intervals, or correlation coefficients? If so, list the exact values and what they measured.
```

### For Gap Verification

```
Do any of these papers benchmark multiple voice cloning systems combined with multiple lip sync systems on the same stimuli? If not, what is the closest any paper comes to this?
```

```
Do any of these papers compare quality between emotional and neutral speech conditions using the same generation systems? What did they find about emotional vs neutral performance?
```

```
What do these papers say about the limitations of LSE-C and LSE-D metrics? What alternative sync metrics do they propose or recommend?
```

```
Do any of these papers mention the interaction between voice cloning quality and lip sync quality — for example, does a better voice clone produce better lip sync, or are they independent?
```

### For Writing — Introduction and Related Work

```
What motivations do these papers give for why talking head evaluation is important? Summarize the key arguments for the significance of this research area.
```

```
What do these papers identify as open challenges or future work in talking head generation and evaluation?
```

```
Based on these papers, what is the current state of the art in lip sync evaluation? What are the recognized limitations?
```

## After asking all questions

Save NotebookLM's answers to `step3_2_output.md`. For each answer:
1. Copy the answer
2. Note which source(s) NotebookLM cited
3. Click through to verify the citation actually says what NotebookLM claims

These answers feed into:
- **Step 4** (experimental design — metrics, sample sizes, datasets)
- **Step 6.1** (Introduction — motivations, significance)
- **Step 6.2** (Related Work — state of the art, limitations)
- **Step 6.5** (Discussion — comparison with literature)
