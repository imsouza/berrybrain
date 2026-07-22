import json
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from berrybrain_api import faster_whisper_extractor


class FasterWhisperExtractorTest(unittest.TestCase):
    def _module_with_model(self, segments: list[object], info: object) -> ModuleType:
        module = ModuleType("faster_whisper")
        model = MagicMock()
        model.transcribe.return_value = (iter(segments), info)
        constructor = MagicMock(return_value=model)
        module.WhisperModel = constructor  # type: ignore[attr-defined]
        self.constructor = constructor
        self.model = model
        return module

    def test_transcribe_returns_timed_segments_and_mean_confidence(self) -> None:
        module = self._module_with_model(
            [
                SimpleNamespace(
                    text=" First idea ", start=0, end=1.23456, avg_logprob=-0.1
                ),
                SimpleNamespace(text="", start=1.2, end=2, avg_logprob=-9),
                SimpleNamespace(text="Second idea", start=2, end=3.5, avg_logprob=-0.3),
            ],
            SimpleNamespace(language="en", language_probability=0.98765),
        )

        with patch.dict(sys.modules, {"faster_whisper": module}):
            result = faster_whisper_extractor.transcribe(Path("audio.wav"), "small")

        self.constructor.assert_called_once_with(
            "small", device="cpu", compute_type="int8"
        )
        self.model.transcribe.assert_called_once_with(
            "audio.wav",
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["language_probability"], 0.9877)
        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(result["segments"][0]["end"], 1.235)
        self.assertGreater(result["confidence"], 0.8)

    def test_transcribe_handles_empty_metadata_and_segments(self) -> None:
        module = self._module_with_model(
            [], SimpleNamespace(language=None, language_probability=None)
        )
        with patch.dict(sys.modules, {"faster_whisper": module}):
            result = faster_whisper_extractor.transcribe(Path("empty.wav"), "tiny")

        self.assertEqual(
            result,
            {
                "language": "",
                "language_probability": 0.0,
                "confidence": 0.0,
                "segments": [],
            },
        )

    def test_cli_resolves_input_and_writes_json(self) -> None:
        payload = {"language": "en", "segments": []}
        with (
            patch.object(
                sys, "argv", ["extractor", "--input", "clip.wav", "--model", "base"]
            ),
            patch.object(
                faster_whisper_extractor, "transcribe", return_value=payload
            ) as transcribe,
            patch("builtins.print") as output,
        ):
            result = faster_whisper_extractor.main()

        self.assertEqual(result, 0)
        transcribe.assert_called_once_with(Path("clip.wav").resolve(), "base")
        self.assertEqual(json.loads(output.call_args.args[0]), payload)


if __name__ == "__main__":
    unittest.main()
