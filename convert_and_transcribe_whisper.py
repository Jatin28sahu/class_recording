# import os
# import sys
# import json
# import argparse
# import subprocess
# from pathlib import Path
# from dotenv import load_dotenv
# from deepgram import DeepgramClient, PrerecordedOptions

# def run(cmd: list[str]) -> None:
#     try:
#         subprocess.run(cmd, check=True)
#     except FileNotFoundError:
#         print("ERROR: ffmpeg not found. Please install ffmpeg and ensure it's in PATH.", file=sys.stderr)
#         raise
#     except subprocess.CalledProcessError as e:
#         print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
#         raise

# def convert_to_wav(src: Path, dst: Path, sr: int = 16000) -> Path:
#     """Convert any audio/video to 16 kHz mono WAV (PCM s16le). Requires ffmpeg."""
#     if dst.suffix.lower() != ".wav":
#         dst = dst.with_suffix(".wav")
#     dst.parent.mkdir(parents=True, exist_ok=True)
#     cmd = [
#         "ffmpeg", "-y",
#         "-i", str(src),
#         "-ac", "1",
#         "-ar", str(sr),
#         "-c:a", "pcm_s16le",
#         str(dst),
#     ]
#     run(cmd)
#     return dst

# def transcribe_whisper(wav_path: Path) -> dict:
#     """Transcribe with Deepgram Whisper Cloud (whisper-large) and return JSON dict."""
#     load_dotenv()
#     key = os.getenv("DEEPGRAM_API_KEY", "").strip()
#     if not key:
#         raise SystemExit("Set DEEPGRAM_API_KEY in .env")

#     dg = DeepgramClient(key)

#     with open(wav_path, "rb") as f:
#         buf = f.read()

#     # Sentence-level chunks via utterances=True.
#     # (We deliberately do NOT force a language; Whisper can handle many languages.)
#     opts = PrerecordedOptions(
#         model="whisper-large",
#         utterances=True,
#         smart_format=True,    # nicer numbers, dates, casing, etc.
#         # diarize=False       # keep off to honor “only whisper-large + sentence chunks”
#     )

#     print(f"Transcribing {wav_path.name} with model=whisper-large …")
#     res = dg.listen.prerecorded.v("1").transcribe_file(
#         {"buffer": buf, "mimetype": "audio/wav"},
#         opts
#     )
#     return res.to_dict()

# def print_sentence_view(dg_json: dict) -> None:
#     utterances = dg_json.get("results", {}).get("utterances", [])
#     if not utterances:
#         print("(No utterances array returned; check options/model.)")
#         return

#     def t(x: float) -> str:
#         return f"{x:.2f}s"

#     print("\n=== Sentence-level transcript ===")
#     for u in utterances:
#         start = t(u.get("start", 0.0))
#         end = t(u.get("end", 0.0))
#         text = (u.get("transcript") or "").strip()
#         print(f"[{start}–{end}] {text}")

# def main():
#     ap = argparse.ArgumentParser(description="Convert to WAV and transcribe with Deepgram Whisper Large (utterances).")
#     ap.add_argument("input", type=Path, help="Path to input media (any format ffmpeg can read)")
#     ap.add_argument("--out-wav", type=Path, default=Path("converted.wav"), help="Output WAV path")
#     ap.add_argument("--save-json", type=Path, default=Path("transcript_full.json"), help="Where to save full JSON")
#     args = ap.parse_args()

#     if not args.input.exists():
#         raise SystemExit(f"Input not found: {args.input.resolve()}")

#     # 1) Convert to wav
#     wav_path = convert_to_wav(args.input, args.out_wav)
#     print(f"Converted to WAV: {wav_path.resolve()}")

#     # 2) Transcribe (utterances=true => sentence-like chunks)
#     dg_json = transcribe_whisper(wav_path)

#     # 3) Save full JSON
#     args.save_json.parent.mkdir(parents=True, exist_ok=True)
#     with open(args.save_json, "w", encoding="utf-8") as f:
#         json.dump(dg_json, f, ensure_ascii=False, indent=2)
#     print(f"Saved full JSON: {args.save_json.resolve()}")

#     # 4) Print sentence-level view
#     print_sentence_view(dg_json)
#     print("\nDone.")

# if __name__ == "__main__":
#     main()


import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions

def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg and ensure it's in PATH.", file=sys.stderr)
        raise
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
        raise

def convert_to_wav(src: Path, dst: Path, sr: int = 16000) -> Path:
    """Convert any audio/video to 16 kHz mono WAV (PCM s16le). Requires ffmpeg."""
    if dst.suffix.lower() != ".wav":
        dst = dst.with_suffix(".wav")
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-ac", "1",
        "-ar", str(sr),
        "-c:a", "pcm_s16le",
        str(dst),
    ]
    run(cmd)
    return dst

def transcribe_whisper(wav_path: Path, language: str = "auto", diarize: bool = False) -> dict:
    """
    Transcribe with Deepgram Whisper Cloud (whisper-large) and return JSON dict.

    language:
      - "auto" (default): let Whisper auto-detect the primary language
      - explicit code like "en", "hi", "de" ... to lock language
    diarize:
      - False by default; set True to get speaker labels
    """
    load_dotenv()
    key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not key:
        raise SystemExit("Set DEEPGRAM_API_KEY in .env")

    dg = DeepgramClient(key)

    with open(wav_path, "rb") as f:
        buf = f.read()

    params = dict(
        model="whisper-large",
        utterances=True,      # sentence-like chunks
        smart_format=True,    # nicer numbers, dates, casing, punctuation
        diarize=diarize,
    )
    if language and language.lower() != "auto":
        params["language"] = language  # lock language if provided

    opts = PrerecordedOptions(**params)

    print(f"Transcribing {wav_path.name} with model=whisper-large "
          f"(language={language}, diarize={diarize}) …")
    res = dg.listen.prerecorded.v("1").transcribe_file(
        {"buffer": buf, "mimetype": "audio/wav"},
        opts
    )
    return res.to_dict()

def print_sentence_view(dg_json: dict) -> None:
    utterances = dg_json.get("results", {}).get("utterances", [])
    if not utterances:
        print("(No utterances array returned; check options/model.)")
        return

    def t(x: float) -> str:
        return f"{x:.2f}s"

    print("\n=== Sentence-level transcript ===")
    for u in utterances:
        start = t(u.get("start", 0.0))
        end = t(u.get("end", 0.0))
        text = (u.get("transcript") or "").strip()
        spk = u.get("speaker")
        if spk:
            print(f"[{start}–{end}] {spk}: {text}")
        else:
            print(f"[{start}–{end}] {text}")

def main():
    ap = argparse.ArgumentParser(description="Convert to WAV and transcribe with Deepgram Whisper Large (utterances, optional diarization).")
    ap.add_argument("input", type=Path, help="Path to input media (any format ffmpeg can read)")
    ap.add_argument("--out-wav", type=Path, default=Path("converted.wav"), help="Output WAV path")
    ap.add_argument("--save-json", type=Path, default=Path("transcript_full.json"), help="Where to save full JSON")
    ap.add_argument("--language", default="auto",
                    help="Language: 'auto' (default) or ISO code like 'en','hi','de' to lock it")
    ap.add_argument("--diarize", action="store_true", help="Enable speaker diarization")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input.resolve()}")

    # 1) Convert to wav
    wav_path = convert_to_wav(args.input, args.out_wav)
    print(f"Converted to WAV: {wav_path.resolve()}")

    # 2) Transcribe (utterances=true => sentence-like chunks)
    dg_json = transcribe_whisper(wav_path, language=args.language, diarize=args.diarize)

    # 3) Save full JSON
    args.save_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.save_json, "w", encoding="utf-8") as f:
        json.dump(dg_json, f, ensure_ascii=False, indent=2)
    print(f"Saved full JSON: {args.save_json.resolve()}")

    # 4) Print sentence-level view
    print_sentence_view(dg_json)
    print("\nDone.")

if __name__ == "__main__":
    main()
