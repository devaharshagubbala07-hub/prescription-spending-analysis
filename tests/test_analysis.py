import unittest
from decimal import InvalidOperation
from analysis import normalize, bridge, cents, integer, INCRETINS

def row(manufacturer='Overall', **changes):
    value={'Brnd_Name':'Example','Gnrc_Name':'Semaglutide','Mftr_Name':manufacturer,'Tot_Spndng_2024':'120.50','Tot_Clms_2024':'11','Tot_Benes_2024':'7','Outlier_Flag_2024':'0'}
    value.update(changes);return value

class AnalysisTests(unittest.TestCase):
    def test_manufacturer_rows_do_not_double_count(self):
        records,q=normalize([row(),row('Manufacturer')]);self.assertEqual(sum(r['spend_cents'] for r in records),12050)
        self.assertEqual(q['manufacturer_detail_rows'],1)
    def test_missing_history_remains_missing(self):
        records,q=normalize([row()]);self.assertEqual([r['year'] for r in records],[2024]);self.assertEqual(q['unavailable_product_years'][2023],1)
    def test_duplicate_overall_rows_fail(self):
        with self.assertRaises(ValueError):normalize([row(),row()])
    def test_dollars_and_counts_are_validated(self):
        self.assertEqual(cents('0.10'),10)
        for value in ('NaN','Infinity','-1'):
            with self.assertRaises(ValueError):cents(value)
        with self.assertRaises(ValueError):integer('2.5')
    def test_bridge_preserves_volume_and_average_components(self):
        b=bridge({'spend_cents':10000,'claims':10},{'spend_cents':16500,'claims':15})
        self.assertAlmostEqual(b['claims_component'],50);self.assertAlmostEqual(b['average_spend_component'],15);self.assertEqual(b['change'],65)
    def test_bridge_does_not_impute_missing_baseline(self):
        self.assertIsNone(bridge(None,{'spend_cents':100,'claims':1}))
    def test_cohort_uses_exact_ingredients(self):
        self.assertNotIn('teduglutide',INCRETINS);self.assertNotIn('insulin degludec/liraglutide',INCRETINS);self.assertIn('tirzepatide',INCRETINS)

if __name__=='__main__':unittest.main()
