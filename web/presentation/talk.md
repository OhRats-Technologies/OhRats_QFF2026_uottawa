# Five-minute narration

Use this as the spoken outline. The browser's **N** notes contain methods and source links for questions. Keep the two appendices outside the main talk. Timings include the short visual demonstrations below, not just reading time.

## 1. Annual wildfire question · 30 seconds

Can a quantum kernel help estimate Ontario's annual average reported fire size? We compare quantum and classical kernels on a climate problem under matched budgets.

This map shows real 2021 land-cover pixels and recorded locations. That year's average was 657 hectares per fire. Our target is the yearly average, rather than total burned area. The study uses same-year climate, so it is retrospective.

## 2. Dataset construction · 55 seconds

We built one row per Ontario year. NRCan's historical fire records supply reported areas. We exclude ambiguous identities and prescribed fires, then divide observed area by accepted fire count. In 2021, 784,447 hectares divided by 1,194 fires gives that 657-hectare average.

ECCC monthly station measurements supply temperature and precipitation. Coverage checks precede annual and seasonal aggregation, then we join by year.

*Click Annual row to show the actual four climate inputs.*

We have 31 training years, 1988 through 2018, and six later years. Those later years were previously inspected, so we disclose them as reused evaluation. Forest cover provides context and separate ablations; the main predictors use climate.

## 3. Feature selection and SQD · 45 seconds

We also tested choosing four of ten climate features. There are only 210 possible subsets, so exact classical enumeration is a strong reference.

QAOA samples candidate bitstrings. Sample-based quantum diagonalization projects our diagonal feature-selection objective into those sampled candidates and recovers the lowest cost. Because this objective is diagonal, the result equals taking the best sampled candidate classically.

The displayed errors use the same fixed ridge predictor, separate from the kernel comparison. Exact enumeration performs best, followed by uniform sampling and then QAOA. This demonstrates SQD, with no speedup or predictive advantage.

## 4. Matched prediction · 45 seconds

Both prediction methods receive the same four climate inputs and equal tuning budgets. Preprocessing uses only the training window in each chronological fold.

The classical kernel compares feature distances. Qiskit's FidelityQuantumKernel compares encoded quantum states through squared overlap. Both similarity matrices feed a classical support-vector regression solver. We do not learn variational circuit parameters.

RBF leads development: about 77 hectares per fire in mean absolute error, compared with 87 for QSVR.

## 5. Later-year extremes · 55 seconds

Each group here is a separate Ontario year. Orange shows recorded average hectares per fire. Grey is the constant training-year mean. The other bars show QSVR and RBF estimates.

The high years remain badly underestimated. In 2021, the average reaches 657 hectares per fire. In 2020, it is only 26. The estimates miss this variation.

Across these six reused years, none of eleven main models beats the training mean. QSVR beats matched RBF, but both lose to the constant. That pairwise result cannot establish useful predictive skill or quantum advantage.

## 6. Encoding geometry · 40 seconds

At the broader angle setting, the ten-qubit matrix is nearly the identity. Different years have very little overlap.

*Switch from π/4 to π/32 and pause for the matrix transition.*

Narrower encoding changes the measured effective rank from about 31 to 5.2 and raises similarity. But narrow kernels can also become poorly conditioned. This training-input diagnostic fits no predictor and leaves the final model unchanged. The phase circles illustrate encoding; they are not full entangled states.

## 7. Findings and limits · 30 seconds

We built an audited annual dataset, tested actual Qiskit kernels and SQD, and measured a concrete encoding failure regime. The classical kernel leads development. Later extremes defeat every main model, including the quantum one.

The next scientific step needs a prospective target and new evaluation evidence. Fireline is an optional strategy demo. Its simulated outcomes remain separate from these results.
