import pathlib
import sys
import unittest

from pydantic import ValidationError

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import schemas  # noqa: E402


class SchemaValidationTests(unittest.TestCase):
    def test_session_rejects_impossible_energy(self):
        with self.assertRaises(ValidationError):
            schemas.SessionCreate(
                date="2026-05-17",
                session_type="gi",
                duration_minutes=60,
                energy_level=11,
            )

    def test_roll_rejects_unknown_outcome(self):
        with self.assertRaises(ValidationError):
            schemas.RollLogCreate(
                session_id="session-1",
                partner="Alex",
                gi_nogi="gi",
                outcome="vibes_win",
            )

    def test_legacy_seed_values_still_serialize(self):
        session = schemas.SessionResponse(
            session_id="session-1",
            date="2026-05-17",
            session_type="gi",
            duration_minutes=60,
            energy_level=8,
            created_at="2026-05-17T12:00:00",
        )
        technique = schemas.TechniqueResponse(
            technique_id="tech-1",
            name="Knee cut",
            category="passing",
            direction="left",
            gi_nogi="no_gi",
            date_added="2026-05-17",
        )
        roll = schemas.RollLogResponse(
            roll_id="roll-1",
            session_id="session-1",
            partner="Alex",
            gi_nogi="gi",
            outcome="competitive",
        )

        self.assertEqual(session.energy_level, 8)
        self.assertEqual(technique.gi_nogi, "no_gi")
        self.assertEqual(roll.outcome, "competitive")

    def test_mutable_list_defaults_are_isolated(self):
        first = schemas.TechniqueCreate(name="Armbar", category="submission")
        second = schemas.TechniqueCreate(name="Triangle", category="submission")

        first.tags.append("guard")

        self.assertEqual(second.tags, [])


class SourceContractTests(unittest.TestCase):
    def test_dashboard_recent_sessions_uses_backend_field_names(self):
        dashboard = (ROOT / "frontend" / "src" / "pages" / "Dashboard.jsx").read_text()

        self.assertIn("session.session_type", dashboard)
        self.assertIn("session.duration_minutes", dashboard)
        self.assertIn("parseISO(session.date)", dashboard)
        self.assertNotIn("s.type", dashboard)
        self.assertNotIn("s.duration}", dashboard)

    def test_oura_sync_translates_http_errors(self):
        oura = (ROOT / "backend" / "routers" / "oura.py").read_text()

        self.assertIn("except httpx.TimeoutException", oura)
        self.assertIn("raise_oura_error", oura)
        self.assertIn("status_code == 401", oura)


if __name__ == "__main__":
    unittest.main()
