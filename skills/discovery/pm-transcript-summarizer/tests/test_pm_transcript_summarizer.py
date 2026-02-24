import json
import os
import sys
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "scripts", "pm_transcript_summarizer.py"
)
SPEC = spec_from_file_location("pm_transcript_summarizer", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load pm_transcript_summarizer module")
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

build_report = MODULE.build_report
format_timestamp = MODULE.format_timestamp
parse_timestamp = MODULE.parse_timestamp
parse_transcript = MODULE.parse_transcript
run = MODULE.run
to_markdown = MODULE.to_markdown


class SummarizerTests(unittest.TestCase):
    def setUp(self):
        self.sample_lines = [
            "[00:10] PM: We are seeing onboarding dropoff because customers are confused about setup.\n",
            "[00:48] Eng: We should ship a setup wizard experiment next sprint and assign an owner.\n",
            "[01:20] Design: The roadmap tradeoff is speed versus discoverability for new users.\n",
            "[02:05] PM: Our target is improving activation conversion by 12 percent this quarter.\n",
            "[02:58] Legal: There is a compliance risk if we collect that data without consent.\n",
        ]

    def test_parse_timestamp(self):
        self.assertEqual(parse_timestamp("01:02"), 62)
        self.assertEqual(parse_timestamp("01:01:02"), 3662)

    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(62), "00:01:02")
        self.assertEqual(format_timestamp(3662), "01:01:02")

    def test_parse_transcript_and_report(self):
        entries = parse_transcript(self.sample_lines)
        self.assertEqual(len(entries), 5)

        report = build_report(entries, max_points=5, max_ideas=3)

        self.assertIn("pm_summary", report)
        self.assertGreaterEqual(len(report["key_talking_points"]), 2)
        self.assertGreaterEqual(len(report["big_ideas"]), 2)

        categories = {p["category"] for p in report["key_talking_points"]}
        self.assertTrue(
            {"Customer Problem", "Metrics & Outcomes", "Risks & Dependencies"}.intersection(categories)
        )

    def test_markdown_render(self):
        entries = parse_transcript(self.sample_lines)
        report = build_report(entries, max_points=5, max_ideas=3)
        md = to_markdown(report)
        self.assertIn("# PM Transcript Summary", md)
        self.assertIn("## Key Talking Points", md)
        self.assertIn("## Big Ideas", md)

    def test_cli_run_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "transcript.txt")
            out = os.path.join(tmp, "summary.json")
            with open(inp, "w", encoding="utf-8") as f:
                f.writelines(self.sample_lines)

            run(
                output_path=out,
                max_points=5,
                max_ideas=3,
                output_format="json",
                input_path=inp,
            )

            with open(out, "r", encoding="utf-8") as f:
                payload = json.load(f)

            self.assertIn("pm_summary", payload)
            self.assertIn("key_talking_points", payload)
            self.assertIn("big_ideas", payload)
            self.assertGreater(len(payload["key_talking_points"]), 0)

    def test_cli_run_from_source_url_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_json = os.path.join(tmp, "transcript.json")
            out = os.path.join(tmp, "summary.json")
            payload = {
                "transcript": [
                    {
                        "timestamp": "00:10",
                        "speaker": "PM",
                        "text": "Customers are confused in onboarding and support tickets are rising.",
                    },
                    {
                        "timestamp": "01:05",
                        "speaker": "Engineering",
                        "text": "We should prioritize a setup wizard in next sprint with one owner.",
                    },
                ]
            }
            with open(source_json, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            url = Path(source_json).as_uri()
            run(
                output_path=out,
                max_points=5,
                max_ideas=3,
                output_format="json",
                source_url=url,
            )

            with open(out, "r", encoding="utf-8") as f:
                result = json.load(f)

            self.assertIn("pm_summary", result)
            self.assertGreater(len(result["key_talking_points"]), 0)


if __name__ == "__main__":
    unittest.main()
