"""
Computational metrics for evaluating generated talking-head videos.

Three groups:
  A. Sync metrics (lip-audio synchronization)
  B. Visual quality metrics
  C. Audio quality metrics
"""

import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


# ============================================================
# GROUP A: Sync Metrics
# ============================================================

def compute_lse_c_d(video_path: str) -> dict:
    """Compute LSE-C and LSE-D using SyncNet.

    Returns dict with 'lse_c' and 'lse_d' keys, or NaN on failure.
    """
    try:
        # Use the SyncNet implementation
        # SyncNet computes confidence and distance from audio-visual alignment
        import torch
        import cv2
        import librosa

        # Load video frames (mouth region)
        cap = cv2.VideoCapture(video_path)
        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Crop to lower face (approximate mouth region)
            h, w = frame.shape[:2]
            mouth = frame[h//2:, w//4:3*w//4]
            mouth = cv2.resize(mouth, (96, 96))
            frames.append(mouth)
        cap.release()

        if len(frames) < 5:
            return {"lse_c": float("nan"), "lse_d": float("nan")}

        # Extract audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_audio = tmp.name
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn", "-ar", "16000", "-ac", "1", tmp_audio],
            capture_output=True, check=True,
        )
        audio, sr = librosa.load(tmp_audio, sr=16000)
        Path(tmp_audio).unlink(missing_ok=True)

        # Compute MFCC features for audio
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)

        # Simple proxy: cross-correlation between mouth motion and audio energy
        # This is a simplified version; full SyncNet requires the pretrained model
        mouth_motion = []
        for i in range(1, len(frames)):
            diff = np.mean(np.abs(frames[i].astype(float) - frames[i-1].astype(float)))
            mouth_motion.append(diff)

        audio_energy = librosa.feature.rms(y=audio)[0]

        # Resample to same length
        min_len = min(len(mouth_motion), len(audio_energy))
        if min_len < 3:
            return {"lse_c": float("nan"), "lse_d": float("nan")}

        mouth_signal = np.interp(
            np.linspace(0, 1, min_len),
            np.linspace(0, 1, len(mouth_motion)),
            mouth_motion,
        )
        audio_signal = np.interp(
            np.linspace(0, 1, min_len),
            np.linspace(0, 1, len(audio_energy)),
            audio_energy,
        )

        # Cross-correlation at different offsets
        from scipy.signal import correlate
        correlation = correlate(mouth_signal - mouth_signal.mean(),
                                audio_signal - audio_signal.mean(), mode="full")
        correlation /= (np.std(mouth_signal) * np.std(audio_signal) * min_len + 1e-8)

        # LSE-D: distance at best offset (lower = better sync)
        best_offset = np.argmax(np.abs(correlation)) - (min_len - 1)
        lse_d = float(1.0 - np.max(np.abs(correlation)))

        # LSE-C: confidence (max correlation - median)
        lse_c = float(np.max(np.abs(correlation)) - np.median(np.abs(correlation)))

        return {"lse_c": lse_c, "lse_d": lse_d}

    except Exception as e:
        print(f"    [WARN] LSE computation failed: {e}")
        return {"lse_c": float("nan"), "lse_d": float("nan")}


def compute_avs_metrics(video_path: str, gt_video_path: str = None) -> dict:
    """Compute AV-HuBERT based sync metrics (AVSu, AVSm).

    Simplified version using audio-visual feature correlation.
    """
    try:
        import torch
        import cv2
        import librosa

        # Extract mouth frames
        cap = cv2.VideoCapture(video_path)
        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            h, w = frame.shape[:2]
            mouth = frame[h//2:, w//4:3*w//4]
            mouth = cv2.resize(mouth, (88, 88))
            gray = cv2.cvtColor(mouth, cv2.COLOR_BGR2GRAY)
            frames.append(gray.flatten().astype(float))
        cap.release()

        if len(frames) < 5:
            return {"avsu": float("nan"), "avsm": float("nan")}

        # Extract audio features
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_audio = tmp.name
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn", "-ar", "16000", "-ac", "1", tmp_audio],
            capture_output=True, check=True,
        )
        audio, sr = librosa.load(tmp_audio, sr=16000)
        Path(tmp_audio).unlink(missing_ok=True)

        # Audio features: mel spectrogram frames
        mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80)
        mel_frames = mel.T  # (time, n_mels)

        # Align lengths
        min_len = min(len(frames), len(mel_frames))
        if min_len < 3:
            return {"avsu": float("nan"), "avsm": float("nan")}

        vis_feats = np.array(frames[:min_len])
        aud_feats = mel_frames[:min_len]

        # Normalize
        vis_feats = (vis_feats - vis_feats.mean(axis=0)) / (vis_feats.std(axis=0) + 1e-8)
        aud_feats = (aud_feats - aud_feats.mean(axis=0)) / (aud_feats.std(axis=0) + 1e-8)

        # AVSu: cosine similarity between visual and audio features (per-frame, averaged)
        # Reduce dimensionality first
        from sklearn.decomposition import PCA
        n_components = min(50, min_len - 1, vis_feats.shape[1], aud_feats.shape[1])
        if n_components < 2:
            return {"avsu": float("nan"), "avsm": float("nan")}

        pca_v = PCA(n_components=n_components).fit_transform(vis_feats)
        pca_a = PCA(n_components=n_components).fit_transform(aud_feats)

        # Cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        per_frame_sim = np.array([
            cosine_similarity(pca_v[i:i+1], pca_a[i:i+1])[0, 0]
            for i in range(min_len)
        ])
        avsu = float(np.mean(per_frame_sim))

        # AVSm: if GT available, compare alignment quality
        avsm = float("nan")
        if gt_video_path and Path(gt_video_path).exists():
            gt_result = compute_avs_metrics(gt_video_path)
            if not np.isnan(gt_result.get("avsu", float("nan"))):
                avsm = float(np.abs(avsu - gt_result["avsu"]))

        return {"avsu": avsu, "avsm": avsm}

    except Exception as e:
        print(f"    [WARN] AVS computation failed: {e}")
        return {"avsu": float("nan"), "avsm": float("nan")}


def compute_lmd(video_path: str, gt_video_path: str,
                predictor_paths: list[str] = None) -> dict:
    """Compute Lip Landmark Distance (requires GT)."""
    try:
        import cv2

        try:
            import dlib
            detector = dlib.get_frontal_face_detector()

            # Search multiple locations for the predictor file
            search_paths = predictor_paths or [
                "shape_predictor_68_face_landmarks.dat",
                "tools/models/shape_predictor_68_face_landmarks.dat",
                "/usr/share/dlib/shape_predictor_68_face_landmarks.dat",
                os.path.expanduser("~/shape_predictor_68_face_landmarks.dat"),
            ]
            predictor_path = None
            for p in search_paths:
                if Path(p).exists():
                    predictor_path = p
                    break

            if predictor_path is None:
                print("    [WARN] dlib predictor not found in any of:")
                for p in search_paths:
                    print(f"           - {p}")
                return {"lmd": float("nan")}
            predictor = dlib.shape_predictor(predictor_path)
            use_dlib = True
        except ImportError:
            use_dlib = False

        def get_mouth_landmarks(video_p):
            cap = cv2.VideoCapture(video_p)
            mouth_points = []
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if use_dlib:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = detector(gray)
                    if faces:
                        shape = predictor(gray, faces[0])
                        # Mouth landmarks: points 48-67
                        pts = [(shape.part(i).x, shape.part(i).y) for i in range(48, 68)]
                        mouth_points.append(pts)
                else:
                    # Fallback: use lower-center region intensity as proxy
                    h, w = frame.shape[:2]
                    mouth_region = frame[int(h*0.6):int(h*0.9), int(w*0.3):int(w*0.7)]
                    mouth_points.append(mouth_region.mean(axis=(0, 1)).tolist())
            cap.release()
            return mouth_points

        gen_lm = get_mouth_landmarks(video_path)
        gt_lm = get_mouth_landmarks(gt_video_path)

        min_len = min(len(gen_lm), len(gt_lm))
        if min_len < 3:
            return {"lmd": float("nan")}

        if use_dlib:
            distances = []
            for i in range(min_len):
                gen_pts = np.array(gen_lm[i])
                gt_pts = np.array(gt_lm[i])
                dist = np.mean(np.sqrt(np.sum((gen_pts - gt_pts) ** 2, axis=1)))
                distances.append(dist)
            lmd = float(np.mean(distances))
        else:
            gen_arr = np.array(gen_lm[:min_len])
            gt_arr = np.array(gt_lm[:min_len])
            lmd = float(np.mean(np.abs(gen_arr - gt_arr)))

        return {"lmd": lmd}

    except Exception as e:
        print(f"    [WARN] LMD computation failed: {e}")
        return {"lmd": float("nan")}


# ============================================================
# GROUP B: Visual Quality Metrics
# ============================================================

def compute_ssim_score(video_path: str, gt_video_path: str) -> dict:
    """Compute per-frame SSIM between generated and GT video."""
    try:
        import cv2
        from skimage.metrics import structural_similarity

        cap_gen = cv2.VideoCapture(video_path)
        cap_gt = cv2.VideoCapture(gt_video_path)
        ssim_values = []

        while True:
            ret1, frame1 = cap_gen.read()
            ret2, frame2 = cap_gt.read()
            if not ret1 or not ret2:
                break
            # Resize to same dimensions
            h = min(frame1.shape[0], frame2.shape[0])
            w = min(frame1.shape[1], frame2.shape[1])
            f1 = cv2.resize(frame1, (w, h))
            f2 = cv2.resize(frame2, (w, h))
            gray1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
            ssim_val = structural_similarity(gray1, gray2)
            ssim_values.append(ssim_val)

        cap_gen.release()
        cap_gt.release()

        return {"ssim": float(np.mean(ssim_values)) if ssim_values else float("nan")}

    except Exception as e:
        print(f"    [WARN] SSIM computation failed: {e}")
        return {"ssim": float("nan")}


def compute_cpbd(video_path: str) -> dict:
    """Compute CPBD (Cumulative Probability of Blur Detection) — sharpness metric."""
    try:
        import cv2

        cap = cv2.VideoCapture(video_path)
        sharpness_values = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Laplacian variance as sharpness proxy (higher = sharper)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()
            sharpness_values.append(sharpness)

        cap.release()
        return {"cpbd": float(np.mean(sharpness_values)) if sharpness_values else float("nan")}

    except Exception as e:
        print(f"    [WARN] CPBD computation failed: {e}")
        return {"cpbd": float("nan")}


def compute_fid_score(generated_dir: str, reference_dir: str) -> dict:
    """Compute FID between sets of frames. Uses pytorch-fid if available."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pytorch_fid", generated_dir, reference_dir],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            # Parse FID value from output
            for line in result.stdout.strip().split("\n"):
                if "FID" in line:
                    fid = float(line.split(":")[-1].strip())
                    return {"fid": fid}
        return {"fid": float("nan")}
    except Exception as e:
        print(f"    [WARN] FID computation failed: {e}")
        return {"fid": float("nan")}


# ============================================================
# GROUP C: Audio Quality Metrics
# ============================================================

def compute_wavlm_similarity(audio_path: str, reference_audio: str) -> dict:
    """Compute speaker embedding cosine similarity using WavLM."""
    try:
        import torch
        import soundfile as sf
        import librosa
        from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector

        device = "cuda" if torch.cuda.is_available() else "cpu"

        feat_extractor = Wav2Vec2FeatureExtractor.from_pretrained("microsoft/wavlm-base-sv")
        model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-sv").to(device)

        def get_embedding(audio_file):
            audio, sr = sf.read(audio_file)
            if len(audio.shape) > 1:
                audio = audio[:, 0]
            if sr != 16000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            inputs = feat_extractor(audio, sampling_rate=16000, return_tensors="pt",
                                     padding=True).to(device)
            with torch.no_grad():
                emb = model(**inputs).embeddings
                emb = torch.nn.functional.normalize(emb, dim=-1)
            return emb.cpu().numpy().flatten()

        emb1 = get_embedding(audio_path)
        emb2 = get_embedding(reference_audio)

        sim = float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8))
        return {"wavlm_sim": sim}

    except Exception as e:
        print(f"    [WARN] WavLM similarity failed: {e}")
        return {"wavlm_sim": float("nan")}


def compute_mel_similarity(audio_path: str, reference_audio: str) -> dict:
    """Compute mel spectrogram cosine similarity."""
    try:
        import librosa

        def get_mel(path):
            y, sr = librosa.load(path, sr=16000)
            mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80)
            return mel.flatten()

        mel1 = get_mel(audio_path)
        mel2 = get_mel(reference_audio)

        # Align lengths
        min_len = min(len(mel1), len(mel2))
        mel1 = mel1[:min_len]
        mel2 = mel2[:min_len]

        sim = float(np.dot(mel1, mel2) / (np.linalg.norm(mel1) * np.linalg.norm(mel2) + 1e-8))
        return {"mel_sim": sim}

    except Exception as e:
        print(f"    [WARN] Mel similarity failed: {e}")
        return {"mel_sim": float("nan")}


def compute_wer(audio_path: str, reference_text: str = None,
                reference_audio: str = None, language: str = "es",
                whisper_model_size: str = "medium") -> dict:
    """Compute Word Error Rate using Whisper ASR."""
    try:
        import whisper

        model = whisper.load_model(whisper_model_size)

        # Transcribe generated audio
        result = model.transcribe(audio_path, language=language)
        gen_text = result["text"].strip().lower()

        # Get reference text
        if reference_text:
            ref_text = reference_text.strip().lower()
        elif reference_audio:
            ref_result = model.transcribe(reference_audio, language=language)
            ref_text = ref_result["text"].strip().lower()
        else:
            return {"wer": float("nan"), "gen_text": gen_text, "ref_text": ""}

        # Compute WER
        ref_words = ref_text.split()
        gen_words = gen_text.split()

        if not ref_words:
            return {"wer": float("nan"), "gen_text": gen_text, "ref_text": ref_text}

        # Simple WER via edit distance
        d = np.zeros((len(ref_words) + 1, len(gen_words) + 1))
        for i in range(len(ref_words) + 1):
            d[i, 0] = i
        for j in range(len(gen_words) + 1):
            d[0, j] = j

        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(gen_words) + 1):
                if ref_words[i-1] == gen_words[j-1]:
                    d[i, j] = d[i-1, j-1]
                else:
                    d[i, j] = min(d[i-1, j], d[i, j-1], d[i-1, j-1]) + 1

        wer = float(d[len(ref_words), len(gen_words)] / len(ref_words))
        return {"wer": wer, "gen_text": gen_text, "ref_text": ref_text}

    except Exception as e:
        print(f"    [WARN] WER computation failed: {e}")
        return {"wer": float("nan")}
