# Judge guide

**Question:** can quantum kernels improve retrospective annual Ontario wildfire-size estimation under a matched budget?

**Answer:** RBF leads chronological development; none of eleven main models beats the training mean on six reused years. The useful quantum finding is a measured encoding-scale/conditioning tradeoff, not predictive advantage.

## Read in this order

1. [README](../README.md): task, quantum contribution, data, results, costs and replay.
2. [Slides and browser presentation](../web/presentation/README.md): main talk and question appendix. The optional [QSVR demo](../web/demo/README.md) contains a short arcade and a separate evidence walkthrough explaining data, SQD, phases, saved kernels and predictions. Gameplay rewards are illustrative, not experimental results.
3. [Report](REPORT.md): controlled comparisons, source assumptions, selection and negative results.
4. [Frozen final evidence](ANNUAL_FINAL.md): every annual error, spectra, recipes and public replay package.

The main story is annual estimation. [Earlier incident work](FINAL_EVALUATION.md), policy evolution and shot/tangent studies are supplemental; they do not supply independent annual evidence. Dataset construction and classical/QAOA/SQD selection are in the main talk. SQD is a diagonal-objective demonstration with no added optimization benefit. See the [independent raw-source audit](DATA_REVIEW.md) for annual totals, denominators and the large-fire explanation.

## What is measured

31 annual training observations (1988–2018), six reused evaluation years (2019–2024); same-year climate, local analytic simulation. QSVR's support-vector optimizer is classical. No predictive accuracy claim follows from the later target-free bandwidth diagnostic. No hardware or quantum advantage is claimed.

## Submission checklist

[Official open challenge](https://github.com/uoquantum/QiskitFF26/blob/main/prompts/hackathon/open_challenge/PROMPT.md) · [shared guidelines](https://github.com/uoquantum/QiskitFF26/blob/main/prompts/hackathon/SUBMISSION_GUIDELINES.md).

Submit **October 7, 2026, 11:59 PM ET**; present live **October 10**. Slides, public repository, self-contained README and supporting results are required. The organizer announcement supplies the submission destination and live duration; the five-minute deck is a planning choice. No video or hardware is required. The team must still submit; repository preparation is not submission.

[Submission audit](SUBMISSION_AUDIT.md) records implemented deliverables and the scope of verification.
