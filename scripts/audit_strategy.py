"""Audit public strategy/context deliverables; no downloads, fitting or simulation."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from context.ordering_public import verify_order

ROOT = Path(__file__).resolve().parents[1]
PRIORITY = {
    '7cbdfae1-f724-4679-8f0f-1c611f17186f', 'a6b81e8b-d429-4629-9121-5a56786fcb83',
    '836082d5-d55f-46c3-9b9c-aaf1a306c247', '0bce352f-6f3f-4a30-9763-c80805fcf272',
    '347a2de5-1006-4c1f-ba09-b66947654d0a', '1728e7f9-472a-474e-9e04-f96bf59479f9',
    'adfa340a-1781-48b1-ab17-2e1ca1b915df',
}


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def source_pins(record):
    pins = record.get('source_sha256', record.get('source_hashes', {}))
    return {path: sha(path) == expected for path, expected in pins.items()}


def audit(catalogue_proof=None, context_proof=None):
    requirements, artifacts = [], {}

    def add(identifier, evidence, facts, scope, status='verified_public_snapshot'):
        for path in evidence:
            artifacts[path] = sha(path)
        requirements.append(dict(id=identifier, status=status, evidence=evidence, facts=facts, scope=scope))

    pages = read('docs/data/fire_catalogue_pages.json')
    inventory = read('docs/data/fire_catalogue_inventory.json')
    ids = [identifier for page in pages['pages'] for identifier in page['ids']]
    assert [p['page'] for p in pages['pages']] == list(range(1, 47))
    assert len(ids) == len(set(ids)) == 455
    assert all(len(p['ids']) == 10 for p in pages['pages'][:-1]) and len(pages['pages'][-1]['ids']) == 5
    records = {row['id']: row for row in inventory['records']}
    assert len(records) == 458 and set(ids) == {r['id'] for r in records.values() if r['page']}
    assert PRIORITY <= set(records) and sum(inventory['categories'].values()) == 455
    add('complete_catalogue_and_priority_sources', ['docs/FIRE_FEATURE_SPACE.md',
        'docs/data/FIRE_CATALOGUE_PAGES.md', 'docs/data/fire_catalogue_pages.json',
        'docs/data/fire_catalogue_inventory.json'], dict(pages=46, search_ids=455, metadata_records=458,
        priority_ids=sorted(PRIORITY), observed_utc=pages['observed_utc']),
        'Preserved search membership and metadata/report coverage; not a new live search or raster validation.')

    layers = read('web/demo/assets/context/layers.json')
    series = read('web/demo/assets/context/height-series-v2.json')
    context = read('docs/data/scanfi_height_context.json')
    assert layers['crs'] == 'EPSG:3978' and len(layers['layers']) == 5
    assert [r['year'] for r in series['records']] == list(range(1985, 2020, 5))
    assert series['renderer_sha256'] == sha('scripts/context/render_height.py')
    for row in layers['layers']:
        path = 'web/demo/assets/context/' + Path(row['image']).name
        assert sha(path) == row['output_sha256'] and row['numeric_predictor'] is False
        artifacts[path] = sha(path)
    for row in series['records']:
        path = 'web/demo/assets/context/' + Path(row['image']).name
        assert sha(path) == row['image_sha256']
        artifacts[path] = sha(path)
    assert context['nodata'] == 255 and context['effective_resolution_m'] == 480
    assert all(c['inside_mask'] and c['roundtrip_error_degrees'] < 1e-12 for c in context['controls'])
    add('bounded_context_schema_and_geography', ['docs/FOREST_CONTEXT.md', 'docs/DATA_SCHEMA.md',
        'scripts/context/pipeline.py', 'scripts/context/manifest.py', 'web/demo/assets/context/layers.json',
        'web/demo/assets/context/height-series-v2.json', 'docs/data/scanfi_height_context.json'],
        dict(styled_wms_layers=5, numeric_epochs=7, sample_resolution_m=480,
             display_crs=layers['crs'], city_controls=context['controls']),
        'Current public display hashes/producer, source-reported grid semantics and city controls. '
        'WMS images are not numerical predictors; native custom LCC differs from display EPSG:3978.')

    change = read('docs/data/height_spatial_change.json')
    assert change['plan_sha256'] == sha('experiments/height_spatial_change.json')
    assert change['code_sha256'] == sha('scripts/context/change.py')
    assert change['source_array_hashes'] == {str(r['year']): r['source_sha256'] for r in series['records']}
    assert change['map']['renderer_sha256'] == sha('scripts/context/render_change.py')
    for key in ['image', 'legend']:
        path = 'web/demo/assets/context/' + Path(change['map'][key]).name
        assert sha(path) == change['map'][key + '_sha256']
        artifacts[path] = sha(path)
    assert abs(change['mean_positive_contribution_m'] - change['mean_negative_contribution_m'] -
               change['mean_signed_m']) < 1e-12
    add('spatial_context_interpretation', ['docs/data/height_spatial_change.json',
        'docs/data/height_spatial_verification.json'], dict(common_samples=change['common_samples'],
        mean_signed_m=change['mean_signed_m'], mean_absolute_m=change['mean_absolute_m']),
        'Pinned descriptive difference and arithmetic; not physical growth, causal disturbance or forecast accuracy.')

    pilot = read('docs/results/coarse-height-context.json')
    plan = read('experiments/coarse_height_context.json')
    checked = read('docs/data/coarse_height_verification.json')
    assert checked['result_sha256'] == sha('docs/results/coarse-height-context.json')
    assert pilot['plan_sha256'] == sha('experiments/coarse_height_context.json')
    assert pilot['model_fits'] == 36 and pilot['pair_circuits'] == 4204 and pilot['hardware_jobs'] == 0
    assert plan['years'] == [1988, 2018] and all(max(row['years']) <= 2018 for row in pilot['results'])
    for path, expected in plan['data_hashes'].items():
        assert sha(path) == expected
    averages = {f'{model}/{condition}': mean(r['mae_ha'] for r in pilot['results']
        if r['model'] == model and r['condition'] == condition)
        for model in ['ridge', 'rbf', 'qsvr'] for condition in plan['conditions']}
    add('context_performance_and_architecture', ['experiments/coarse_height_context.json',
        'docs/results/coarse-height-context.json', 'docs/data/coarse_height_verification.json',
        'experiments/constant_ancilla_control.json', 'docs/data/constant_ancilla_verification.json'],
        dict(original_fits=36, original_pair_circuits=4204, development_mean_mae_ha=averages),
        'Saved fixed training-only pilot: no consistent height gain; known constant-ancilla identity/control, '
        'not a breakthrough, independent confirmation or replacement for frozen final models.')

    verify_order(read, sha, add)

    pruning = read('docs/data/game_pruning_verification.json')
    assert all(source_pins({'source_hashes': {p: h for p, h in pruning['source_hashes'].items()
        if Path(p).name in ['rules.js', 'scenario.js', 'upgrades.js', 'session.js']}}).values())
    tracked = subprocess.check_output(['git', 'ls-files', 'web/demo'], cwd=ROOT, text=True).splitlines()
    retired = [p for p in tracked if '/game/' in p or 'runner' in p.lower() or 'signal' in p.lower()]
    assert not retired
    balance = read('docs/data/game_balance_v2.json')
    assert all(sha(path) == expected for path, expected in balance['rules_sha256'].items())
    add('strategy_challenge_progression_and_pruning', ['docs/WILDFIRE_GAME.md',
        'web/demo/strategy/rules.js', 'web/demo/strategy/upgrades.js', 'web/demo/strategy/session.js',
        'docs/data/game_balance_v2.json', 'docs/data/game_pruning_verification.json'],
        dict(balance_seeds=balance['seeds'], policies=balance['policies'], retired_runtime_paths=retired),
        'Implemented/reviewed constrained crews, supplies, delays, seeded permanent choices, win/loss and replay. '
        'Fixed policy balance does not establish human enjoyment or operational effectiveness.')

    diagnostic = read('docs/data/instrument_diagnostic.json')
    assert diagnostic['status'] == 'passed' and diagnostic['paths'] == 256
    assert diagnostic['maximum_coordinate_error'] < 1e-12 and all(source_pins(diagnostic).values())
    add('quantum_lens_sqd_and_accepted_steers', ['web/demo/README.md', 'web/demo/strategy/quantum.js',
        'web/demo/strategy/bench.js', 'web/demo/strategy/instruments.js', 'docs/data/instrument_diagnostic.json',
        'docs/data/bench_inspection_verification.json', 'docs/data/instrument_effect_verification.json'],
        dict(saved_qiskit_paths=256, maximum_coordinate_error=diagnostic['maximum_coordinate_error']),
        'Working illustrative sphere/noise/echo/twirling/readout/PSD controls and sampled diagonal objective; '
        'browser sampling equals classical minimum, with no game-response or predictive benefit.')

    for name in ['touch_input', 'short_viewport', 'upgrade_choice', 'game_keyboard', 'season_feedback',
                 'marker_picker', 'forest_audio', 'render_fallback']:
        path = 'docs/data/' + name + '_verification.json'
        receipt = read(path)
        pins = source_pins(receipt)
        add(name, [path], dict(current_source_pins=pins), receipt.get('scope',
            'Receipt-specific authoring checks; see saved cases and limits.'),
            'current_pinned_scope' if pins and all(pins.values()) else 'historical_pinned_scope')

    current_path = 'docs/data/current_interaction_verification.json'
    current = read(current_path)
    assert current['status'] == 'passed' and current['authoring_runs'] == len(current['checks']) >= 10
    assert all(source_pins(current).values())
    add('current_interaction_and_visual_review', [current_path],
        dict(authoring_runs=current['authoring_runs'], enumerated_cases=sum(len(c['cases']) for c in current['checks']),
             inspected_screenshots=len(current['visual_review'])), current['scope'], 'current_pinned_scope')

    accessibility = read('docs/data/accessibility_context_verification.json')
    assert accessibility['status'] == 'passed' and all(source_pins(accessibility).values())
    assert len(accessibility['cases']) == 3 and not accessibility['errors']
    add('accessible_dialog_and_fire_context', ['docs/data/accessibility_context_verification.json'],
        dict(viewports=3, baseline=accessibility['before']), accessibility['scope'], 'current_pinned_scope')

    seeds = read('docs/data/new_season_verification.json')
    assert seeds['status'] == 'passed' and all(source_pins(seeds).values())
    assert len(seeds['seed_sequence']) == 32 and len(seeds['first_upgrade_offer_counts']) == 4
    assert all(seeds['old_game_recipe_hashes_preserved'].values())
    add('new_season_variety_and_replay', ['docs/data/new_season_verification.json'],
        dict(seasons=32, observed_offer_sets=4), seeds['scope'], 'current_pinned_scope')
    trades = read('docs/data/upgrade_tradeoff_review.json')
    assert trades['status'] == 'passed' and all(source_pins(trades).values())
    assert trades['plan_sha256'] == sha('experiments/game_upgrade_tradeoffs.json')
    assert trades['game_branches'] == 384 and trades['saved_arithmetic_check']['paired_rows'] == 12
    add('upgrade_tradeoffs', ['experiments/game_upgrade_tradeoffs.json',
        'docs/data/upgrade_tradeoff_review.json'], dict(game_branches=384, paired_rows=12),
        trades['scope'] + ' ' + trades['offer_coverage_limitation'])

    viewer = read('docs/data/current_view_portability.json')
    assert viewer['status'] == 'passed' and not viewer['errors'] and not viewer['failedLocal']
    assert len(viewer['slides']) == 9 and len(viewer['sections']) == 5 and len(viewer['contextLayers']) == 8
    changed = subprocess.check_output(['git', 'diff', '--name-only', viewer['commit'], 'HEAD', '--',
        'web/demo', 'web/presentation'], cwd=ROOT, text=True).splitlines()
    runtime_changes = [p for p in changed if Path(p).suffix in
        ['.js', '.ts', '.html', '.css', '.json', '.png', '.svg', '.woff2', '.pdf', '.pptx']]
    runtime_unchanged = not runtime_changes
    assert runtime_unchanged
    for row in viewer['downloads']:
        path = 'web/presentation/slides/' + row['name']
        assert sha(path) == row['sha256']
        artifacts[path] = sha(path)
    slides = re.findall(r"id:'([^']+)',title:'[^']+',seconds:(\d+)", (ROOT / 'web/presentation/slides.js').read_text())
    assert len(slides) == 9 and sum(int(seconds) for _, seconds in slides) == 300
    talk = (ROOT / 'web/presentation/talk.md').read_text().split('## 1.', 1)[1].split('\n', 1)[1]
    spoken = ' '.join(line for line in talk.splitlines() if line.strip() and not line.startswith('#')
        and not (line.startswith('*') and line.endswith('*')))
    add('presentation_and_clean_viewing', ['web/presentation/slides.js', 'web/presentation/talk.md',
        'docs/data/current_view_portability.json', 'docs/data/presentation_note_review.json'],
        dict(main_seconds=300, main_slides=7, appendix_slides=2, runtime_unchanged_since_view=runtime_unchanged,
             spoken_words_whitespace=len(spoken.split()), changed_runtime_assets=runtime_changes),
        'Existing nine-slide exports retained and current served runtime assets match the clean-view receipt; '
        'Markdown/authoring-check changes are outside that runtime comparison. '
        'Planned duration is not measured rehearsal; native PowerPoint and broad platforms remain untested.')

    parents = read('docs/data/annual_goal_handoff.json')['artifact_sha256']
    annual_paths = ['experiments/annual_final.json', 'docs/results/annual-final-training.json',
        'docs/results/annual-final.json', 'docs/data/annual_final_bundle.json',
        'docs/data/annual_training.csv', 'docs/data/annual_reused_evaluation.csv']
    annual = {path: parents[path] for path in annual_paths}
    assert all(sha(path) == expected for path, expected in annual.items())
    training = read('docs/results/annual-final-training.json')
    assert training['plan_sha256'] == sha('experiments/annual_final.json')
    execution_code = {path: sha(path) == expected for path, expected in training['code_sha256'].items()
                      if path not in ['uv.lock', 'pyproject.toml']}
    project_manifests = {path: sha(path) == training['code_sha256'][path]
                         for path in ['uv.lock', 'pyproject.toml']}
    assert all(execution_code.values())
    legacy = read('docs/data/annual_requirement_audit.json')['protected_scientific_sha256']
    available = {path: (ROOT / path).exists() for path in legacy}
    assert all(sha(path) == expected for path, expected in legacy.items() if available[path])
    add('frozen_science_preserved', annual_paths + ['docs/data/annual_goal_handoff.json',
        'docs/data/annual_requirement_audit.json'], dict(protected_annual_public_hashes=annual,
        annual_execution_code_hashes_match=execution_code,
        project_manifests_match_frozen_execution=project_manifests, legacy_parent_availability=available),
        'Annual public plan, execution record, result, bundle and datasets match their annual handoff. '
        'Legacy incident/policy parents are checked only when present; missing ignored files do not '
        'certify private state. Current project dependency manifests differ from frozen execution; '
        'this does not certify its environment or refit predictors. No hardware accounts are inspected or jobs authorized.')

    code_paths = subprocess.check_output(['git', 'ls-files', 'scripts/context', 'scripts/catalogue',
        'web/demo/strategy'], cwd=ROOT, text=True).splitlines() + ['scripts/audit_strategy.py']
    loc = {p: len((ROOT / p).read_text().splitlines()) for p in code_paths
           if Path(p).suffix in ['.py', '.js', '.mjs', '.css']}
    assert max(loc.values()) <= 300
    add('modularity_and_tooling', ['scripts/audit_strategy.py', 'web/demo/package.json',
        'web/demo/bun.lock', 'pyproject.toml', 'uv.lock', 'AGENTS.md'],
        dict(handwritten_files_checked=len(loc), maximum_loc=max(loc.values())),
        'New context/catalogue/strategy concern modules meet the 300-line preference. '
        'Generated bundles and historical unrelated modules are outside this count; Bun/uv configuration is explicit.')

    board_bytes = (ROOT / 'AGENT_BOARD.jsonl').read_bytes()
    remote_board = subprocess.check_output(['git', 'show', 'origin/main:AGENT_BOARD.jsonl'], cwd=ROOT)
    assert board_bytes == remote_board
    seen = set()
    for line in board_bytes.splitlines():
        row = json.loads(line)
        assert row['id'] not in seen and (row['ref'] is None or row['ref'] in seen)
        seen.add(row['id'])
    assert 'Accept safe, relevant implementation steers' in (ROOT / 'AGENTS.md').read_text()
    add('coordination_and_peer_steering', ['AGENTS.md', 'AGENT_BOARD.md'],
        dict(board_records=len(seen), local_board_matches_fetched_tracking_branch=True),
        'Current local board order/uniqueness/backrefs and steering policy; caller fetches first. '
        'This does not infer peer agreement or authorize unrelated spending.')

    for key, path in [('catalogue', catalogue_proof), ('context', context_proof)]:
        if path is not None:
            proof = read(path)
            if key == 'catalogue':
                assert proof['status'] == 'passed' and proof['pages'] == 46 and proof['search_ids'] == 455
                assert proof['metadata_responses'] == 458 and proof['original_cache_preserved']
                for name, expected in proof['byte_identical_rebuild'].items():
                    assert sha('docs/data/' + name) == expected
            else:
                assert proof['status'] == 'identical_context' and proof['optional_derived_context_hashes_checked']
            add(key + '_local_source_check', [str(path)], dict(checked_utc=proof['checked_utc']),
                proof['scope'], 'verified_local_source_scope')
    return dict(checked_utc=datetime.now(timezone.utc).isoformat(), status='artifact_review',
        git_head_at_check=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        requirements=requirements, artifact_sha256=artifacts, goal_complete=False, audit_revision=2,
        correction='0743287 mislabeled the legacy incident/policy freeze as annual parents and required ignored files. Annual checks now use annual execution/handoff hashes; private legacy parents are optional.',
        completion_not_checked=['Manual full-objective review beyond these artifact contracts',
            'Final report and successful Git/board publication',
            'Goal-tool completion after required work is achieved'],
        limits=['Physical devices, human enjoyment, listening quality and actual rehearsal are unmeasured',
            'Native PowerPoint/public repository access/submission are separate checks or team actions',
            'Historical input receipts are explicitly distinguished from current pinned scopes'],
        new_downloads=0, new_predictor_fits=0, new_quantum_states=0, hardware_jobs=0,
        scope='Public artifact/static contracts plus optional completed offline source-check receipts; '
              'not an end-to-end rerun of every historical experiment or UI case.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.cache/strategy-review/receipt.json'))
    parser.add_argument('--catalogue-proof', type=Path)
    parser.add_argument('--context-proof', type=Path)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / '.cache'):
        parser.error('Write audit output under ignored .cache/')
    result = audit(args.catalogue_proof, args.context_proof)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], requirements=len(result['requirements']),
        goal_complete=False, new_fits=0, hardware_jobs=0)))


if __name__ == '__main__':
    main()
