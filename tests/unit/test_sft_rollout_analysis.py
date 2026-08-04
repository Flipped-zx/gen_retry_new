from __future__ import annotations

import pytest

from gen_retry.analysis.sft_rollout import _validate_request_output_alignment


def test_request_output_alignment_allows_transport_retry() -> None:
    requests = [
        {"request_id": "ep_turn_000"},
        {"request_id": "ep_turn_000"},
        {"request_id": "ep_turn_001"},
    ]
    outputs = [
        {"request_id": "ep_turn_000"},
        {"request_id": "ep_turn_001"},
    ]

    _validate_request_output_alignment("ep", requests, outputs)


def test_request_output_alignment_rejects_missing_success() -> None:
    requests = [
        {"request_id": "ep_turn_000"},
        {"request_id": "ep_turn_001"},
    ]
    outputs = [{"request_id": "ep_turn_000"}]

    with pytest.raises(ValueError, match="ids mismatch"):
        _validate_request_output_alignment("ep", requests, outputs)


def test_request_output_alignment_rejects_duplicate_success() -> None:
    requests = [{"request_id": "ep_turn_000"}]
    outputs = [
        {"request_id": "ep_turn_000"},
        {"request_id": "ep_turn_000"},
    ]

    with pytest.raises(ValueError, match="duplicate successful"):
        _validate_request_output_alignment("ep", requests, outputs)
