# Current Task Index

The repository is in Phase 7, beyond the bootstrap Phase 0--4 task files.
Those earlier files are historical gate specifications, not the current work
queue.

Authoritative current state and next action:

- `docs/status.md`
- `docs/phase7/high_quality_trajectory_policy_and_evidence_plan.md`
- `docs/operations/phase7_flow_dppo1000_v9_live_status.md`

Current protocol baseline:

- Action protocol v0.5;
- PlannerContext v0.7 for new rollouts;
- `qwen_dual_backend@1` execution profile;
- v9 SFT re-freeze remains open pending the documented compatibility audit and
  paired rollout evidence.

Reference governance:

- external source roots remain read-only;
- sibling/legacy Gen-Retry repositories are excluded unless a future task
  explicitly requests bounded archaeology;
- start reference work at `references/README.md` and
  `docs/research/related_work_evidence_map.md`.
