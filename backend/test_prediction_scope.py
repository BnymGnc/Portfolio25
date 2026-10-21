import unittest
from pilot_kayseri import create_pilot
from profiles import generate_profiles
from interventions import candidates
import synthetic_ml

class PredictionScopeTests(unittest.TestCase):
    def test_office_combined_compares_total_annual_gas_and_exact_action_flags(self):
        c=create_pilot()[2];b=c.buildings[0]
        profile=next(p for p in candidates(b,generate_profiles(b,c.profile_settings),c.scenario) if p.report.package=='combined')
        context={'project_id':c.id,'input_revision':1,'input_hash':'test-only','engine_version':'test-only','calculation_id':None}
        result=synthetic_ml.predict(b,profile,context,2025)
        self.assertEqual(result.status,'available');self.assertEqual(result.year,2025)
        inputs=result.input_features
        self.assertEqual(inputs['action_insulation'],1);self.assertEqual(inputs['action_heat_pump'],1)
        for key in ('action_roof','action_lighting','action_schedule'):self.assertEqual(inputs[key],0)
        self.assertEqual(inputs['heating_gas'],b.heating_kwh_year);self.assertEqual(inputs['other_gas'],b.non_heating_gas_kwh_year)
        self.assertEqual(result.physics_result.non_heating_gas_kwh_year,b.non_heating_gas_kwh_year)
        gas_reference=profile.report.heating_gas_kwh_year+b.non_heating_gas_kwh_year
        self.assertAlmostEqual(result.difference.gas_kwh_year,result.prediction.gas_kwh_year-gas_reference)
        self.assertAlmostEqual(result.difference.electricity_kwh_year,result.prediction.electricity_kwh_year-profile.report.electricity_kwh_year)
        # Output indices must match the persisted training target schema, not heat.
        self.assertEqual(synthetic_ml.metadata()['targets'],['electricity_kwh_year','gas_kwh_year'])
        x=synthetic_ml.features(b,{'insulation','heat_pump'},2025)
        import joblib
        model=joblib.load(synthetic_ml.ASSET_DIR/'model.joblib')
        y=model.predict([x])[0]
        self.assertAlmostEqual(result.prediction.gas_kwh_year,y[1]);self.assertAlmostEqual(result.prediction.electricity_kwh_year,y[0])

if __name__=='__main__':unittest.main()
