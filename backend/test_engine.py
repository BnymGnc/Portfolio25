import itertools
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

import main
from engine import PACKAGES, calculate, calculate_package, prepare, solve_packages, summarize
from models import Building, CalculationRequest, ProfileSettings, Provenance, RetrofitAssumptions, Scenario
from profiles import AnnualProfiles, audit_profiles, generate_profiles
from sample_data import create_sample_campus


def toy_building(index=1):
    return Building(id=f"B{index:02d}", name=f"Elle kontrol {index}", use_type="Eğitim", area_m2=100,
                    year_built=2000, electricity_kwh_year=400, heating_kwh_year=1000,
                    non_heating_gas_kwh_year=100, peak_electric_kw=999, connection_limit_kw=200,
                    provenance=Provenance(kind="synthetic", source="Dört saatlik test örneği", seed=25),
                    retrofit=RetrofitAssumptions(boiler_efficiency=.8, insulation_relevant_heat_fraction=.5,
                        insulation_reduction_fraction=.4, heat_pump_scop=4, heat_pump_coverage_fraction=.75,
                        heat_pump_capacity_kw_thermal=100, insulation_cost_try_m2=10,
                        heat_pump_cost_try_kw=20, heat_pump_fixed_cost_try=100, annual_maintenance_fraction=.01))


def toy_profile(electricity=None, heat=None):
    return AnnualProfiles(tuple(f"2025-01-01T{h:02d}:00:00+03:00" for h in range(4)),
                          np.array([100., 100., 100., 100.] if electricity is None else electricity, dtype=float),
                          np.array([200., 200., 200., 200.] if heat is None else heat, dtype=float))


def toy_scenario():
    return Scenario(budget_try=5000, savings_target_pct=20, electric_capacity_kw=300,
                    electricity_price_try_kwh=2, heating_price_try_kwh=1)


class PhysicsTests(unittest.TestCase):
    def test_hand_calculation_and_capacity_backup(self):
        b, s = toy_building(), toy_scenario()
        p = calculate_package(b, toy_profile(), s, "combined")
        # Gas heat 1000*.8=800; insulation affects .5*.4 of it =>640.
        # Eligible 480, but 100 kW *4h=400 served; 240 heat remains on boiler.
        expected = {"useful_heat_before_kwh_year": 800, "useful_heat_after_kwh_year": 640,
                    "heat_pump_heat_kwh_year": 400, "heat_pump_electricity_kwh_year": 100,
                    "backup_boiler_heat_kwh_year": 240, "heating_gas_kwh_year": 300,
                    "non_heating_gas_kwh_year": 100, "electricity_kwh_year": 500,
                    "investment_try": 3100, "maintenance_cost_try_year": 31,
                    "energy_savings_kwh_year": 600, "net_savings_try_year": 469,
                    "electric_peak_kw": 125, "unmet_heat_kwh_year": 0}
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertAlmostEqual(getattr(p.report, key), value)
        self.assertAlmostEqual(p.report.simple_payback_years, 3100 / 469)
        np.testing.assert_allclose(p.heat_pump_heat_kw + p.backup_heat_kw, p.useful_heat_kw)
        self.assertTrue(np.all(p.heat_pump_heat_kw <= 100))

    def test_combined_is_not_sum_of_savings(self):
        b, s = toy_building(), toy_scenario()
        b.retrofit.heat_pump_capacity_kw_thermal = 200
        reports = {name: calculate_package(b, toy_profile(), s, name).report for name in PACKAGES}
        self.assertAlmostEqual(reports["insulation"].energy_savings_kwh_year, 200)
        self.assertAlmostEqual(reports["heat_pump"].energy_savings_kwh_year, 600)
        self.assertAlmostEqual(reports["combined"].energy_savings_kwh_year, 680)
        self.assertNotEqual(680, 200 + 600)

    def test_negative_economics_not_hidden(self):
        s = toy_scenario()
        s.electricity_price_try_kwh = 10
        report = calculate_package(toy_building(), toy_profile(), s, "combined").report
        self.assertAlmostEqual(report.net_savings_try_year, -331)
        self.assertIsNone(report.simple_payback_years)

    def test_insulation_only_affects_related_heating(self):
        b, s = toy_building(), toy_scenario()
        b.retrofit.insulation_relevant_heat_fraction = 0
        report = calculate_package(b, toy_profile(), s, "insulation").report
        self.assertAlmostEqual(report.heating_gas_kwh_year, 1000)
        self.assertEqual(report.non_heating_gas_kwh_year, 100)
        self.assertEqual(report.electricity_kwh_year, 400)
        b.retrofit.heat_pump_capacity_kw_thermal = 0
        pump = calculate_package(b, toy_profile(), s, "heat_pump").report
        self.assertEqual(pump.heat_pump_heat_kwh_year, 0)
        self.assertAlmostEqual(pump.backup_boiler_heat_kwh_year, 800)

    def test_no_intervention_has_exactly_zero_savings(self):
        campus = create_sample_campus()
        for building in campus.buildings:
            report = calculate_package(building, generate_profiles(building, campus.profile_settings), campus.scenario, "none").report
            self.assertEqual(report.energy_savings_kwh_year, 0)
            self.assertEqual(report.net_savings_try_year, 0)
            self.assertIsNone(report.simple_payback_years)

    def test_hourly_annual_consistency_seed_and_leap_year(self):
        c = create_sample_campus()
        for year, hours in [(2025, 8760), (2024, 8784)]:
            c.profile_settings.year = year
            profiles = [generate_profiles(b, c.profile_settings) for b in c.buildings]
            audit = audit_profiles(c, profiles)
            self.assertEqual(audit.hour_count, hours)
            self.assertTrue(audit.all_consistent)
            self.assertTrue(audit.start.endswith("+03:00"))
            for b, p in zip(c.buildings, profiles):
                self.assertAlmostEqual(float(p.electricity_kw.sum()), b.electricity_kwh_year, places=6)
                self.assertAlmostEqual(float(p.useful_heat_kw.sum()), b.heating_kwh_year * b.retrofit.boiler_efficiency, places=6)
                np.testing.assert_array_equal(p.electricity_kw, generate_profiles(b, c.profile_settings).electricity_kw)
        c.profile_settings.seed = 42
        changed = generate_profiles(c.buildings[0], c.profile_settings)
        self.assertFalse(np.array_equal(changed.electricity_kw, profiles[0].electricity_kw))

    def test_aligned_peaks_and_area_weighted_intensity(self):
        a, b, s = toy_building(1), toy_building(2), toy_scenario()
        a.area_m2, b.area_m2 = 100, 900
        ps = [calculate_package(a, toy_profile([100, 0, 0, 0]), s, "none"),
              calculate_package(b, toy_profile([0, 100, 0, 0]), s, "none")]
        summary = summarize([a, b], ps, s)
        self.assertEqual(summary.electric_peak_kw, 100)
        self.assertEqual(summary.electric_peak_sum_kw, 200)
        self.assertAlmostEqual(summary.intensity_kwh_m2_year, summary.total_energy_kwh_year / 1000)
        self.assertEqual(summary.electric_peak_timestamp, "2025-01-01T00:00:00+03:00")
        ps[1].timestamps = tuple(reversed(ps[1].timestamps))
        with self.assertRaises(ValueError):
            summarize([a, b], ps, s)


class OptimizerTests(unittest.TestCase):
    def setup_example(self):
        buildings = [toy_building(1), toy_building(2)]
        s = toy_scenario()
        profiles = [toy_profile(), toy_profile([20, 80, 180, 120], [320, 280, 120, 80])]
        options = [[calculate_package(b, p, s, name) for name in PACKAGES] for b, p in zip(buildings, profiles)]
        return buildings, s, options

    def test_both_modes_match_exhaustive_enumeration(self):
        buildings, s, options = self.setup_example()
        baseline = summarize(buildings, [g[0] for g in options], s)
        for mode in ("A", "B"):
            feasible = []
            for combination in itertools.product(*options):
                cost = sum(p.report.investment_try for p in combination)
                saving = sum(p.report.energy_savings_kwh_year for p in combination)
                loads = sum((p.electricity_kw for p in combination), np.zeros(4))
                if cost > s.budget_try or loads.max() > s.electric_capacity_kw:
                    continue
                if any(p.electricity_kw.max() > b.connection_limit_kw for b, p in zip(buildings, combination)):
                    continue
                if mode == "B" and saving < baseline.total_energy_kwh_year * s.savings_target_pct / 100:
                    continue
                feasible.append((cost, saving))
            self.assertTrue(feasible)
            result = solve_packages(buildings, options, s, CalculationRequest(revision=1, mode=mode))
            self.assertEqual(result.status, "optimal")
            self.assertTrue(result.solver.optimality_proven)
            self.assertEqual(len(result.selected_packages), 2)
            self.assertLessEqual(result.after.electric_peak_kw, s.electric_capacity_kw + 1e-6)
            if mode == "A":
                self.assertAlmostEqual(result.energy_savings_kwh_year, max(saving for cost, saving in feasible))
            else:
                self.assertAlmostEqual(result.investment_try, min(cost for cost, saving in feasible))
                self.assertTrue(result.target_met)

    def test_mode_b_enforces_budget_and_reports_infeasible(self):
        buildings, s, options = self.setup_example()
        s.budget_try = 0
        r = solve_packages(buildings, options, s, CalculationRequest(revision=1, mode="B"))
        self.assertEqual(r.status, "infeasible")
        self.assertIsNone(r.after)
        self.assertEqual(r.selected_packages, [])
        self.assertIsNone(r.target_met)

    def test_separate_building_and_campus_limits(self):
        buildings, s, options = self.setup_example()
        buildings[0].connection_limit_kw = 90
        r = solve_packages(buildings, options, s, CalculationRequest(revision=1))
        self.assertEqual(r.status, "infeasible")
        buildings[0].connection_limit_kw = 200
        s.electric_capacity_kw = 1
        r = solve_packages(buildings, options, s, CalculationRequest(revision=1))
        self.assertEqual(r.status, "infeasible")

    def test_staggered_peaks_are_feasible(self):
        a, b, s = toy_building(1), toy_building(2), toy_scenario()
        s.electric_capacity_kw, s.budget_try = 100, 0
        groups = [[calculate_package(x, p, s, "none")] for x, p in
                  [(a, toy_profile([100, 0, 0, 0])), (b, toy_profile([0, 100, 0, 0]))]]
        r = solve_packages([a, b], groups, s, CalculationRequest(revision=1))
        self.assertEqual(r.status, "optimal")
        self.assertEqual(r.after.electric_peak_kw, 100)

    def test_limits_and_unverified_candidates_not_labeled_optimum(self):
        buildings, s, options = self.setup_example()
        candidate = np.array([1, 0, 0, 0, 1, 0, 0, 0])
        with patch("engine.milp", return_value=SimpleNamespace(status=1, message="Time limit", x=candidate, mip_gap=.5)):
            r = solve_packages(buildings, options, s, CalculationRequest(revision=1, time_limit_s=.01))
        self.assertEqual(r.status, "feasible_limit")
        self.assertFalse(r.solver.optimality_proven)
        self.assertEqual(r.solver.time_limit_s, .01)
        self.assertEqual(r.solver.mip_gap, .5)
        with patch("engine.milp", return_value=SimpleNamespace(status=1, message="Time limit", x=None)):
            r = solve_packages(buildings, options, s, CalculationRequest(revision=1))
        self.assertEqual(r.status, "limit_no_solution")
        self.assertIsNone(r.after)
        with patch("engine.milp", return_value=SimpleNamespace(status=0, message="bad candidate", x=candidate * .5)):
            r = solve_packages(buildings, options, s, CalculationRequest(revision=1))
        self.assertEqual(r.status, "failed")
        s.budget_try = 0
        candidate = np.array([0, 0, 0, 1, 1, 0, 0, 0])
        with patch("engine.milp", return_value=SimpleNamespace(status=0, message="bad feasibility", x=candidate)):
            r = solve_packages(buildings, options, s, CalculationRequest(revision=1))
        self.assertEqual(r.status, "failed")

    def test_reproducible_actual_milp_and_zero_energy(self):
        c = create_sample_campus()
        request = CalculationRequest(revision=c.revision)
        a, b = calculate(c, request), calculate(c, request)
        self.assertEqual([(p.building_id, p.package) for p in a.selected_packages],
                         [(p.building_id, p.package) for p in b.selected_packages])
        c.scenario.budget_try = 0
        for building in c.buildings:
            building.electricity_kwh_year = building.heating_kwh_year = building.non_heating_gas_kwh_year = 0
        r = calculate(c, CalculationRequest(revision=c.revision, mode="B"))
        self.assertEqual(r.status, "optimal")
        self.assertIsNone(r.energy_savings_pct)
        self.assertIsNone(r.simple_payback_years)
        self.assertTrue(r.target_met)


class StageTwoApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = main.DATA_FILE
        main.DATA_FILE = Path(self.temp.name) / "campus.json"
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.DATA_FILE = self.previous
        self.temp.cleanup()

    def test_v1_migration_backup_and_legacy_put_preserves_v2_fields(self):
        c = create_sample_campus().model_dump(mode="json")
        for key in ("profile_settings", "migration_notes"):
            c.pop(key)
        c["schema_version"], c["optimization_status"] = "1.0", "not_implemented"
        for b in c["buildings"]:
            for key in ("connection_limit_kw", "non_heating_gas_kwh_year", "retrofit"):
                b.pop(key)
        for key in ("price_basis", "emission_basis", "electricity_emission_kg_kwh", "gas_emission_kg_kwh"):
            c["scenario"].pop(key)
        main.DATA_FILE.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        migrated = self.client.get("/api/campus").json()["campus"]
        self.assertEqual(migrated["revision"], 2)
        self.assertEqual(migrated["schema_version"], "3.0")
        self.assertEqual(migrated["buildings"][0]["electricity_kwh_year"], c["buildings"][0]["electricity_kwh_year"])
        self.assertEqual(migrated["buildings"][0]["heating_kwh_year"], c["buildings"][0]["heating_kwh_year"])
        self.assertEqual(migrated["buildings"][0]["non_heating_gas_kwh_year"], 0)
        self.assertEqual(json.loads(main.DATA_FILE.with_name("campus.v1-backup.json").read_text(encoding="utf-8")), c)
        self.assertEqual(self.client.get("/api/campus").json()["campus"]["revision"], 2)
        # First store an explicit v2 value; then submit a legacy-shaped client update.
        migrated["buildings"][0]["retrofit"]["heat_pump_scop"] = 4.1
        body = {k: migrated[k] for k in ("revision", "buildings", "scenario")}
        self.assertEqual(self.client.put("/api/campus", json=body).status_code, 200)
        legacy = {"revision": 3, "buildings": c["buildings"], "scenario": c["scenario"]}
        saved = self.client.put("/api/campus", json=legacy).json()["campus"]
        self.assertEqual(saved["buildings"][0]["retrofit"]["heat_pump_scop"], 4.1)

    def test_calculation_persist_export_and_invalidation(self):
        c = self.client.get("/api/campus").json()["campus"]
        result = self.client.post("/api/calculate", json={"revision": c["revision"], "mode": "A"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["status"], "optimal")
        self.assertTrue(main.result_path().exists())
        loaded = self.client.get("/api/campus").json()
        self.assertEqual(loaded["calculation"], result.json())
        self.assertEqual(len(loaded["investment_plan"]), 8)
        self.assertEqual(self.client.get("/api/export/json").json()["calculation"], result.json())
        self.assertIn("combined", self.client.get("/api/export/csv").text)
        c["scenario"]["electricity_price_try_kwh"] = 9
        self.client.put("/api/campus", json={k: c[k] for k in ("revision", "buildings", "scenario")})
        self.assertIsNone(self.client.get("/api/campus").json()["calculation"])
        self.assertEqual(self.client.post("/api/calculate", json={"revision": 1}).status_code, 409)

    def test_hourly_api_and_assumption_validation(self):
        c = self.client.get("/api/campus").json()["campus"]
        result = self.client.get("/api/buildings/B01/profiles?package=combined")
        self.assertEqual(result.status_code, 200)
        p = result.json()
        self.assertEqual(len(p["timestamps"]), 8760)
        self.assertTrue(p["timestamps"][0].endswith("+03:00"))
        self.assertAlmostEqual(sum(p["baseline_electricity_kw"]), c["buildings"][0]["electricity_kwh_year"], places=5)
        self.assertAlmostEqual(sum(p["electricity_kw"]), p["summary"]["electricity_kwh_year"], places=5)
        self.assertEqual(self.client.get("/api/buildings/B99/profiles").status_code, 404)
        self.assertEqual(self.client.get("/api/buildings/B01/profiles?package=invalid").status_code, 422)
        c["buildings"][0]["retrofit"]["boiler_efficiency"] = 0
        self.assertEqual(self.client.put("/api/campus", json={k: c[k] for k in ("revision", "buildings", "scenario")}).status_code, 422)
        self.assertEqual(self.client.post("/api/calculate", json={"revision": 1, "time_limit_s": 100}).status_code, 422)

    def test_edit_during_calculation_does_not_store_stale_result(self):
        c = self.client.get("/api/campus").json()["campus"]
        def changed(campus, request):
            result = calculate(campus, request)
            campus.revision += 1
            main.write_campus(campus)
            return result
        with patch("main.calculate", side_effect=changed):
            response = self.client.post("/api/calculate", json={"revision": c["revision"]})
        self.assertEqual(response.status_code, 409)
        self.assertFalse(main.result_path().exists())


if __name__ == "__main__":
    unittest.main()


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
