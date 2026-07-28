# 5.6sol Design Review Request: PlannerContext / Round Memory

## Scope

Review the proposed design before implementation:

- `docs/phase3/planner_context_round_memory_design.md`
- current schemas under `schemas/`
- current runtime files:
  - `src/gen_retry/runtime/planner_view.py`
  - `src/gen_retry/runtime/reducer.py`
  - `src/gen_retry/agent/teacher_client.py`
  - `src/gen_retry/phase3/live_runner.py`

## Questions

1. Are the semantic boundaries among Action Step, Planning Round, Attempt, and Transition correct, especially for `query_skill` and rollback edits?
2. Is the proposed v0.3 action schema sufficient and minimal, and does removing `strategy_tags` in favor of `interventions[].operation` avoid duplicate intent fields?
3. Is the operation registry grounded enough in current Skills/trajectory evidence, or are any operations duplicate, too broad, or likely to create future SFT ambiguity?

## Known Design Constraints

- Do not change Qwen generation/edit behavior, Geneval2 evaluation, budget semantics, best-attempt ranking, or RL/SFT algorithms.
- `query_skill` is a planner action inside the current round but not an attempt.
- `generate_image` and `edit_image` are planner image actions.
- Prompt text remains an argument of the image action; no separate prompt-refine action.
- Completed RoundRecord outcome is environment-owned and can only appear in later PlannerContext.

## Expected Output

Return `PASS` or `FAIL` with blocking issues only.
