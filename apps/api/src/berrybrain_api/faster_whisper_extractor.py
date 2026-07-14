from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def transcribe(input_path: Path, model_path: str) -> dict[str, object]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(
        str(input_path),
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    segments: list[dict[str, object]] = []
    confidences: list[float] = []
    for segment in segments_iter:
        text = str(segment.text or "").strip()
        if not text:
            continue
        confidence = max(0.0, min(1.0, math.exp(float(segment.avg_logprob))))
        confidences.append(confidence)
        segments.append(
            {
                "start": round(float(segment.start), 3),
                "end": round(float(segment.end), 3),
                "text": text,
                "confidence": round(confidence, 4),
            }
        )
    return {
        "language": str(info.language or ""),
        "language_probability": round(float(info.language_probability or 0.0), 4),
        "confidence": round(sum(confidences) / len(confidences), 4)
        if confidences
        else 0.0,
        "segments": segments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    payload = transcribe(Path(args.input).resolve(), args.model)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
