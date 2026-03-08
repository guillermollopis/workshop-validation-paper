# Step 3.2 Output: Grounded Q&A on Research Papers

Generated: 2026-03-05 10:43
Tool: Gemini API (File Search with grounded citations)

---

## Papers uploaded

1. 2307.09368.pdf
2. 2403.06421.pdf
3. 2405.04327.pdf
4. 2405.10272.pdf
5. 2504.20581.pdf
6. 2507.20579.pdf
7. 2511.04520.pdf

---

## Experimental Design

### Q: What exact computational metrics did each of these papers use to evaluate lip synchronization quality? List every metric name, what it measures, and which paper used it.

The following computational metrics have been used to evaluate lip synchronization quality across various papers:

**1. Lip Landmark Distance (LMD)**
*   **What it measures:** The Euclidean distance between facial landmark locations around the mouth region of a generated video and a reference video. It specifically uses M predefined facial landmarks around the mouth.
*   **Which paper used it:** Proposed in, and discussed in paper 2405.04327 and 2403.06421.
*   **Note:** Paper 2403.06421 refers to this as LMDl, emphasizing its focus on mouth landmarks. It requires access to the reference video.

**2. SyncNet-based Metrics (from SyncNet)**
These metrics are based on the SyncNet model, which captures correlations between audio and spatiotemporal features of the mouth region.

*   **LSE-D (Lip-Sync Error - Distance)**
    *   **What it measures:** The average Euclidean distance between visual and audio embeddings. It represents the feature distance at the predicted offset.
    *   **Which paper used it:** Wav2Lip proposed this metric. It's also mentioned in 2403.06421 and 2511.04520.

*   **LSE-C (Lip-Sync Error - Confidence)**
    *   **What it measures:** The lip-audio synchronization confidence. It measures the difference between the minimum and median distances across various offsets.
    *   **Which paper used it:** Wav2Lip proposed this metric. It's also mentioned in 2403.06421 and 2511.04520.

*   **LSE-O (Lip-Sync Error - Offset)**
    *   **What it measures:** The time offset according to a pre-defined temporal grid.
    *   **Which paper used it:** Mentioned in paper 2403.06421 as one of the SyncNet-based metrics.

**3. SparseSync**
*   **What it measures:** Fuses audio and visual information from pre-trained sound classification and action recognition models to predict the time offset over a pre-defined time grid.
*   **Which paper used it:** Mentioned in paper 2403.06421. It acts as a substitute for evaluating lip-audio synchronization when no reference information is available.

**4. Word Error Rate (WER)**
*   **What it measures:** Proposed as an evaluation metric for reading intelligibility.
*   **Which paper used it:** Mentioned in paper 2405.04327.

**5. Audio-Visual Synchronization (AVSu)**
*   **What it measures:** Cosine similarity between features extracted independently from the lips of generated faces and the audio sequence using a transformer encoder block (specifically, the AV-HuBERT model).
*   **Which paper used it:** Proposed in paper 2405.04327.

**6. Multimodal Audio-Visual Synchronization (AVSm)**
*   **What it measures:** Cosine similarity between the alignment of the generated lips-audio pair and the Ground Truth (GT) lips-audio pair. It extracts features from both generated and GT videos (mouth region and audio) using the AV-HuBERT model.
*   **Which paper used it:** Proposed in paper 2405.04327.

**7. Visual-only Lip Synchronization (AVSv)**
*   **What it measures:** Focuses solely on the visual shape similarity of the lips by comparing features from the lips of the generated faces and GT faces, without involving audio.
*   **Which paper used it:** Proposed in paper 2405.04327.

**Sources cited:**

- **2403.06421:** "all facial landmark locations around the mouth re�gion of the generated video v and that of the reference video
r as: LMDl =
1
M
PM
i=1 ||f
i
d
(v), fi
d
(r)||2, where fd(·) de�notes a facia..."
- **2405.04327:** "and
face dubbing. These systems are also well-suited for utiliza�tion in meeting rooms, facilitating seamless communication
among individuals conversing in different languages [38].
In addition to ..."
- **2511.04520:** "most prominent metrics for lip synchronization are the Syncnet distance (LSE�D) and confidence score (LSE-C). Syncnet, a CNN-based network, aims to capture the correlation
between audio and spatio-te..."

---

### Q: What exact computational metrics did each of these papers use to evaluate voice/audio quality? List every metric name, what it measures, and which paper used it.

Based on the provided documents, the computational metrics primarily evaluate aspects related to lip-audio synchronization and visual quality in talking head videos, rather than the intrinsic voice or audio quality in isolation (e.g., clarity, naturalness, absence of noise).

Here are the relevant metrics found:

*   **LSE-D (Lip-Sync Expert - Distance)**: This metric, part of Syncnet, aims to capture the correlation between audio and spatio-temporal features of the mouth region to calculate the audio offset (how early or late audio is compared to video). It is widely used to evaluate audio-lip synchronization.
    *   **Paper Used:** Syncnet (Chung & Zisserman, 2016), as referenced in paper `2511.04520`.
*   **LSE-C (Lip-Sync Expert - Confidence)**: Also part of Syncnet, this is a confidence score associated with the audio offset. It's used alongside LSE-D for evaluating audio-lip synchronization.
    *   **Paper Used:** Syncnet (Chung & Zisserman, 2016), as referenced in paper `2511.04520`.
*   **Lip-Sync Metric (Lsync)**: This metric evaluates the degree of alignment between mouth movements and spoken audio. It calculates the mean absolute difference between normalized mouth openness (distance between upper and lower lip landmarks) and normalized audio volume (Root-Mean-Square energy) signals during speech frames.
    *   **Paper Used:** `2511.04520` (as proposed within the paper).
*   **Silent Lip Stability**: This metric relates to mouth movement during silent periods. It detects silent frames using a Voice Activity Detection (VAD) model, extracts facial landmarks, computes the vertical distances between upper and lower lips, normalizes them, and then quantifies stability using the median absolute deviation of these distances across all silent frames.
    *   **Paper Used:** `2511.04520` (as proposed within the paper).

It is important to note that while these metrics involve audio, their primary focus is on synchronization with visual elements or the stability of lip movements, rather than evaluating the standalone quality of the voice or audio signal itself (e.g., how clear, natural, or free from artifacts the sound is). The documents also discuss numerous visual quality metrics (e.g., PSNR, SSIM, LPIPS, DISTS) and video quality assessment methods, which are outside the scope of "voice/audio quality" as specified in the question.

**Sources cited:**

- **2511.04520:** "luminance comparison, contrast comparison and structure comparison respectively.
SSIM need the images to be perfectly aligned in order to be accurate. Also, since it use small patches,
it focus on l..."
- **2403.06421:** "2
for testing, following [13, 14] by using the 2AFC score as the
performance measure for all objective metrics. Specifically,
the 2AFC score is computed by p × q + (1 − p) × (1 − q),
where p is th..."

---

### Q: What human evaluation methods did these papers use? For each paper that included a human study: what was the study design (MOS, A/B preference, Likert scale, etc.), how many participants, and what did they ask participants to judge?

Several papers included human evaluation methods with varying study designs, participant counts (or annotation counts), and judgment criteria.

### Paper: "2511.04520"

*   **Study Design**: The paper utilized human ratings to assess "human preference scores" and "human opinion scores" to understand human perception of realism. It correlated various metrics with these human ratings. While the exact scale (e.g., Likert, MOS) is not explicitly mentioned, the study involved collecting "3,519 ratings" distributed equally across seventeen different models.
*   **Number of Participants**: The exact number of participants is not specified in the provided information. However, a total of 3,519 ratings were acquired.
*   **What Participants Were Asked to Judge**: Participants provided judgments on various aspects that contributed to human preference and opinion scores, including Global Aesthetics, Mouth Visual Quality, Face Quality, Lip Dynamics, Head Motion Dynamics, Eyebrow Dynamics, Silent Lip Stability, Lip-Sync Quality, Naturalness, and Synchronization.

### Paper: "2403.06421"

*   **Study Design**: This study employed a two-alternative forced choice (2AFC) method. Participants compared pairs of videos generated by different methods for the same audio and identity, selecting their preferred option. The experiments were conducted in a controlled lab setting.
*   **Number of Participants**: The specific number of participants is not stated, but the study resulted in a total of "2,700 human annotations".
*   **What Participants Were Asked to Judge**: Participants were asked to choose their preferred video based on three criteria: visual quality, lip-audio synchronization, and head movement naturalness.

### Paper: "2405.04327"

*   **Study Design, Number of Participants, and Judgment Criteria**: This paper mentions a "user study" and suggests that the "sample size of our user study could be increased to gain more statistical power". However, the provided snippets do not offer details regarding the specific study design, the actual number of participants, or what participants were asked to judge.

**Sources cited:**

- **2511.04520:** "errors, ensuring participants could make consistent and intuitive judgments. In total,
we acquired 3,519 ratings, distributed equally among the seventeen models. We then compute the
Spearman correla..."
- **2403.06421:** "two-alternative
forced choice (2AFC) method, participants compare pairs of
videos generated by different methods (e.g., MakeItTalk vs.
AD-NeRF) for the same audio and identity, choosing the pre�fer..."
- **2405.04327:** "them more efficiently for lip syn�chronization, despite increased performance and stability in
the training. Furthermore, the sample size of our user study 
could be increased to gain more statistica..."

---

### Q: What datasets did each paper use for evaluation? For each dataset mentioned: how many samples, what types of speech (neutral, emotional, multilingual), and what video characteristics (resolution, length, number of speakers)?

Several papers discuss the datasets used for evaluation, providing details on their characteristics.

**Paper 2511.04520**
This paper created a new evaluation set called **THEval**.
*   **Samples**: The dataset consists of 5,011 videos.
*   **Types of Speech**: It features multilingual content, including Spanish, Italian, English, French, Japanese, and Chinese.
*   **Video Characteristics**:
    *   **Resolution**: High-fidelity 1080p resolution.
    *   **Length**: The dataset contains over 18 hours of content, with an average video length of 13 seconds.
    *   **Number of Speakers**: Each video includes a single speaker.
    *   **Source**: Videos were sourced from 31 public YouTube channels.

**Paper 2403.06421**
This paper assembled its own diverse dataset of photorealistic human videos for training and evaluation of audio-driven talking head generation models.
*   **Samples**: It comprises ten real human videos with paired audio-visual data.
*   **Types of Speech**: The dataset includes spoken languages such as Mandarin, English, Japanese, and Spanish, indicating a multilingual nature.
*   **Video Characteristics**:
    *   **Resolution**: Videos are processed to a uniform frame resolution of 256 × 256 pixels at 25 frames-per-second (FPS).
    *   **Length**: Specific video lengths are not provided beyond "ten real human videos".
    *   **Number of Speakers**: The video set covers both male and female identities, but the number of speakers per video isn't explicitly stated, though "real human video sequences" implies individual speakers.
    *   **Source**: Videos were retrieved from sources including HDTF, youtube.com, and bilibili.com.

**Paper 2507.20579**
This paper refers to several existing datasets and works:
*   **FaceForensics++**: This dataset is mentioned in the context of learning to detect manipulated facial images.
*   **ILLUSION**: Described as a comprehensive multi-modal, multi-lingual deepfake dataset.
*   **"Do I Have Your Attention: A Large Scale Engagement Prediction Dataset and Baselines"**: This likely refers to a large-scale engagement prediction dataset.
*   **Vigo**: An audiovisual fake detection and segment localization dataset.
*   **Semi-Truths**: A large-scale dataset of AI-augmented images for evaluating the robustness of AI-generated image detectors.

**Paper 2405.04327**
This paper references other works that involve datasets:
*   A dataset of **230,000 3D facial landmarks** from Bulat and Tzimiropoulos (2017).
*   The **"Lip Reading in the Wild"** dataset from Chung and Zisserman (2016).

**Sources cited:**

- **2511.04520:** "create an evaluation set with samples explicitly not seen
during the training of the models we evaluate. The dataset was constructed by sourcing 5,011 video
from a wide range of 31 public YouTube ch..."
- **2403.06421:** "Mandarin (e) English
(f) Japanese (g) Mandarin (h) English (i) English (j) Spanish
Fig. 2. Thumbnails of real human video sequences in our dataset. The spoken language is marked below each thumbnail..."
- **2507.20579:** "Luisa Verdoliva, Christian Riess, Justus Thies,
and Matthias Niessner. 2019. FaceForensics++: Learning to Detect Manipulated
Facial Images. In Proceedings of the IEEE/CVF International Conference on..."
- **2405.04327:** "2
[5] Adrian Bulat and Georgios Tzimiropoulos. How far are we
from solving the 2d & 3d face alignment problem? (and a
dataset of 230,000 3d facial landmarks). In International
Conference on Comput..."

---

### Q: What sample sizes were used in each paper's experiments? This means: how many models compared, how many video clips generated, how many stimuli per condition, and how many human evaluators (if applicable)?

Here's a breakdown of the sample sizes used in the experiments described in the provided papers:

**For the paper identified as 2403.06421:**
*   **Number of models compared:** The study compared four representative generative methods for audio-driven talking head videos.
*   **Number of video clips generated:** While the exact total number of unique generated video clips is not explicitly stated, the experiments involved comparisons that resulted in 2,700 human annotations. These annotations were derived from comparing 6 video pairs for each combination of identity and driving audio. The dataset for evaluation was based on ten real human videos with paired audio-visual data.
*   **Number of stimuli per condition:** Participants used a two-alternative forced choice (2AFC) method to compare pairs of videos generated by different methods, ensuring the same audio and identity for each pair. There were 6 video pairs for every combination of identity and driving audio.
*   **Number of human evaluators:** Fifteen participants were recruited for the psychophysical experiments.

**For the paper identified as 2511.04520:**
*   **Number of models compared:** The extensive experiments were conducted on videos generated by 17 state-of-the-art models.
*   **Number of video clips generated:** The experiments utilized a total of 85,000 videos.
*   **Number of stimuli per condition:** The provided information indicates that a user study interface was used where videos were randomly selected from common videos of all methods for comparison. However, the specific number of stimuli presented per condition to each evaluator is not detailed.
*   **Number of human evaluators:** The paper mentions conducting "human user studies" and involving "human raters" in the evaluation process. However, the exact number of human evaluators is not specified in the provided snippets.

**Sources cited:**

- **2511.04520:** "images (Xu et al., 2024b; Xue et al., 2024) and videos (Wang et al.,
2024b;a). However, the rapid advancement in generation has outpaced the development of adequate
evaluation metrics, see details o..."
- **2403.06421:** "Mandarin (e) English
(f) Japanese (g) Mandarin (h) English (i) English (j) Spanish
Fig. 2. Thumbnails of real human video sequences in our dataset. The spoken language is marked below each thumbnail..."
- **2507.20579:** "John
Schulman, Jacob Hilton, Fraser Kelton, Luke Miller, Maddie Simens, Amanda
Askell, Peter Welinder, Paul F. Christiano, Jan Leike, and Ryan Lowe. 2022.
Training language models to follow instruc..."

---

### Q: Did any of these papers report effect sizes, confidence intervals, or correlation coefficients? If so, list the exact values and what they measured.

Yes, the paper "2511.04520" reported correlation coefficients and confidence intervals.

Here are the exact values and what they measured:

**Spearman Correlation Coefficients (ρ) and 95% Confidence Intervals (CI) with Human Preferences:**

*   **Final THEval score:** ρ = 0.870, 95% CI: [0.648, 0.967]. This measures the correlation between the final THEval score and human ratings.
*   **LSE-C:** ρ = -0.164, 95% CI: [-0.613, 0.388].
*   **LSE-D:** ρ = -0.269, 95% CI: [-0.675, 0.282].
*   **FVD:** ρ = 0.289, 95% CI: [-0.321, 0.782].
*   **FID:** ρ = 0.210, 95% CI: [-0.344, 0.710].
*   **LMD-F:** ρ = 0.231, 95% CI: [-0.392, 0.775].
*   **LMD-L:** ρ = 0.227, 95% CI: [-0.389, 0.759].
*   **(1) Global Aesthetics:** ρ = 0.544, 95% CI: [0.129, 0.795].
*   **(2) Mouth Visual Quality:** ρ = 0.765, 95% CI: [0.498, 0.917].
*   **(3) Face Quality:** ρ = 0.699, 95% CI: [0.430, 0.875].
*   **(4) Lip Dynamics:** ρ = 0.414, 95% CI: [-0.155, 0.769].
*   **(5) Head Motion Dynamics:** ρ = 0.763, 95% CI: [0.418, 0.942].
*   **(6) Eyebrow Dynamics:** ρ = 0.527, 95% CI: [0.060, 0.856].
*   **(7) Silent Lip Stability:** ρ = 0.484, 95% CI: [0.033, 0.808].
*   **(8) Lip-Sync:** ρ = 0.404, 95% CI: [-0.143, 0.775].
*   **Quality:** ρ = 0.713, 95% CI: [0.424, 0.895].
*   **Naturalness:** ρ = 0.702, 95% CI: [0.217, 0.862].
*   **Synchronization:** ρ = 0.603, 95% CI: [0.323, 0.919].

The 95% Confidence Intervals were obtained via bootstrapping with n = 10,000 resamples. These metrics demonstrate varying degrees of alignment with human preferences.

The paper "2504.20581" reported **cosine similarity** values for various acoustic features and emotional states, which are a type of similarity measure.

**Cosine Similarity for Acoustic Features (between original and cloned samples):**

*   **pitch:** Ranges from 0.5278 (SpeechT5) to 0.6094 (OuteTTS).
*   **mel spectrogram:** Ranges from 0.8622 (XTTS-v2) to 0.9259 (OuteTTS).
*   **RMS:** Ranges from 0.6040 (SpeechT5) to 0.6970 (OuteTTS).
*   **spectral centroid:** Ranges from 0.7387 (XTTS-v2) to 0.7855 (SpeechT5).
*   **spectral flatness:** Ranges from 0.2418 (XTTS-v2) to 0.3229 (OuteTTS).
*   **spectral roll-off:** Ranges from 0.7907 (XTTS-v2) to 0.8357 (SpeechT5).
*   **tempogram:** Ranges from 0.3658 (XTTS-v2) to 0.5159 (OuteTTS).
*   **chromagram:** Ranges from 0.5694 (WhisperSpeech) to 0.6312 (SpeechT5).
*   **pseudo-constant-Q transform:** Ranges from 0.6242 (XTTS-v2) to 0.6707 (OuteTTS).
*   **constant-Q chromagram:** Ranges from 0.6836 (WhisperSpeech) to 0.7330 (SpeechT5).
*   **WavLM:** Ranges from 0.7499 (OuteTTS) to 0.8356 (XTTS-v2).

**Cosine Similarity for Speaker Embeddings (WavLM model, emotional states):**

*   **anger:** Ranges from 0.7197 (OuteTTS) to 0.8098 (XTTS-v2).
*   **disgust:** Ranges from 0.7034 (OuteTTS) to 0.8325 (XTTS-v2).
*   **fear:** Ranges from 0.6953 (OuteTTS) to 0.7996 (SpeechT5).
*   **happiness:** Ranges from 0.7329 (OuteTTS) to 0.8160 (XTTS-v2).
*   **neutral:** Ranges from 0.7370 (OuteTTS) to 0.8480 (XTTS-v2).
*   **sadness:** Ranges from 0.7135 (OuteTTS) to 0.8365 (XTTS-v2).
*   **Average:** Ranges from 0.7170 (OuteTTS) to 0.8226 (XTTS-v2).

**Sources cited:**

- **2511.04520:** "errors, ensuring participants could make consistent and intuitive judgments. In total,
we acquired 3,519 ratings, distributed equally among the seventeen models. We then compute the
Spearman correla..."
- **2504.20581:** "of similarity for spectral features, including
centroid, flatness, and roll-off, further indicate that the speak�ers are highly similar in frequency distribution and that the
noise is minimal.
The ..."

---

## Gap Verification

### Q: Do any of these papers benchmark multiple voice cloning systems combined with multiple lip sync systems on the same stimuli? If not, what is the closest any paper comes to this?

None of the provided papers directly benchmark multiple voice cloning systems combined with multiple lip-sync systems on the same stimuli.

However, the paper "2511.04520" comes closest by benchmarking various "state-of-the-art TH-generation methods" (talking head generation methods) which inherently involve both audio (and thus voice) and visual (including lip motion) aspects. This paper evaluates several models, such as Controltalk, DaGAN, Dimitra, OmniAvatar, and Wav2Lip, on metrics like "Lip Dynamics," "Head Motion," "Eyebrow Dynamics," and "Naturalness." While these are end-to-end talking head generation systems rather than separate voice cloning and lip-sync modules being combined, their evaluation includes lip dynamics and overall video quality, which are relevant to lip-sync performance. For instance, Wav2Lip, which is primarily a lip-sync model, is included in this benchmark as a talking head generation method. The paper also mentions the instability of Syncnet, a lip-sync evaluation metric, which can be influenced by various factors unrelated to lip synchronization.

Another paper, "2504.20581", introduces "CLONEVAL: An Open Voice Cloning Benchmark," which focuses specifically on evaluating the performance of voice cloning text-to-speech models. This benchmark provides an evaluation protocol and a library for assessing voice cloning capabilities, but it does not incorporate lip-sync systems.

The paper "2405.04327" discusses various lip-sync evaluation metrics, including Lip Landmark Distance (LMD), SyncNet, and LSE-C/LSE-D, and highlights the limitations of some of these metrics. It also briefly mentions different approaches for synthesizing heads, but it does not describe a benchmark combining distinct voice cloning and lip-sync systems.

**Sources cited:**

- **2511.04520:** "H.264 and H.265 encodings. In both experiments there are no
noticeable qualitative differences from a human evaluation standpoint. This confirms the findings of
(Yaman et al., 2024b) that Syncnet is..."
- **2504.20581:** "CLONEVAL: AN OPEN VOICE CLONING BENCHMARK
Iwona Christop Tomasz Kuczynski Marek Kubis ´
Adam Mickiewicz University, ul. Uniwersytetu Poznanskiego 4, 61-614 Pozna ´ n, Poland ´
ABSTRACT
We present ..."
- **2405.04327:** "and
face dubbing. These systems are also well-suited for utiliza�tion in meeting rooms, facilitating seamless communication
among individuals conversing in different languages [38].
In addition to ..."

---

### Q: Do any of these papers compare quality between emotional and neutral speech conditions using the same generation systems? What did they find about emotional vs neutral performance?

Yes, the paper "2504.20581" compares the quality between emotional and neutral speech conditions using the same generation systems. It evaluates several voice cloning models, including OuteTTS, SpeechT5, VALL-E X, WhisperSpeech, and XTTS-v2, across various emotional states and a neutral state.

Regarding their findings on emotional vs. neutral performance, the paper concluded that all models were most effective at cloning the neutral state. Conversely, they were least effective at cloning highly expressive emotions such as fear, anger, and disgust. The similarity values, particularly for the WavLM model's speaker embeddings, further support this, showing generally higher scores for neutral speech compared to emotional speech across all tested models. XTTS-v2, in particular, showed the best results for almost all emotions, with a minimal difference for fear, while OuteTTS consistently demonstrated the lowest performance. Additionally, findings from the LS test-clean dataset indicated that the models performed better when cloning non-emotional speech.

**Sources cited:**

- **2504.20581:** "0.6953 0.7996 0.7466 0.7601 0.7929
happiness 0.7329 0.8068 0.7658 0.7462 0.8160
neutral 0.7370 0.8322 0.7699 0.7714 0.8480
sadness 0.7135 0.8099 0.7525 0.7516 0.8365
Average 0.7170 0.8097 0.7595 0..."

---

### Q: What do these papers say about the limitations of LSE-C and LSE-D metrics? What alternative sync metrics do they propose or recommend?

The papers highlight several limitations of LSE-C and LSE-D metrics. Both LSE-C (Syncnet Confidence score) and LSE-D (Syncnet Distance) rely on the SyncNet model, which has been shown to be unstable and easily influenced by factors other than lip synchronization, such as mouth cropping, image quality, and brightness. SyncNet is also sensitive to audio and video encoding, even when human observers perceive no noticeable difference.

Specifically, the limitations of LSE-C and LSE-D include:
*   **Limited Correlation with Human Evaluation:** They have very limited correlation with how humans perceive lip synchronization.
*   **Unreasonable Values:** In some cases, generated results have significantly outperformed ground truth data on these metrics, indicating their limitations.
*   **Instability to External Factors:** They are unstable to factors like the cropped mouth region, image quality, and brightness.
*   **Sensitivity to Translations:** SyncNet, on which these metrics are based, is vulnerable to translations in the data because it is not properly shift-invariant. Small translations in the face can affect the metrics, leading to a measurement of poor lip synchronization performance even when the lip shape is preserved. This means they can show fluctuations in performance even for ground truth data.

Given these limitations, one paper proposes **AV-HuBERT-based lip sync metrics** as an alternative. The AV-HuBERT features are presented as more stable than SyncNet features. The paper suggests three novel metrics based on AV-HuBERT (AVSm, AVSv, and AVSu) that demonstrate greater stability compared to LSE-C and LSE-D.

Another paper suggests that **user studies** remain a viable evaluation method for talking head generation due to the limitations of objective metrics, although user studies are time-consuming and tedious. It also implies that relying on single metrics is insufficient and that a more comprehensive evaluation should consider various aspects like accurate mouth movements and realistic head motion.

**Sources cited:**

- **2511.04520:** "limitations. Additionally recent works (Yaman
et al., 2024b;a) have shown that Syncnet is not stable and can easily be influenced by factors outside
of lip synchronization (e.g mouth cropping, image..."
- **2405.04327:** "fair comparison by evaluating
under the same conditions.
The three widely utilized synchronization metrics in the
literature have crucial problems. The mouth landmark dis�tance (LMD) measures the s..."

---

### Q: Do any of these papers mention the interaction between voice cloning quality and lip sync quality — for example, does a better voice clone produce better lip sync, or are they independent?

Based on the provided papers, there is no direct mention of the interaction between the quality of a voice clone and the quality of lip synchronization. The papers discuss aspects of talking head generation, including audio-driven methods for synchronization and expressiveness, and metrics for evaluating lip-audio synchronization. However, they do not explicitly state whether a better quality voice clone produces better lip sync or if these two aspects are independent. The focus appears to be on the visual accuracy of lip movements in relation to the audio, rather than the perceptual quality of the cloned voice itself influencing the synchronization process.

**Sources cited:**

- **2511.04520:** "In the case of OmniAvatar, this is due to the employed image�to-video model WanVideo (Wan Team et al., 2025), which generates exaggerated articulations that
appear unnatural, reflected in the scores ..."
- **2403.06421:** "requires access to the reference video,
1We adopt the 68 points facial landmark definition by Dlib, among which
12 landmarks correspond to the mouth region. 
Table 2. 2AFC scores for visual quality ..."
- **2405.04327:** "them more efficiently for lip syn�chronization, despite increased performance and stability in
the training. Furthermore, the sample size of our user study 
could be increased to gain more statistica..."

---

## Writing

### Q: What motivations do these papers give for why talking head evaluation is important? Summarize the key arguments for the significance of this research area.

The evaluation of talking head generation is crucial for several reasons, as highlighted by the provided papers:

Firstly, current evaluation methods for talking head videos, particularly those driven by audio-speech sequences, are often inadequate and do not fully capture the complexity and nuance of human perception. Existing metrics commonly focus on image quality (such as FID, FVD, SSIM, and PSNR) and lip synchronization quality (using tools like Syncnet). However, these general metrics often struggle with complex generated videos, can be impacted by factors unrelated to video quality, and have been shown to correlate poorly with human preferences for high-quality images and videos. Specifically, Syncnet, a popular tool for assessing lip-audio synchronization, has been found to be unstable, sensitive to factors like mouth cropping and head pose, and its confidence and distance scores do not align well with human judgment.

Secondly, talking head videos involve specific elements that require dedicated assessment beyond general video generation. These include global image quality, the quality of facial motions (like lip synchronization, facial expressions, and head pose movement), and overall naturalness. Many generated talking heads currently lack natural head motion and may exhibit exaggerated expressions. More recent video-driven methods, while generating more expressive and realistic videos, still necessitate robust evaluation frameworks to accurately measure their improvements.

Thirdly, the development of robust evaluation frameworks, such as THEVAL, is motivated by the need to enhance existing metrics and provide a more comprehensive understanding of talking head generation models. By breaking down the evaluation into relevant factors, from global head movement to nuanced expressions, these frameworks facilitate targeted improvements in future models. This detailed diagnostics and a final measure that aligns with human preference are essential for fostering the development of new generation methods.

Finally, the accurate assessment of advancements in audio-driven talking head generation is critical due to its wide array of potential applications, including newscasting, customer service, gaming, and smart healthcare. As digital humans and avatars play an increasingly vital role in virtual worlds like the metaverse, ensuring the quality and naturalness of their animation becomes paramount. Therefore, reliable evaluation metrics are crucial for guiding the progress in this field and ensuring that these technologies can be effectively deployed. Moreover, providing a robust, human-aligned evaluation framework helps researchers understand model capabilities and limitations, which is a step towards creating effective detection methods and safeguards against potential misuse, such as "deepfake" technology.

**Sources cited:**

- **2511.04520:** "quality, as well as for background consistency and motion
smoothness in the context of temporal evaluation.
Deviating from general text-based video generation, talking head (TH) generation involves ..."
- **2403.06421:** "accessed by humans through digital avatars
for interaction. Inhabiting the metaverse, digital humans play
a vital role in shaping this virtual world. The audio-driven
talking head generation [1] st..."

---

### Q: What do these papers identify as open challenges or future work in talking head generation and evaluation?

The papers identify several open challenges and areas for future work in talking head generation and evaluation:

**Challenges in Talking Head Generation:**
*   **Lack of Natural Head Motion and Exaggerated Expressions:** Audio-driven methods, while advanced in synchronization, often struggle to produce natural head movements and can lead to exaggerated facial expressions.
*   **Generating Expressiveness and Artifact-Free Details:** Many algorithms face difficulties in generating expressive and artifact-free details in talking head videos. This includes visible artifacts like tearing, blur, or instability in facial regions, especially during large head movements, indicating a trade-off between expressivity and quality.
*   **Realistic Lip Movements:** State-of-the-art generative models still struggle with producing realistic lip movements.

**Challenges in Talking Head Evaluation:**
*   **Limited and Insufficient Metrics:** The current assessment of talking head generation heavily relies on a limited set of metrics, primarily evaluating general video quality and lip synchronization, alongside user studies. These existing metrics, such as FID, FVD, SSIM, PSNR for image quality, and Syncnet for lip synchronization, often fail to reflect human perceptual ratings.
*   **Poor Correlation with Human Preference:** Commonly used metrics like Syncnet's confidence score (LSE-C) and distance (LSE-D) have been shown to correlate poorly with human preferences.
*   **Instability and Sensitivity of Current Tools:** Syncnet, a frequently used tool for lip synchronization, has been found to be unstable and sensitive to factors like mouth cropping and head pose.
*   **Lack of Detailed Diagnostics:** Existing evaluation methods do not offer detailed diagnostics, making it difficult to interpret specific over or underperformance related to aspects like accurate mouth movements, realistic head motion, or overall appearance.

**Future Work:**
*   **Extending Benchmarks to Diverse Scenarios:** Future work will involve extending evaluation benchmarks to include more diverse scenarios, such as multiple humans and side views.
*   **Fostering Development of New Generation Methods:** The aim is to encourage the creation of new and improved talking head generation techniques by providing robust evaluation frameworks.
*   **Creating Effective Detection Methods and Safeguards:** By better understanding model capabilities and limitations through improved evaluation, researchers can take steps towards creating effective detection methods and safeguards against potential misuse of "deepfake" technology.
*   **Public Release and Regular Updates:** Publicly releasing benchmarks, datasets, and code, along with regularly updating leaderboards with new methods, is crucial to reflect progress and ensure reproducibility in the field.

**Sources cited:**

- **2511.04520:** "often
lack natural head motion and may incorporate exaggerated expressions. At the same time recent video�driven counterparts generate more expressive and realistic videos. Our THEval metrics capture..."

---

### Q: Based on these papers, what is the current state of the art in lip sync evaluation? What are the recognized limitations?

The current state of the art in lip sync evaluation primarily relies on metrics derived from SyncNet, a CNN-based network designed to measure the correlation between audio and the spatio-temporal features of the mouth region. The most prominent of these are the SyncNet distance (LSE-D) and confidence score (LSE-C). These metrics calculate the audio offset, indicating whether the audio is early or late compared to the video. LSE-D specifically represents the feature distance at the predicted offset, while LSE-C measures the difference between the minimum and median distances across various offsets. SyncNet metrics are particularly effective for determining audio offsets and identifying speakers in videos with multiple people.

Before SyncNet, the Lip Landmark Distance (LMD) was an early proposed metric, though it suffered from several issues. LSE-C and LSE-D, introduced by Wav2Lip, became a "gold standard" in the literature due to their advantage of not requiring ground truth data. More recently, the Word Error Rate (WER) has been suggested as an evaluation metric for reading intelligibility. User studies also remain a viable evaluation method, especially given the limitations of objective metrics.

Despite their widespread adoption, several recognized limitations exist for these evaluation methods:

*   **Limited Correlation with Human Evaluation:** LSE-C and LSE-D have a very limited correlation with how humans perceive lip synchronization quality. This means that a good score on these metrics does not always align with human judgment.
*   **Unreasonable Values:** In some cases, generation results have been shown to widely outperform ground truth data on LSE-C and LSE-D, indicating that these metrics can produce unreasonable values.
*   **Instability:** SyncNet-based metrics are unstable and can be easily influenced by factors such as the cropped mouth region, image quality, brightness, and small translations in the face. This is partly because SyncNet is not properly shift-invariant.
*   **Lack of Disentanglement for LMD:** The Lip Landmark Distance (LMD) is sensitive to errors in landmark detection and struggles to separate synchronization issues from general generation stability. For example, if a model accurately generates lip movements but introduces errors in the mouth region (like shifting the mouth or face), the landmark positions change, leading to a higher landmark distance even if synchronization is good. LMD also fails to properly consider lip movements or shapes, as variations in lip aperture and spreading can cause misleading scores even with the same lip shape.
*   **Insufficiency of Single Metrics:** Current methods often rely on a few limited metrics to summarize the complex process of generating talking heads. Relying on single metrics can make it difficult to interpret aspects related to over- or underperformance, such as accurate mouth movements or realistic head motion.
*   **Bias in Limited Samples:** Metrics like FID (and by extension FVD) can be biased when assessed on limited samples, which may not provide a sufficient basis for generalization, particularly in the context of audio-driven talking head generation that uses small subsets of videos for inference.
*   **Tedious Nature of User Studies:** While valuable, user studies are tedious and time-consuming to conduct.
*   **Penalization by Facial Landmark-Based Metrics:** LMD-M, a facial landmark-based metric, penalizes small temporal lags that human evaluators might not notice. LMD-F imposes strong penalties for differences in head motion and expression between generated videos and ground truth, even though head motion and facial expression only weakly correlate with audio sequences. This penalization is often not justified, as naturalness can still lead to high human ratings despite such discrepancies.

**Sources cited:**

- **2511.04520:** "most prominent metrics for lip synchronization are the Syncnet distance (LSE�D) and confidence score (LSE-C). Syncnet, a CNN-based network, aims to capture the correlation
between audio and spatio-te..."
- **2405.04327:** "and
face dubbing. These systems are also well-suited for utiliza�tion in meeting rooms, facilitating seamless communication
among individuals conversing in different languages [38].
In addition to ..."

---
