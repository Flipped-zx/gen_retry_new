Read `AGENTS.md`, `README_START_HERE.md`, `DEVELOPMENT_BLUEPRINT.md`, `configs/paths/local.yaml`, and `tasks/PHASE_00_REPOSITORY_ARCHAEOLOGY.md`.

Execute **Phase 0 only** in this new clean-room repository.

Requirements:
- verify that every configured external source root exists;
- record Git commit, branch, dirty status, license, and exact paths without modifying any external root;
- write only inside this new repository, primarily under `docs/`;
- inspect the legacy Gen-Retry root for reusable Geneval2, Qianwen-Image-Edit, trajectory, memory, masking, resume/cache, and SFT code;
- use `source_researcher` for focused read-only inspection of Gen-Searcher and GenEvolve;
- update `docs/SOURCE_LEDGER.md` with exact paths, symbols, commits, licenses, and the specific design lesson being reused;
- produce all required Phase 0 reports;
- do not call any paid API, do not generate images, do not run Geneval2, do not change schemas, do not copy implementation code yet, and do not invoke the high-level reviewer unless authoritative sources conflict and block Phase 1.

At the end, report:
1. files written in the new repository;
2. external roots inspected;
3. evidence used;
4. unresolved conflicts;
5. exact proposed Phase 1 file plan;
6. confirmation that no external repository was modified.
