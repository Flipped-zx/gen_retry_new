from __future__ import annotations

from pathlib import Path

from PIL import Image

from gen_retry.tools.qwen_common import (
    reuse_valid_cached_image,
    save_output_image,
)


def test_save_output_image_atomically_replaces_target(tmp_path: Path) -> None:
    output_path = tmp_path / "images" / "attempt.png"
    save_output_image(Image.new("RGB", (32, 24), "red"), output_path)

    with Image.open(output_path) as image:
        assert image.size == (32, 24)
    assert not list(output_path.parent.glob(".*.tmp.png"))


def test_reuse_valid_cached_image_removes_corrupt_or_wrong_size(
    tmp_path: Path,
) -> None:
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"not an image")
    assert not reuse_valid_cached_image(corrupt, expected_size=(32, 24))
    assert not corrupt.exists()

    wrong_size = tmp_path / "wrong.png"
    Image.new("RGB", (16, 16), "blue").save(wrong_size)
    assert not reuse_valid_cached_image(wrong_size, expected_size=(32, 24))
    assert not wrong_size.exists()


def test_reuse_valid_cached_image_accepts_decodable_expected_size(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "valid.png"
    Image.new("RGB", (32, 24), "green").save(output_path)

    assert reuse_valid_cached_image(output_path, expected_size=(32, 24))
