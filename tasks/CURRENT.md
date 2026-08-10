# Current Task Index

The repository is in Phase 8, beyond the bootstrap Phase 0--4 task files.
Those earlier files are historical gate specifications, not the current work
queue.

Authoritative current state and next action:

- `docs/status.md`
- `docs/phase8/geneval2_atomic_branch_rl_plan.md`
- `docs/decisions/ADR-0011-geneval2-atomic-branch-credit-rl.md`
- `docs/reviews/geneval2_rl_sol_review.md`

Current protocol baseline:

- Action protocol v0.5;
- PlannerContext v0.7 for new rollouts;
- `qwen_dual_backend@1` execution profile;
- frozen v9 SFT checkpoint is the RL initialization;
- trainer-side offline provenance validation is implemented; live RL remains
  gated on frozen fresh-prompt manifests and a 32-group resume/replay smoke;
- ABC follows the terminal-only naive GRPO baseline.

Reference governance:

- external source roots remain read-only;
- sibling/legacy Gen-Retry repositories are excluded unless a future task
  explicitly requests bounded archaeology;
- start reference work at `references/README.md` and
  `docs/research/related_work_evidence_map.md`.
