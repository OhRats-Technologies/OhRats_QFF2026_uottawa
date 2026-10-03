# Independent matched-study audit

The corrected random-encoder baseline solves the full-label classification task. These experiments do not demonstrate a downstream quantum benefit.

## Random encoder, trained classifier

The original `Untrained` branch passes `epochs=0` to every supervised probe. This tests a random classifier as well as a random encoder. The audit changes only classifier training to the same 40 epochs used for trained encoders, verifies that every encoder parameter remains unchanged, and preserves the original study files.

| Label fraction | Corrected accuracy, mean of 10 seeds |
| --- | ---: |
| 1% | 51.66% |
| 5% | 78.98% |
| 10% | 92.29% |
| 100% | 99.85% |
| 5-NN, all training labels | 100% |

Full-label accuracy is saturated and cannot support a representation-learning advantage. Low-label results remain exploratory: 1% supplies only eight training examples for ten classes, and equal subset RNG seeds do not by themselves establish equal sample identities when loader order differs. A future comparison should fix sample IDs, classifier initialization and label coverage across methods.

## Paired distribution metrics

Positive differences mean the quantum variant has higher held-out RBF-MMD squared, hence worse agreement with the Gaussian reference. Recomputed from the original ten paired seeds, with a deterministic 10,000-resample bootstrap and sample standard errors.

| Comparison | Mean difference | Bootstrap 95% interval | Quantum wins | Raw Wilcoxon p | Holm p, three comparisons |
| --- | ---: | --- | ---: | ---: | ---: |
| Q + moments vs RBF + moments | 0.001020 | [-0.002893, 0.004970] | 5/10 | 0.556641 | 0.556641 |
| Pure Q vs pure RBF | 0.008580 | [0.000833, 0.015668] | 2/10 | 0.048828 | 0.097656 |
| Q + moments vs SIGReg | 0.011185 | [0.008682, 0.013841] | 0/10 | 0.001953 | 0.005859 |

The first comparison provides no evidence of a difference; it does not establish equivalence. The pure-kernel result is suggestive but fails the three-comparison Holm threshold. The bootstrap intervals are pointwise, not simultaneous. All analyses are exploratory rather than pre-registered.

SIGReg uses the full batch of 64 at every training step; the other regularizers use batches of eight every fourth step. The direct Q/RBF comparisons share those schedules, but the assertion that all seven variants are schedule-matched is incorrect. SIGReg is better in these runs, without isolating kernel choice from batch size and frequency.

Gradient cosine summaries condition on positive MMD and moment losses. Negative unbiased MMD estimates are legitimate, so this filter can bias the diagnostic; zero placeholders for unmeasured variants do not indicate orthogonal gradients.

## Reproduction and limits

Run `uv run python -m scripts.q_sigreg_matched_audit`. `results.json` contains every corrected seed, frozen-state checks and recomputed statistics. `manifest.json` records hashes of the original results, audit results and source dependencies (the original-result hash is in `results.json`). Original evidence is unchanged.

All 86 repository tests passed in 9.13 seconds when discovery ran after `torch.set_num_threads(1)`. The three new audit tests passed independently, and `uv run python -m flybrain run` passed. Default mixed PyTorch/Aer discovery previously segfaulted; the single-thread run is a verified workaround, not a diagnosis or fix of that failure.

No quantum hardware was used. This is an audit of simulator experiments, not a new breakthrough. Noah and the study author have been asked on the board to independently verify the probe diagnosis and reconsider the task. A promising next test is exact mean-density MMD with a cached Gaussian target: it may reduce estimator noise, but cannot remove the fixed kernel's finite-feature identifiability limit or establish quantum advantage by itself.
