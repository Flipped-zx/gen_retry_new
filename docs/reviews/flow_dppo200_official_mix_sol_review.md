# Flow-DPPO 200 Official-Mix Sol Review

Reviewer: GPT-5.6 Sol

## Initial Verdict

`PASS`

Blocking issues: none.

## Verified Design

- Official GenEval2 has 800 prompts with exactly 100 prompts for each
  `atom_count` from 3 through 10.
- The selected pool uses 25 prompts for each atom count, producing local
  reporting tiers easy=75, medium=75, and hard=50.
- All 200 prompts and source rows are unique.
- Exact official prompts, conservative official semantic-family overlaps, and
  the 20 previously selected Flow-DPPO source rows are excluded.
- Selection uses metadata only and does not use generated images or Geneval2
  outcomes.
- Skill frequencies are soft-balanced rather than claimed as exactly matched.

## Required Pre-Launch Corrections

The reviewer requested:

1. freeze and persist the selection artifact SHA;
2. label difficulty tiers as local rather than official;
3. report selected-versus-target skill deviations;
4. report the actual VQA-count histogram;
5. test deterministic same-input equality.

All five corrections were implemented. The frozen selection artifact is:

```text
artifacts/phase7/flow_dppo200_official_mix_selected_prompts.json
sha256=25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8
```

The SHA is locked in the preparation summary and every episode
`rollout_plan.json`. Two independent selector executions produced
byte-identical artifacts.

## Final Verdict

`PASS`

Blocking issues: none.

## Claim Boundary

Supported: this is a deterministic, non-test synthetic training pool whose
`atom_count` marginal exactly matches official GenEval2 and whose skill
coverage is soft-balanced toward the official aggregate.

Unsupported without a separate held-out official-800 evaluation: official
benchmark performance, benchmark improvement, generalization, or official
easy/medium/hard difficulty.
