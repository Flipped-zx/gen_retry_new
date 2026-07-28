from __future__ import annotations


def patch_torch_from_numpy_if_needed() -> None:
    """Work around local torch/numpy ABI mismatch without changing call sites."""

    import numpy as np
    import torch

    probe = np.array([1.0], dtype=np.float32)
    try:
        torch.from_numpy(probe)
        return
    except TypeError as exc:
        if "expected np.ndarray" not in str(exc):
            raise

    original_from_numpy = torch.from_numpy

    def compatible_from_numpy(array):  # type: ignore[no-untyped-def]
        try:
            return original_from_numpy(array)
        except TypeError as exc:
            if "expected np.ndarray" not in str(exc):
                raise
            return torch.as_tensor(array)

    torch.from_numpy = compatible_from_numpy  # type: ignore[method-assign]
