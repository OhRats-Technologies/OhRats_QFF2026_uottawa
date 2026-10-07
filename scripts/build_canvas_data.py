"""Export public development inputs and saved selector costs for the browser game."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'docs/data/forest_selector_scaling_training.csv'
saved = json.loads((ROOT / 'web/demo/console/evidence.json').read_text())
rows = list(csv.DictReader(source.open()))
features = saved['features']
output = {
    'features': features,
    'rows': [{'year': int(row['year']), 'y': float(row['mean_reported_size_ha']),
              'x': [float(row[f['id']]) if row[f['id']] else None for f in features]}
             for row in rows],
    'rounds': [{'trainEnd': r['fold'][1], 'years': r['years'],
                'objective': r['objective'],
                'selectors': {m['id']: [next(i for i, f in enumerate(features)
                                    if f['id'] == name) for name in m['features']]
                              for m in r['models'] if m['id'] in ['mi', 'exact', 'optimized1', 'uniform']}}
               for r in saved['rounds']],
    'source': str(source.relative_to(ROOT)),
    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'scope': 'Browser teaching sandbox; inspected 1988–2018 development data. No research promotion or QPU calls.'
}
(ROOT / 'web/demo/canvas/data.json').write_text(json.dumps(output, separators=(',', ':')) + '\n')
print('Exported 31 public development rows, 20 inputs and three saved objectives.')
