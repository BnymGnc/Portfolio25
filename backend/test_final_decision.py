import unittest
from pydantic import ValidationError
from sample_data import create_sample_campus
from models import Campus, CalculationRequest
from engine import calculate

class FinalDecisionTests(unittest.TestCase):
    def test_legacy_sources_and_explicit_source_roundtrip(self):
        raw=create_sample_campus().model_dump(mode='json')
        for b in raw['buildings']:b.pop('field_sources',None)
        c=Campus.model_validate(raw)
        self.assertEqual(c.buildings[0].field_sources,{})
        c.buildings[0].field_sources={'area':'measured','scop':'user_estimate'}
        self.assertEqual(Campus.model_validate_json(c.model_dump_json()).buildings[0].field_sources,c.buildings[0].field_sources)
        raw['buildings'][0]['field_sources']={'scop':'confidence_99'}
        with self.assertRaises(ValidationError):Campus.model_validate(raw)

    def test_ratio_target_zero_stops_and_evaluations_reconcile(self):
        c=create_sample_campus();c.scenario.savings_target_pct=0
        r=calculate(c,CalculationRequest(revision=c.revision,mode='B'))
        methods=r.decision_evidence['methods']
        self.assertEqual(methods['ratio']['evaluation']['investment_try'],0)
        for method in methods.values():
            v=method['evaluation']
            if v:
                self.assertAlmostEqual(v['after']['total_energy_kwh_year']/sum(b.area_m2 for b in c.buildings),v['after']['intensity_kwh_m2_year'])
                self.assertAlmostEqual(v['net_savings_try_year'],r.baseline.operating_cost_try_year-v['after']['operating_cost_try_year'])
                self.assertAlmostEqual(v['investment_try']+v['budget_remaining_try'],c.scenario.budget_try)

if __name__=='__main__':unittest.main()
