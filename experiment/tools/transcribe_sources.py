#!/usr/bin/env python3
"""
Pre-transcribe all source audio clips using Whisper medium.

Saves transcripts to data/source/transcripts.json for use by
text-based VC systems (XTTS-v2, CosyVoice 2) instead of letting
each system run its own (unreliable) Whisper base ASR.

Usage:
    python3 tools/transcribe_sources.py
    python3 tools/transcribe_sources.py --model large-v3   # use a different model
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Pre-transcribe source clips with Whisper")
    parser.add_argument("--model", default="medium", help="Whisper model size (default: medium)")
    parser.add_argument("--language", default="es", help="Language code (default: es)")
    parser.add_argument("--source-dir", default="data/source", help="Source audio directory")
    args = parser.parse_args()

    import whisper

    source_dir = Path(args.source_dir)
    wav_files = sorted(source_dir.glob("*.wav"))

    if not wav_files:
        print(f"ERROR: No .wav files found in {source_dir}")
        raise SystemExit(1)

    print(f"Loading Whisper '{args.model}' model...")
    model = whisper.load_model(args.model)

    print(f"Transcribing {len(wav_files)} source clips (language={args.language})...\n")

    transcripts = {}
    for i, wav_path in enumerate(wav_files, 1):
        stem = wav_path.stem  # e.g., George_neutral_c01
        print(f"  [{i}/{len(wav_files)}] {stem}...", end=" ", flush=True)

        result = model.transcribe(str(wav_path), language=args.language)
        text = result["text"].strip()
        transcripts[stem] = text

        preview = text[:80] + "..." if len(text) > 80 else text
        print(f'"{preview}"')

    # Save transcripts
    output_path = source_dir / "transcripts.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcripts, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(transcripts)} transcripts to {output_path}")

    # Quick validation
    empty = [k for k, v in transcripts.items() if not v]
    if empty:
        print(f"WARNING: {len(empty)} empty transcriptions: {empty}")
    else:
        print("All transcriptions non-empty.")


if __name__ == "__main__":
    main()
