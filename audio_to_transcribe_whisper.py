import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg and ensure it's in PATH.", file=sys.stderr)
        raise
    except subprocess.CalledProcessError:
        print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
        raise


def _convert_to_wav(src: Path, dst: Path, sr: int = 16000) -> Path:
    """
    Convert any audio/video to 16 kHz mono WAV (PCM s16le). Requires ffmpeg.
    """
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
    _run(cmd)
    return dst


def _transcribe_whisper(wav_path: Path, language: str = "auto", diarize: bool = False) -> dict:
    """
    Transcribe with Deepgram Whisper Cloud (whisper-large) and return JSON dict.

    language:
      - "auto" (default): auto-detect
      - ISO code like "en", "hi", "de" to lock it
    diarize:
      - False by default; True to get speaker labels
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
        params["language"] = language

    opts = PrerecordedOptions(**params)

    print(f"Transcribing {wav_path.name} with model=whisper-large "
          f"(language={language}, diarize={diarize}) …")
    res = dg.listen.prerecorded.v("1").transcribe_file(
        {"buffer": buf, "mimetype": "audio/wav"},
        opts
    )
    return res.to_dict()


def _extract_full_transcript(dg_json: dict) -> str:
    """
    Build a single plain-text transcript string from Deepgram JSON.
    Prefer utterances; fall back to channels/alternatives if needed.
    """
    results = dg_json.get("results", {})

    # 1) Prefer utterances (sentence-like)
    utterances = results.get("utterances", [])
    if isinstance(utterances, list) and utterances:
        parts = []
        for u in utterances:
            text = (u.get("transcript") or "").strip()
            if text:
                parts.append(text)
        if parts:
            return " ".join(parts).strip()

    # 2) Fallback to first channel/alternative transcript
    channels = results.get("channels", [])
    if isinstance(channels, list) and channels:
        alts = channels[0].get("alternatives", [])
        if isinstance(alts, list) and alts:
            text = (alts[0].get("transcript") or "").strip()
            if text:
                return text

    # 3) Nothing found
    return ""


def transcribe_audio_to_text(
    input_path: str,
    *,
    out_wav: Optional[str] = "converted.wav",
    save_json: Optional[str] = "transcript_full.json",
    language: str = "auto",
    diarize: bool = False
) -> str:
    """
    Convert input media to WAV, transcribe with Deepgram Whisper Large,
    save the full JSON to disk (same behavior as before), and return
    the full transcript as a single string.

    Args:
        input_path: Path to input media (any format ffmpeg can read)
        out_wav:    Path for intermediate WAV (default: 'converted.wav')
        save_json:  Path where the full JSON is saved (default: 'transcript_full.json')
        language:   'auto' or ISO code like 'en', 'hi', 'de'
        diarize:    If True, request speaker labels in JSON

    Returns:
        The complete transcript as a plain string ("" if none).
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Input not found: {src.resolve()}")

    # 1) Convert to wav
    wav_path = _convert_to_wav(src, Path(out_wav))
    print(f"Converted to WAV: {wav_path.resolve()}")

    # 2) Transcribe
    dg_json = _transcribe_whisper(wav_path, language=language, diarize=diarize)

    # 3) Save full JSON (same behavior)
    if save_json:
        save_path = Path(save_json)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(dg_json, f, ensure_ascii=False, indent=2)
        print(f"Saved full JSON: {save_path.resolve()}")

    # 4) Return full transcript as a single string
    return _extract_full_transcript(dg_json)
