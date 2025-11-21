#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Adjust these imports to your actual filenames
# transcribe function you already have
from audio_to_transcribe_whisper import transcribe_audio_to_text
# the graph file you posted
from class_test_graph import run_tutor_pipeline

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python main.py /path/to/audio_or_video", file=sys.stderr)
        return 2

    in_path = Path(sys.argv[1])
    if not in_path.exists():
        print(f"ERROR: Input not found: {in_path.resolve()}", file=sys.stderr)
        return 2

    # Keep the same Deepgram-saving behavior next to the input
    out_wav   = in_path.with_suffix(".converted.wav")
    print(1)
    save_json = in_path.with_suffix(".deepgram.json")
    print(2)

    try:
        # 1) Transcribe to a single text string (JSON auto-saved as above)
        transcript = transcribe_audio_to_text(
            str(in_path),
            out_wav=str(out_wav),
            save_json=str(save_json),
            language="auto",
            diarize=False,
        )

        # 2) Run the tutor pipeline on the transcript
        result = run_tutor_pipeline(
            transcript=transcript,
            student_level="college",
            student_goal="score well in final exam and actually understand the concepts",
        )

        final_state      = result["final_state"]
        combined_md      = result["combined_markdown"]
        combined_json    = result["combined_json"]

        # 3) Save node outputs + combined views next to input file
        nodes_json_path     = in_path.with_suffix(".tutor.nodes.json")
        combined_md_path    = in_path.with_suffix(".tutor.combined.md")
        combined_json_path  = in_path.with_suffix(".tutor.combined.json")

        nodes_json_path.write_text(json.dumps(final_state, ensure_ascii=False, indent=2), encoding="utf-8")
        combined_md_path.write_text(combined_md, encoding="utf-8")
        combined_json_path.write_text(json.dumps(combined_json, ensure_ascii=False, indent=2), encoding="utf-8")

        # 4) Print the combined text to stdout (so you see something immediately)
        print("\n=== COMBINED OUTPUT ===\n")
        print(combined_md)

        # Optional: tell where files were saved (stderr so stdout stays clean if you pipe it)
        print(f"\nSaved:", file=sys.stderr)
        print(f" - Deepgram JSON:    {save_json.resolve()}", file=sys.stderr)
        print(f" - Tutor nodes JSON: {nodes_json_path.resolve()}", file=sys.stderr)
        print(f" - Combined MD:      {combined_md_path.resolve()}", file=sys.stderr)
        print(f" - Combined JSON:    {combined_json_path.resolve()}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
