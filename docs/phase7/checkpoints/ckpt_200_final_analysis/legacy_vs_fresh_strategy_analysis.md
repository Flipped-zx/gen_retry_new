# Legacy vs Fresh Strategy Analysis

The 200 completed trajectories used the selected fresh prompts and did not import legacy images, legacy attempts, or legacy parentage. Legacy evidence remains limited to the earlier read-only diagnostic reports under `docs/phase3/` and `artifacts/phase3/`.

- Fresh image attempts: 684 total; 253 generation/regeneration actions and 431 edit actions.
- Historical-best submissions: 60/200 trajectories.
- Archived invalid infrastructure runs counted as Phase 3 episodes: 0 (archived count: 1).

The fresh rollouts differ from legacy-derived traces in the evidence available to the policy: every branch, regression, best-so-far update, and submission here is grounded in v0.2 canonical events and local Geneval2 atom normalization. This makes the traces suitable for Phase 4 supervision design without treating legacy behavior as a positive target.
