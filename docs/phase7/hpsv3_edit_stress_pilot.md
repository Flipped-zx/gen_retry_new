# HPSv3 Edit-Stress Pilot

This is a prospective evaluation plan for the auxiliary quality branch. It is
not a leaderboard claim and it does not alter the frozen 1k trajectory pool.

## Cohort Selection

From the completed 1k trajectories, retain prompt groups with at least two
canonical `edit_image` Attempts and a resolvable source/child image lineage.
Stratify by edit depth (`2`, `3+`), local difficulty, and dominant failed atom
type (`count`, `attribute`, `spatial`, `verb`). Prefer both semantic-repair and
semantic-regression examples. Freeze IDs before looking at any intervention
result. Attempts within a prompt group are not independent observations.

## Arms

- `G`: frozen v9 planner, Skill store, Geneval2, and `qwen_dual_backend@1`.
- `G+H`: the same system plus HPSv3 observations, immutable quality anchors,
  and the advisory branch/source rule in ADR-0010.

Both arms have the same image-call budget and rendering settings. HPSv3 never
adds an alternative image call, changes reducer ordering, or filters a
Geneval2 result.

## Endpoints

Primary: submitted Geneval2 passed-atom fraction and all-pass rate, reported by
prompt group and difficulty. Secondary: HPSv3 `delta_from_source` and
`delta_from_anchor`, edit-depth curves, and blind judgments of identity,
non-target preservation, and visible artifacts. Report conflict cases where
Geneval2 improves while HPS/human quality declines.

Use a small paired admission pilot first. Freeze any risk threshold on a
calibration subset, then evaluate confirmation prompts without retuning. A
positive result may support a quality-aware source heuristic; it cannot support
the claim that HPSv3 guarantees no quality loss.
