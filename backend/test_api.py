import csv
import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
from models import Campus
from sample_data import calculate_baseline, create_sample_campus


class CampusApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.previous_file = main.DATA_FILE
        main.DATA_FILE = Path(self.directory.name) / "campus.json"
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.DATA_FILE = self.previous_file
        self.directory.cleanup()

    def payload(self):
        campus = self.client.get("/api/campus").json()["campus"]
        return {key: campus[key] for key in ("revision", "buildings", "scenario")}

    def test_sample_is_deterministic_and_honest(self):
        self.assertEqual(create_sample_campus(), create_sample_campus())
        result = self.client.get("/api/campus")
        self.assertEqual(result.status_code, 200)
        body = result.json()
        self.assertEqual(len(body["campus"]["buildings"]), 8)
        self.assertEqual(body["campus"]["provenance"]["kind"], "synthetic")
        self.assertIsNone(body["after"])
        self.assertIsNone(body["investment_plan"])
        self.assertEqual(body["campus"]["optimization_status"], "ready")
        self.assertIsNone(body["calculation"])
        self.assertTrue(body["profile_audit"]["all_consistent"])

    def test_edit_is_persisted_and_baseline_recomputed(self):
        payload = self.payload()
        payload["buildings"][0]["name"] = "Örnek Düzenlenen Bina"
        payload["buildings"][0]["electricity_kwh_year"] += 10000
        payload["scenario"]["budget_try"] = 30000000
        payload["scenario"]["electric_capacity_kw"] = 1000
        saved = self.client.put("/api/campus", json=payload)
        self.assertEqual(saved.status_code, 200)
        body = saved.json()
        self.assertEqual(body["campus"]["revision"], 2)
        stored = Campus.model_validate_json(main.DATA_FILE.read_text(encoding="utf-8"))
        self.assertEqual(stored.buildings[0].name, "Örnek Düzenlenen Bina")
        baseline = calculate_baseline(stored)
        self.assertEqual(body["baseline"], baseline.model_dump())
        self.assertEqual(self.client.get("/api/campus").json(), body)

    def test_stale_revision_cannot_overwrite(self):
        payload = self.payload()
        self.assertEqual(self.client.put("/api/campus", json=payload).status_code, 200)
        self.assertEqual(self.client.put("/api/campus", json=payload).status_code, 409)
        self.assertEqual(self.client.get("/api/campus").json()["campus"]["revision"], 2)

    def test_invalid_inputs_rejected_without_mutation(self):
        invalid = [
            ("buildings", 0, "area_m2", 0),
            ("buildings", 0, "heating_kwh_year", -1),
            ("buildings", 0, "year_built", 2000.5),
            ("buildings", 0, "name", "   "),
            ("scenario", None, "budget_try", -1),
            ("scenario", None, "savings_target_pct", 101),
            ("scenario", None, "electric_capacity_kw", 0),
        ]
        for section, index, key, value in invalid:
            with self.subTest(key=key):
                payload = self.payload()
                target = payload[section] if index is None else payload[section][index]
                target[key] = value
                self.assertEqual(self.client.put("/api/campus", json=payload).status_code, 422)
                self.assertEqual(self.client.get("/api/campus").json()["campus"]["revision"], 1)

    def test_source_cannot_be_relabeled(self):
        for key, value in [("kind", "measured"), ("seed", 42), ("source", "Başka bir kaynak")]:
            payload = self.payload()
            payload["buildings"][0]["provenance"][key] = value
            self.assertEqual(self.client.put("/api/campus", json=payload).status_code, 422)

    def test_duplicate_or_missing_buildings_rejected(self):
        payload = self.payload()
        payload["buildings"][1]["id"] = "B01"
        self.assertEqual(self.client.put("/api/campus", json=payload).status_code, 422)
        payload["buildings"].pop()
        self.assertEqual(self.client.put("/api/campus", json=payload).status_code, 422)

    def test_baseline_formula_and_zero_energy(self):
        campus = create_sample_campus()
        baseline = calculate_baseline(campus)
        self.assertAlmostEqual(baseline.intensity_kwh_m2_year, baseline.total_energy_kwh_year / baseline.area_m2)
        self.assertAlmostEqual(baseline.operating_cost_try_year,
                               baseline.electricity_kwh_year * 4.5 + baseline.total_gas_kwh_year * 1.5)
        for building in campus.buildings:
            building.electricity_kwh_year = building.heating_kwh_year = building.peak_electric_kw = 0
            building.non_heating_gas_kwh_year = 0
        baseline = calculate_baseline(campus)
        self.assertEqual(baseline.total_energy_kwh_year, 0)
        self.assertEqual(baseline.capacity_utilization_pct, 0)

    def test_exports_contain_saved_inputs_and_provenance(self):
        payload = self.payload()
        payload["buildings"][0]["name"] = '=HYPERLINK("example")'
        self.client.put("/api/campus", json=payload)
        result = self.client.get("/api/export/csv")
        self.assertEqual(result.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(result.text.lstrip("\ufeff"))))
        self.assertEqual(len(rows), 8)
        self.assertTrue(rows[0]["name"].startswith("'="))
        self.assertEqual(rows[0]["data_kind"], "synthetic")
        self.assertEqual(rows[0]["budget_try"], "25000000.0")
        self.assertEqual(rows[0]["optimization_status"], "ready")
        self.assertEqual(rows[0]["solver_status"], "not_calculated")
        self.assertIn("attachment", result.headers["content-disposition"])
        result = self.client.get("/api/export/json").json()
        self.assertEqual(result["campus"]["revision"], 2)
        self.assertIsNone(result["after"])
        self.assertEqual(self.client.get("/api/export/pdf").status_code, 404)

    def test_cors_allows_configured_frontend(self):
        result = self.client.options("/api/campus", headers={
            "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "Content-Type",
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        result = self.client.get("/api/campus", headers={"Origin": "https://unconfigured.example"})
        self.assertNotIn("access-control-allow-origin", result.headers)


if __name__ == "__main__":
    unittest.main()


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
