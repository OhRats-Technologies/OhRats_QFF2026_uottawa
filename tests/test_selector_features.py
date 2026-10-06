"""Check candidate expansion against audited prior-epoch means and lag identities."""
import json
import unittest
from pathlib import Path
import pandas as pd
from wildfire_lab.selector_features import FEATURES, SPECIES, expand

ROOT = Path(__file__).resolve().parents[1]


class FeatureTests(unittest.TestCase):
    def test_actual_training_source_join(self):
        original = pd.read_csv(ROOT/'docs/data/forest_expansion_training.csv')
        summary = json.loads((ROOT/'docs/data/forest_feature_summary.json').read_text())
        result = expand(original, summary)
        self.assertEqual(len(FEATURES),20)
        self.assertEqual(len(set(FEATURES)),20)
        self.assertEqual(result.year.tolist(),list(range(1988,2019)))
        self.assertTrue(pd.isna(result.lag_recorded_incidents.iloc[0]))
        self.assertEqual(result.lag_recorded_incidents.iloc[1],original.recorded_incidents.iloc[0])
        for year in [1988,1990,1991,2018]:
            row = result[result.year==year].iloc[0]
            self.assertLess(row.forest_epoch,year)
            for column,layer in zip(SPECIES,['broadleaf','black_spruce','jack_pine']):
                source = next(r for r in summary['rows'] if r['epoch']==row.forest_epoch and r['layer']==layer)
                self.assertEqual(row[column],source['mean'])

    def test_lag_does_not_shift_across_gaps(self):
        summary = {'rows':[dict(epoch=1985,layer=layer,model_eligible=True,mean=5.)
                           for layer in ['broadleaf','black_spruce','jack_pine']]}
        table = pd.DataFrame(dict(year=[1988,1990],forest_epoch=[1985,1985],recorded_incidents=[8,9]))
        self.assertTrue(expand(table,summary).lag_recorded_incidents.isna().all())


if __name__ == '__main__':
    unittest.main()
