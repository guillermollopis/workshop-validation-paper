"""
Voice Cloning system wrappers.

Each function takes a source audio path and a reference audio path (for speaker embedding),
and returns a cloned audio path.
"""

import os
import subprocess
import tempfile
from pathlib import Path


def _check_duration(output_path: str, source_audio: str, system_name: str, tolerance: float = 0.5):
    """Log a warning if output duration deviates >tolerance from source duration."""
    try:
        import soundfile as sf
        src_data, src_sr = sf.read(source_audio)
        out_data, out_sr = sf.read(output_path)
        src_dur = len(src_data) / src_sr
        out_dur = len(out_data) / out_sr
        deviation = abs(out_dur - src_dur) / src_dur if src_dur > 0 else 0
        if deviation > tolerance:
            print(f"    [WARN] {system_name}: duration {out_dur:.2f}s vs source {src_dur:.2f}s "
                  f"(deviation {deviation:.0%})")
            return False
        return True
    except Exception:
        return True


def clone_xtts_v2(source_audio: str, reference_audio: str, output_path: str,
                   text: str = "", gpu: bool = True, language: str = "es") -> bool:
    """Clone voice using XTTS-v2 (Coqui TTS).

    Uses TTS mode: source text is provided (pre-transcribed with Whisper medium),
    then re-synthesized with the reference speaker's voice.
    """
    try:
        from TTS.api import TTS
        device = "cuda" if gpu else "cpu"
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

        if not text:
            print("    [WARN] XTTS-v2: no transcript provided, falling back to Whisper medium")
            import whisper
            whisper_model = whisper.load_model("medium")
            result = whisper_model.transcribe(source_audio, language=language)
            text = result["text"]

        if not text.strip():
            print("    [ERROR] XTTS-v2: empty transcription from source audio")
            return False

        tts.tts_to_file(
            text=text,
            speaker_wav=reference_audio,
            language=language,
            file_path=output_path,
        )

        # Duration validation — retry once if duration is off
        if not _check_duration(output_path, source_audio, "XTTS-v2"):
            print("    [INFO] XTTS-v2: retrying due to duration mismatch...")
            tts.tts_to_file(
                text=text,
                speaker_wav=reference_audio,
                language=language,
                file_path=output_path,
            )
            _check_duration(output_path, source_audio, "XTTS-v2")

        return True
    except Exception as e:
        print(f"    [ERROR] XTTS-v2: {e}")
        return False


def clone_knn_vc(source_audio: str, reference_audio: str, output_path: str,
                  text: str = "", gpu: bool = True, language: str = "es") -> bool:
    """Clone voice using kNN-VC (INTERSPEECH 2023).

    Audio-to-audio voice conversion using WavLM features and k-nearest neighbors.
    Language-agnostic, preserves duration naturally (frame-level matching).
    """
    try:
        import torch
        import torchaudio

        device = "cuda" if gpu and torch.cuda.is_available() else "cpu"

        knn_vc = torch.hub.load('bshall/knn-vc', 'knn_vc',
                                prematched=True, trust_repo=True,
                                pretrained=True, device=device)

        query_seq = knn_vc.get_features(source_audio)
        # Use vad_trigger_level=0 to disable VAD trimming which fails on quiet clips
        matching_set = knn_vc.get_matching_set([reference_audio], vad_trigger_level=0)
        out_wav = knn_vc.match(query_seq, matching_set, topk=4)

        torchaudio.save(output_path, out_wav[None], 16000)

        _check_duration(output_path, source_audio, "kNN-VC")
        return True
    except Exception as e:
        print(f"    [ERROR] kNN-VC: {e}")
        return False


def clone_openvoice_v2(source_audio: str, reference_audio: str, output_path: str,
                        text: str = "", gpu: bool = True, language: str = "es") -> bool:
    """Clone voice using OpenVoice V2 (tone color conversion via coqui-tts).

    Language-agnostic audio-to-audio voice conversion — converts the timbre
    of source_audio to match the speaker in reference_audio.
    """
    try:
        from TTS.api import TTS
        device = "cuda" if gpu else "cpu"
        tts = TTS("voice_conversion_models/multilingual/multi-dataset/openvoice_v2").to(device)

        tts.voice_conversion_to_file(
            source_wav=source_audio,
            target_wav=reference_audio,
            file_path=output_path,
        )

        _check_duration(output_path, source_audio, "OpenVoice V2")
        return True
    except Exception as e:
        print(f"    [ERROR] OpenVoice V2: {e}")
        return False


def clone_cosyvoice(source_audio: str, reference_audio: str, output_path: str,
                     text: str = "", gpu: bool = True, language: str = "es",
                     model_dir: str = "tools/repos/CosyVoice",
                     prompt_text: str = "") -> bool:
    """Clone voice using CosyVoice 2 (Alibaba FunAudioLLM).

    Zero-shot TTS with voice cloning — needs text input. Text is provided
    pre-transcribed with Whisper medium instead of using internal ASR.
    """
    try:
        import sys
        model_path = Path(model_dir).resolve()

        # Add CosyVoice to path if needed
        if str(model_path) not in sys.path:
            sys.path.insert(0, str(model_path))
            # Also add third_party/Matcha-TTS if it exists
            matcha = model_path / "third_party" / "Matcha-TTS"
            if matcha.exists() and str(matcha) not in sys.path:
                sys.path.insert(0, str(matcha))

        from cosyvoice.cli.cosyvoice import CosyVoice2 as CosyVoice
        import soundfile as sf
        import numpy as np

        # Locate pretrained model
        pretrained = model_path / "pretrained_models" / "CosyVoice2-0.5B"
        if not pretrained.exists():
            print(f"    [ERROR] CosyVoice model not found: {pretrained}")
            return False

        cosyvoice = CosyVoice(str(pretrained))

        # Use pre-transcribed text instead of running Whisper base
        if not text:
            print("    [WARN] CosyVoice: no transcript provided, falling back to Whisper medium")
            import whisper
            whisper_model = whisper.load_model("medium")
            result = whisper_model.transcribe(source_audio, language=language)
            text = result["text"]

        if not text.strip():
            print("    [ERROR] CosyVoice: empty transcription from source audio")
            return False

        # Use pre-transcribed prompt text instead of running Whisper base on reference
        if not prompt_text:
            prompt_text = text  # fallback: use same text as prompt

        # Generate with zero-shot voice cloning
        chunks = []
        for chunk in cosyvoice.inference_zero_shot(
            tts_text=text,
            prompt_text=prompt_text,
            prompt_wav=reference_audio,
        ):
            chunks.append(chunk["tts_speech"].numpy().flatten())

        if not chunks:
            print("    [ERROR] CosyVoice: no audio chunks generated")
            return False

        audio = np.concatenate(chunks)
        sf.write(output_path, audio, 22050)

        # Duration validation — retry once if duration is off
        if not _check_duration(output_path, source_audio, "CosyVoice"):
            print("    [INFO] CosyVoice: retrying due to duration mismatch...")
            chunks = []
            for chunk in cosyvoice.inference_zero_shot(
                tts_text=text,
                prompt_text=prompt_text,
                prompt_wav=reference_audio,
            ):
                chunks.append(chunk["tts_speech"].numpy().flatten())
            if chunks:
                audio = np.concatenate(chunks)
                sf.write(output_path, audio, 22050)
                _check_duration(output_path, source_audio, "CosyVoice")

        return True
    except Exception as e:
        print(f"    [ERROR] CosyVoice: {e}")
        return False


# Registry of all VC systems
VC_SYSTEMS = {
    "xtts_v2": {
        "name": "XTTS-v2",
        "func": clone_xtts_v2,
    },
    "knn_vc": {
        "name": "kNN-VC",
        "func": clone_knn_vc,
    },
    "openvoice_v2": {
        "name": "OpenVoice V2",
        "func": clone_openvoice_v2,
    },
    "cosyvoice": {
        "name": "CosyVoice 2",
        "func": clone_cosyvoice,
    },
}


def get_enabled_systems(config: dict) -> dict:
    """Return only enabled VC systems from config."""
    enabled = {}
    for key, system in VC_SYSTEMS.items():
        if config.get("vc_systems", {}).get(key, {}).get("enabled", False):
            enabled[key] = system
    return enabled
