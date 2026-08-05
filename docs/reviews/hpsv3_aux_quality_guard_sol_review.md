# HPSv3 Auxiliary Quality Guard Sol Review

## Verdict

`PASS`

The research branch is approved to begin only the GPT-5.5 Teacher paired pilot
defined in `docs/phase7/hpsv3_edit_stress_pilot.md`. This verdict does not
approve PlannerContext v0.8 for the frozen SFT planner, SFT export, or policy
promotion.

## Protocol

No P0/P1 blocker remains. The accepted boundary is:

- HPS follows the same Attempt's Geneval2 event;
- every v0.8 context has an explicit HPS `success`, `failed`, or `missing` for
  every evaluated Attempt;
- failed/missing results expose no score, delta, or risk other than `unknown`;
- HPS image ID and digest match the execution output;
- source is the direct parent and anchor is the deterministic lineage root;
- prompt hash, delta formula, risk policy, and episode evaluator profile are
  replay-validated;
- HPS remains planner-visible advisory context and never changes reducer best,
  filters a source, vetoes Geneval2 gain, or enters an Action/SFT target.

## Pilot

The 18-episode calibration set and disjoint 60-episode confirmation set are
accepted. Offline rescoring is diagnostic only. The live mitigation test must
use the paired GPT-5.5 Teacher arms and the pre-registered conjunctive gates:
Geneval2 non-inferiority, HPS coverage, submitted-score improvement, high-risk
edit-rate reduction, and blind-human preference. Statistics use episode
clusters, never independent Attempts.

Before confirmation results are opened, persist and fingerprint the calibrated
risk-policy artifact and blind-human annotation protocol. This is an execution
prerequisite, not a protocol blocker.

## Validation

- `pytest tests/contract -q`: 79 passed.
- `pytest tests/unit -q`: 196 passed.
- schema validation: 15 passed.
- fixture validation: 106 records.
- canonical episode replay: passed.
- confirmation manifest: 60 unique episodes, 0 calibration overlap, 60 direct
  edit pairs with resolvable artifacts.
- `git diff --check`: passed.

Review gate triggered and passed.
