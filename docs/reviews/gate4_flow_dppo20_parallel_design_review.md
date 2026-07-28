# Gate 4 Flow-DPPO 20-Trajectory Design Review

Reviewer: GPT-5.6 Sol

Initial verdict: `REQUEST_CHANGES`

## Blocking Issues

1. Resume must cover the complete image-round suffix:
   `image_execution_completed -> geneval2_completed -> memory_reduced ->
   round_record_persisted -> next planner_context`.
2. Preparation must refuse non-empty episode directories. Resume may operate
   only on the same immutable task and source provenance.
3. Selection must use actual VQA count in addition to `atom_count`, record a
   deterministic semantic-family identifier, and protect the official 800-row
   test boundary.
4. The two-GPU scheduler must prove one visible device per child, one active
   child per device, and continued queue consumption after one episode fails.

## Accepted Direction

- Prompt mix: 12 hard, 5 medium, 3 easy.
- Scheduler: one fixed sequential worker queue per physical GPU.
- Persistent model residency: not a launch prerequisite.
- Start only after the four blocking issues are covered by focused tests.

## Resolution

- Full image-round suffix recovery and cached report reuse are implemented.
- Non-empty preparation is rejected.
- Flow-DPPO selection uses both metadata atom count and actual VQA count.
- Exact prompt and semantic-family overlaps with the official 800 rows are
  excluded.
- HCU workers expose exactly one physical card through
  `ROCR_VISIBLE_DEVICES`.
- A failed episode does not stop its device worker.
- Local model loading is globally serialized to avoid transient host-memory
  peaks; inference remains parallel across both cards.

Launch validation:

- Contract tests: 74 passed.
- Unit tests before launch: 61 passed; 62 passed after the instruction-quality
  boundary fix; focused resource/recovery tests also pass.
- Prepared episodes: 20 fresh PlannerContext v0.5 directories.
- Render settings: 40 steps, 1024 x 1024.
