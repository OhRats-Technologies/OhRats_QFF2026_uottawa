"""Descriptive sensitivity of saved predictions; no fitting or model promotion."""
import numpy as np


def error_summary(years, actual, predicted):
    error = np.abs(np.asarray(predicted)-actual)
    total = float(error.sum())
    omitted = (total-error)/(len(error)-1)
    worst = int(error.argmax())
    return dict(years=years, actual_ha=list(actual), predicted_ha=list(predicted),
                absolute_errors=error.tolist(), mae_ha=float(error.mean()),
                omitted_year_mae=omitted.tolist(),
                omitted_year_range=[float(omitted.min()), float(omitted.max())],
                largest_error_year=years[worst],
                largest_error_share=float(error[worst]/total) if total else 0.)


def prediction_panels(evidence):
    panels = {}
    for cohort in evidence['cohorts']:
        panels.setdefault(cohort['panel'], []).append(cohort)
    rows = []
    for panel, cohorts in panels.items():
        cohorts.sort(key=lambda c: c['fold'][2])
        years = [year for c in cohorts for year in range(c['fold'][2], c['fold'][3]+1)]
        actual = np.concatenate([c['results']['qsvr']['actual_ha'] for c in cohorts])
        models = {}
        for kind in ['ridge', 'rbf', 'qsvr', 'fixed_qsvr']:
            predicted = np.concatenate([c['results'][kind]['predicted_ha'] for c in cohorts])
            models[kind] = error_summary(years, actual, predicted)
        q, r = np.asarray(models['qsvr']['absolute_errors']), np.asarray(models['rbf']['absolute_errors'])
        difference = q-r
        omit_year = (difference.sum()-difference)/(len(years)-1)
        fold_differences = difference.reshape(len(cohorts), -1).mean(axis=1)
        omit_fold = (fold_differences.sum()-fold_differences)/(len(cohorts)-1)
        rows.append(dict(panel=panel, models=models,
            paired_q_minus_rbf=dict(mean_ha=float(difference.mean()),
                year_differences=difference.tolist(), q_winning_years=int((difference < 0).sum()),
                fold_differences=fold_differences.tolist(),
                omitted_year_range=[float(omit_year.min()), float(omit_year.max())],
                omitted_fold_range=[float(omit_fold.min()), float(omit_fold.max())])))
    return rows


def tuning_sensitivity(evidence):
    """Delete validation weights from cached predictions, not observations from fits."""
    rows = []
    for cohort in evidence['cohorts']:
        tuning = cohort['tuning']
        years = [year for split in tuning['inner_splits'] for year in split['validation_years']]
        actual = np.concatenate([split['actual_ha'] for split in tuning['inner_splits']])
        assert len(years) == len(set(years))
        for kind in ['ridge', 'rbf', 'qsvr']:
            candidates = [r for r in tuning['candidates'] if r['specification']['model'] == kind]
            errors = np.abs(np.asarray([r['predicted_ha'] for r in candidates])-actual)
            scores = errors.mean(axis=1)
            chosen = int(scores.argmin())
            assert candidates[chosen]['specification'] == tuning['chosen'][kind]
            altered = (errors.sum(axis=1)[:, None]-errors)/(len(years)-1)
            winners = altered.argmin(axis=0)
            ordered = np.sort(scores)
            rows.append(dict(panel=cohort['panel'], fold=cohort['fold'], model=kind,
                inner_years=years, candidate_count=len(candidates), chosen_index=chosen,
                chosen_specification=candidates[chosen]['specification'],
                chosen_inner_mae=float(scores[chosen]), second_score_margin=float(ordered[1]-ordered[0]),
                deletion_winner_indices=winners.tolist(),
                changed_deletions=int((winners != chosen).sum()),
                distinct_deletion_choices=int(len(np.unique(winners))),
                deletion_winner_specifications=[candidates[i]['specification'] for i in winners]))
    return rows
