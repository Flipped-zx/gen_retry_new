# Flow-DPPO 200 Official-Mix Data Review Request

## Gate

`Training-pool distribution and claim-sufficiency review`

## Decision To Review

Freeze 200 non-test Flow-DPPO Geneval2-compatible prompts for new v0.7 /
PlannerContext v0.6 trajectories, then run them with one sequential episode
worker per physical GPU.

## Evidence

- The official GenEval2 file has 800 rows and exactly 100 prompts for each
  `atom_count` from 3 through 10. It does not contain official
  easy/medium/hard labels.
- The proposed hard quota is 25 prompts for every `atom_count` from 3 through
  10. The derived reporting tiers are easy=3-5 (75), medium=6-8 (75), and
  hard=9-10 (50).
- The source is the 20,000-row Flow-DPPO synthetic training file at
  `Tencent-Hunyuan/UniRL@e1a814ff9de6de644b093c6ed0106869c1881e53`.
- Selection excludes exact official prompts, the repository's conservative
  official semantic-family boundary, and all 20 previously selected source
  rows. It uses no image or evaluator outcome.
- Official skill-atom frequencies are soft selection targets. A deterministic
  trial selected 200 unique prompts with attribute=304, count=459, object=459,
  position=175, and verb=22, versus scaled official targets 303.5, 506.25,
  506.25, 165.5, and 21.5.
- Existing episode scheduling remains unchanged: one local image worker per
  GPU, episodes parallel, attempts inside an episode sequential, append-only
  resume, and no rerun of submitted episodes.

## Questions

1. Is exact atom-count balancing the correct primary meaning of
   "official-like difficulty," with easy/medium/hard explicitly labeled as
   local reporting tiers rather than official labels?
2. Are the skill soft targets and leakage exclusions sufficient to freeze this
   200-prompt training pool, or is there a blocking distribution defect?
3. What bounded claim may this data support, and what claim must remain
   unsupported without a separate official-800 evaluation?

## Non-Goals

- Do not change Action Protocol v0.5, PlannerContext v0.6, generator,
  evaluator, reward, or SFT masking.
- Do not treat these 200 synthetic training prompts as an official benchmark.
- Do not run a model, image generator, or evaluator during review.

## Expected Response

`PASS` or `FAIL` with blocking issues only, followed by the bounded claim and
any required pre-launch correction.
