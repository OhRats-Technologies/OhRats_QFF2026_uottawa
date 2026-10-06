"""Publish sanitized metadata and reproducible search-page screening."""
import argparse
import json
from collections import Counter
from pathlib import Path

from metadata import OWNER_IDS, read_package

ROOT = Path(__file__).resolve().parents[2]


def english(record, field):
    translated = record.get(field + '_translated', {})
    return translated.get('en') or translated.get('en-t-fr') or record.get(field, '')


def screen(record):
    title = english(record, 'title').lower()
    publisher = record.get('organization', {}).get('title', '')
    ontario = 'Ontario' in publisher or 'ontario' in title
    rules = [
        ('exclude:keyword_collision', ['fire lake', 'fire assaying', 'geochemistry', 'gold recovery', 'ring of', 'firing practice', 'weapons range', 'tobacco', 'traffic', 'engines', 'boilers', 'furnaces', 'water heaters', 'homicide', 'radar -', 'candle', 'consumer product', 'household chemical', 'railways', 'glimpce']),
        ('exclude:narrative_or_administration', ['news release', 'communiqué', 'bulletins', 'investigation', 'briefing', 'gazette', 'consultations', 'corrections:', 'council', 'registrant', 'performance measurement', 'charges', 'portable fire extinguisher', 'fund', 'montreal company', 'activist', 'agreements', 'aircraft', 'earthquake', 'seismic risk', 'regdoc', 'notice of danger']),
        ('urban_response', ['hydrant', 'fire station', 'barracks', 'firefighters', 'smoke alarm', 'sprinkler', 'fire-related death', 'type of structure', 'incident-based fire', 'property losses', 'buildings', 'municipal', 'public places', 'photographic archives', 'first responders']),
        ('future_climate_scenario', ['2050', '2090', '2071', '2041', '2011-2040', 'rcp', 'future fire weather', 'large ensemble', 'canleadv1']),
        ('forest_structure', ['scanfi', 'forest inventory', 'forest attributes', 'forest height', "lorey", 'elevation(ht)', 'crown closure', 'above-ground biomass', 'forest volume', 'needle-leaved', 'broad-leaved', 'spruces', 'pines (', 'birches', 'poplars', 'maples', 'cedars', 'hemlocks', 'true firs', 'douglas-firs', 'treed land', 'forest sections', 'satellite-based canada forest inventory']),
        ('fuel_or_vegetation', ['fuel type', 'fuel structure', 'hazardous forest', 'vegetation vigor', 'intensity and spread', 'ecoforest', 'land-use/land-cover', 'fao forest', 'crop inventory', 'managed forest', 'tree species', 'landcover', 'forest water', 'peatlands']),
        ('recovery_disturbance_or_carbon', ['recovery', 'disturbance', 'burned severity', 'burn severity', 'canlad', 'carbon', 'ghg emissions', 'regeneration', 'revegetation', 'seedling', 'whitebark', 'forest loss', 'restoration', 'wetlands and wildfires', 'bioengineering', 'landslide', 'active-layer', 'timber assets', 'bog dynamics', 'forest change']),
        ('weather_or_smoke', ['weather', 'danger rating', 'moisture index', 'season length', 'air quality', 'pollution', 'goes-', 'avhrr', 'palsar', 'airborne-sar', 'aviris', 'mercury', 'radioactivity', 'deposition', 'ecosystem exposure']),
        ('management_response_or_boundaries', ['response plan', 'management', 'restricted fire', 'restrictions', 'preventive measures', 'control zone', 'non-permit', 'suppression rates', 'protection area', 'aviation and emergency', 'fire district', 'fire regions', 'fire weather sector', 'utm (', 'tower', 'civic address', 'territorial boundaries', 'civil and fire safety', 'first nations', 'historical forestry', 'infrastructure', 'defence']),
        ('fire_labels_or_regime', ['fire history', 'fire ignition', 'ignition density', 'wildfire data', 'perimeter', 'fire disturbance', 'fire locations', 'forest wildfire', 'forest fires', 'forestry database', 'number of fires', 'area burned', 'area disturbed by fire', 'fire cycle', 'fire regime', 'fire severity', 'fire areas', 'fire hotspots', 'evacuation', 'disaster', 'grassland area burned', 'prescribed fire']),
    ]
    category = next((category for category, terms in rules if any(term in title for term in terms)), 'ancillary_review')
    overrides = {
        '01c1866d': 'fuel_or_vegetation', '02e85d01': 'exclude:keyword_collision',
        '04f5b200': 'exclude:keyword_collision', '093bcc9c': 'ecosystem_context',
        '10fe38cd': 'exclude:keyword_collision', '150beb08': 'ecosystem_context',
        '15eea1c7': 'ecosystem_context', '166b5b4c': 'exclude:keyword_collision',
        '1810fdca': 'fuel_or_vegetation', '1989de32': 'exclude:keyword_collision',
        '1a59dfdc': 'exclude:keyword_collision', '1fe01580': 'exclude:keyword_collision',
        '2b44eab2': 'exclude:keyword_collision', '32e942d5': 'exclude:keyword_collision',
        '3343aeab': 'management_response_or_boundaries', '3424abc1': 'exclude:keyword_collision',
        '36a3912f': 'exclude:keyword_collision', '3acc0a45': 'fire_labels_or_regime',
        '3b52c0eb': 'management_response_or_boundaries', '4c72a234': 'exclude:keyword_collision',
        '50c3bafa': 'terrain_context', '5258bfdb': 'management_response_or_boundaries',
        '53070989': 'ecosystem_context', '5686c613': 'exclude:keyword_collision',
        '56b92582': 'recovery_disturbance_or_carbon', '58557559': 'recovery_disturbance_or_carbon',
        '5eafb4ea': 'exclude:keyword_collision', '63ef1708': 'management_response_or_boundaries',
        '66c24181': 'exclude:narrative_or_administration', '6ad8e956': 'fire_labels_or_regime',
        '799f52a3': 'imagery_context', '7e24a14e': 'terrain_context',
        '84ee93a7': 'ecosystem_context', '86d1bafc': 'ecosystem_context',
        '88d70716': 'fuel_or_vegetation', '8fbd7b5e': 'exclude:keyword_collision',
        '9338bea3': 'imagery_context', '99c9c84a': 'weather_or_smoke',
        'a8194449': 'recovery_disturbance_or_carbon', 'ab0c22c6': 'terrain_context',
        'ac415f65': 'exclude:keyword_collision', 'b5531add': 'fire_labels_or_regime',
        'be7f3f25': 'exclude:keyword_collision', 'c32dfe71': 'recovery_disturbance_or_carbon',
        'cc11cd31': 'exclude:keyword_collision', 'd1be3c0e': 'fire_labels_or_regime',
        'd223ea14': 'terrain_context', 'd5a75b00': 'ecosystem_context',
        'da29fdf0': 'fuel_or_vegetation', 'e2dadc60': 'fire_labels_or_regime',
        'ed8aa69f': 'fire_labels_or_regime', 'f0e3bf4c': 'exclude:keyword_collision',
    }
    category = overrides.get(record['id'][:8], category)
    if category.startswith('exclude:'):
        decision = 'Excluded from wildfire predictor acquisition: keyword collision or non-feature document.'
    elif category == 'urban_response':
        decision = 'Urban/structural response is a separate outcome, not an Ontario wildland label.'
    elif category == 'future_climate_scenario':
        decision = 'Scenario/ensemble output is not observed historical weather; retain for future-scenario discussion.'
    elif category == 'recovery_disturbance_or_carbon':
        decision = 'Context or post-event outcome; require dated lag and outcome-leakage audit before predictor use.'
    else:
        decision = 'Candidate metadata screened; verify footprint, dated coverage, units and raw access before joining.'
    if not ontario:
        decision += ' Ontario coverage is not established by this screening.'
    return category, decision


def publish(cache, output, manifest):
    pages = json.loads(manifest.read_text())
    page_by_id = {identifier: p['page'] for p in pages['pages'] for identifier in p['ids']}
    if len(page_by_id) != pages['unique_ids'] or sum(len(p['ids']) for p in pages['pages']) != len(page_by_id):
        raise ValueError('Page manifest has duplicate or missing IDs')
    paths = sorted(p for p in (cache / 'packages').glob('*.json') if '.receipt.' not in p.name)
    expected = set(page_by_id) | set(OWNER_IDS)
    if {p.stem for p in paths} != expected:
        raise ValueError('Cache membership does not match screened IDs and owner-linked sources')
    packages = []
    for path in paths:
        record, receipt = read_package(path)
        category, decision = screen(record)
        resources = [{'name': english(r, 'name'), 'format': r.get('format'), 'url': r['url']}
                     for r in record['resources'] if 'safelinks.protection.outlook.com' not in r['url']]
        packages.append({'id': record['id'], 'page': page_by_id.get(record['id']),
                         'owner_linked_extra': record['id'] not in page_by_id,
                         'title': english(record, 'title'),
                         'publisher': record.get('organization', {}).get('title'),
                         'catalogue': 'https://open.canada.ca/data/en/dataset/' + record['id'],
                         'modified': record.get('metadata_modified'),
                         'period_start': record.get('time_period_coverage_start'),
                         'period_end': record.get('time_period_coverage_end'),
                         'license': record.get('license_title'), 'spatial': record.get('spatial'),
                         'category': category, 'decision': decision,
                         'metadata_sha256': receipt['sha256'], 'resources': resources})
    counts = Counter(p['category'] for p in packages if p['page'])
    output.mkdir(parents=True, exist_ok=True)
    (output / 'fire_catalogue_inventory.json').write_text(json.dumps({'method': 'All search-result summaries inspected; transparent title-based triage plus selected detailed source review. Candidate does not mean verified usable data.', 'categories': dict(counts), 'records': packages}, indent=2) + '\n')
    by_id = {p['id']: p for p in packages}
    lines = ['# Fire catalogue: page-by-page screening', '',
             'Generated from the observed 46-page receipt and official CKAN metadata. All 455 search records are listed once; three extra owner-linked products appear only in the JSON inventory. Titles drive reproducible triage; detailed compatibility decisions are in [the source report](../FIRE_FEATURE_SPACE.md). No source is admitted into a model by this list.', '']
    for page in pages['pages']:
        lines += [f"## Page {page['page']}", '', f"[Observed search page]({page['url']}) · {len(page['ids'])} records", '', '| Record | Screening |', '| --- | --- |']
        for identifier in page['ids']:
            r = by_id[identifier]
            title = r['title'].replace('|', ' / ').replace('\n', ' ')
            lines.append(f"| [{title}]({r['catalogue']}) | `{r['category']}` — {r['decision']} |")
        lines.append('')
    (output / 'FIRE_CATALOGUE_PAGES.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'pages': pages['page_count'], 'inventory': len(packages), 'categories': dict(counts)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/catalogue/20261006'))
    parser.add_argument('--manifest', type=Path, default=ROOT / 'docs/data/fire_catalogue_pages.json')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/catalogue/rebuilt-inventory')
    args = parser.parse_args()
    publish(args.cache, args.output, args.manifest)
