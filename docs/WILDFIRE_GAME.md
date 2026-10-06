# Ontario wildfire strategy demo

The owner rejected Signal Run's reflex-runner mechanics. Replace it with a short, turn-based **season of decisions** on the full Ontario raster. The preserved annual QSVR/SQD evidence stays in the [lab walkthrough](../web/demo/lab.html); gameplay is an educational simulation, not a validated forecast or firefighting tool.

## Core loop

Select a fire on the map. Examine uncertain fuel, current weather, intensity and threatened landscape. Allocate a crew, spend supplies on a water drop, investigate, or retain resources. Advance one turn and watch growth, suppression, new ignitions and returning crews. Each season lasts twelve turns; two milestone upgrades change the next decisions. There is no reaction-time requirement or feature-selection puzzle.

The design must make scarcity consequential: a crew is unavailable while deployed; water is immediate but consumes supplies; investigation narrows uncertainty without extinguishing a fire; reserves protect against the next front. Loss follows excessive accumulated landscape damage. A clear debrief explains the player's decisions and supports retrying the same seed or exploring another season. This is a roguelike run, not a grind or leaderboard.

## Interface

- The map dominates the left side, with full Ontario including southern cities; historical source positions seed fictional incidents. Rings, embers and short weather transitions make consequences visible. Clickable points also have keyboard-accessible list controls.
- The right side holds a restrained incident brief and an illustrative quantum sphere. It shows how input changes rotate a state, not a “quantum firefighting shield.”
- A sampled-subspace matrix illustrates feature relevance/redundancy, feasible subsets and a diagonal minimum. Sampling fewer candidates can miss a better subset. For a diagonal objective, selecting the lowest sampled cost is also a classical minimum; no advantage is claimed.
- Bottom resources and branching upgrades are compact, with exact costs/effects. A field guide holds provenance, equations and source limitations so the play surface stays readable.

## Model and evidence boundaries

The detailed game equations, calibrated scenario checks and validation receipt will accompany the implementation. Intensity, landscape integrity, supplies and progression are game units. Simulated weather and growth are never labelled as observed data. Historical source maps are dated; styled WMS imagery is never decoded as a numerical measurement. Quebec layers inform concepts only, unless the game explicitly switches geography in a future scope decision.

New layers are candidates for future training-only research, not new final-model inputs. The [feature-space report](FIRE_FEATURE_SPACE.md) explains why static provincial averages cannot supply yearly variation and why post-disturbance recovery requires a leakage audit. There are no new quantum hardware calls.

## Acceptance checks

Play multiple seeds with conserving, intervention and careless strategies. Verify resource conservation, crew delays, deterministic replay and a meaningful win/loss range. Confirm that decisions affect outcomes and that one free action does not dominate every strategy. Check actual map clicks, keyboard controls, touch, narrow layouts, reduced motion and sound opt-in. Preserve all frozen scientific hashes. Delete superseded runner modules/tests after the new playable mode works, rather than retaining two competing games.
