# Qwen Original-Prompt Baseline

Status: **PASS**; episodes: 20; variants/episode: 5.

| Arm | Passed atoms | AM | GM | All-pass |
| --- | ---: | ---: | ---: | ---: |
| Single raw prompt (variant 0) | 105/146 (71.92%) | 72.42 | 14.23 | 0/20 |
| Best-of-5, highest GM | 121/146 (82.88%) | 82.31 | 39.27 | 5/20 |
| Best-of-5, pass-count first | 121/146 (82.88%) | 82.31 | 39.27 | 5/20 |

Prompt input: exact TaskSpec `original_prompt`; no SFT action, Skill, edit, or Teacher planner is used.
