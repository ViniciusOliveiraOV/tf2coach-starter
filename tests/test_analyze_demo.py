from __future__ import annotations

import json
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_demo import AnalysisError, build_analysis, cli, render_report  # noqa: E402


FIXTURE = Path(__file__).parent / "fixtures" / "anonymized_demo_summary.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class AnalyzeDemoTests(unittest.TestCase):
    def test_counts_only_events_for_uniquely_identified_pov_player(self):
        result = build_analysis(load_fixture())

        self.assertEqual(result["metrics"], {
            "kills": 2,
            "deaths": 2,
            "assists": 1,
            "self_eliminations": 1,
        })
        self.assertEqual(result["weapon_counts"], {"rocketlauncher": 1, "world": 1})
        self.assertEqual(len(result["events"]), 5)
        self.assertEqual(result["events"][0], {
            "tick": 110,
            "roles": ["eliminação atribuída"],
            "weapon": "rocketlauncher",
        })
        self.assertEqual(result["events"][1]["roles"], ["morte"])
        self.assertNotIn("weapon", result["events"][1])
        self.assertEqual(result["event_window"], {
            "first_tick": 110,
            "last_tick": 180,
            "start_seconds": 0.15,
            "end_seconds": 1.2,
        })

    def test_explicit_steam_id_selects_player_without_printing_it(self):
        result = build_analysis(load_fixture(), steam_id="ANON_STEAM_B")

        self.assertEqual(result["metrics"], {
            "kills": 2,
            "deaths": 1,
            "assists": 1,
            "self_eliminations": 0,
        })
        report = render_report(result)
        self.assertNotIn("ANON_STEAM_B", report)

    def test_rejects_ambiguous_pov_name_without_explicit_identity(self):
        parsed = load_fixture()
        parsed["users"]["40"] = {
            **parsed["users"]["10"],
            "userId": 40,
            "steamId": "ANON_STEAM_D",
        }

        with self.assertRaisesRegex(AnalysisError, "--steam-id"):
            build_analysis(parsed)

    def test_report_excludes_personal_identifiers_and_chat(self):
        report = render_report(build_analysis(load_fixture()))

        for private_value in (
            "POV_A",
            "THIRD_PARTY",
            "ANON_STEAM_A",
            "ANON_STEAM_B",
            "PRIVATE_CHAT_MUST_NOT_APPEAR",
            "REDACTED",
        ):
            self.assertNotIn(private_value, report)
        self.assertIn("rocketlauncher", report)
        self.assertIn("`world`", report)
        self.assertIn("não comprovam uma arma equipada", report)
        self.assertIn("ctf_test", report)

    def test_missing_tick_timing_omits_derived_seconds(self):
        parsed = load_fixture()
        del parsed["startTick"]
        del parsed["intervalPerTick"]

        result = build_analysis(parsed)

        self.assertEqual(result["event_window"], {"first_tick": 110, "last_tick": 180})

    def test_missing_deaths_field_does_not_turn_unknown_metrics_into_zero(self):
        parsed = load_fixture()
        del parsed["deaths"]

        result = build_analysis(parsed)

        self.assertIsNone(result["metrics"])
        self.assertIn("métricas individuais não calculadas", render_report(result))

    def test_event_without_victim_does_not_add_an_elimination(self):
        parsed = load_fixture()
        parsed["deaths"].append({"killer": 10, "weapon": "unverified", "tick": 200})

        result = build_analysis(parsed)

        self.assertEqual(result["metrics"]["kills"], 2)

    def test_cli_preserves_existing_report_without_explicit_force(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            output.write_text("existing user report", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = cli([str(FIXTURE), "--output", str(output)])

            self.assertEqual(result, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing user report")

    def test_cli_never_overwrites_its_json_input(self):
        with tempfile.TemporaryDirectory() as directory:
            input_file = Path(directory) / "summary.json"
            input_file.write_bytes(FIXTURE.read_bytes())
            original = input_file.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = cli([
                    str(input_file), "--output", str(input_file), "--force"
                ])

            self.assertEqual(result, 2)
            self.assertEqual(input_file.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
