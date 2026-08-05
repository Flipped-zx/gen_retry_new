from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from gen_retry.domain.artifacts import sha256_bytes


ROOT = Path(__file__).resolve().parents[2]
COHORT_PATH = ROOT / "artifacts/phase7/edit_stress_confirmation_cohort_v1.json"


def test_edit_stress_confirmation_cohort_is_disjoint_and_resolvable() -> None:
    cohort = json.loads(COHORT_PATH.read_text(encoding="utf-8"))
    episodes = cohort["episodes"]
    episode_ids = [episode["episode_id"] for episode in episodes]

    assert cohort["schema_version"] == "edit_stress_confirmation_cohort_v1"
    assert cohort["target_episode_count"] == 60
    assert cohort["selected_episode_count"] == len(episodes) == 60
    assert len(set(episode_ids)) == 60
    assert set(episode_ids).isdisjoint(cohort["calibration_exclusion_episode_ids"])
    assert sum(cell["selected_episode_count"] for cell in cohort["stratum_summary"]) == 60
    assert Counter(episode["stratum"] for episode in episodes) == Counter(
        {
            cell["stratum"]: cell["selected_episode_count"]
            for cell in cohort["stratum_summary"]
        }
    )

    for source_ref, sha_ref in (
        ("official_selected_prompts", "official_selected_prompts_sha256"),
        ("prepared_rollouts", "prepared_rollouts_sha256"),
    ):
        path = ROOT / cohort["source_artifacts"][source_ref]
        assert path.is_file()
        assert sha256_bytes(path.read_bytes()) == cohort["source_artifacts"][sha_ref]

    # The large frozen run is intentionally not versioned. Validate full local
    # closure when it is mounted, while keeping clean Git checkouts testable.
    if not (ROOT / cohort["source_run_root"]).is_dir():
        return

    for episode in episodes:
        state_path = ROOT / episode["episode_state_path"]
        assert state_path.is_file()
        assert (ROOT / episode["task_spec_path"]).is_file()
        assert (ROOT / episode["manifest_path"]).is_file()
        state = json.loads(state_path.read_text(encoding="utf-8"))
        pair = episode["primary_hps_rescore_pair"]
        parent = state["attempts"][pair["parent_attempt_id"]]
        child = state["attempts"][pair["child_attempt_id"]]

        assert child["operation"] == "edit"
        assert child["parent_attempt_id"] == parent["attempt_id"]
        assert parent["image_artifact_id"] == pair["parent_image_artifact_id"]
        assert child["image_artifact_id"] == pair["child_image_artifact_id"]
        assert (ROOT / pair["parent_image_path"]).is_file()
        assert (ROOT / pair["child_image_path"]).is_file()
        assert (ROOT / pair["parent_geneval2_path"]).is_file()
        assert (ROOT / pair["child_geneval2_path"]).is_file()
