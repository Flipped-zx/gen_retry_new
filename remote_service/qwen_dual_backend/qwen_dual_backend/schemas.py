from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    model_validator,
)


RequestId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]


class OutputFormat(StrEnum):
    png = "png"
    jpeg = "jpeg"
    webp = "webp"


class InferenceFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: RequestId
    prompt: str = Field(min_length=1, max_length=8192)
    negative_prompt: str | None = Field(default=None, max_length=8192)
    width: int = Field(default=1024, ge=256, le=1664)
    height: int = Field(default=1024, ge=256, le=1664)
    seed: int | None = Field(default=None, ge=0, lt=2**63)
    num_inference_steps: int = Field(default=50, ge=1, le=100)
    true_cfg_scale: float = Field(default=4.0, ge=0.0, le=20.0)
    output_format: OutputFormat = OutputFormat.png

    @model_validator(mode="after")
    def dimensions_are_aligned(self) -> "InferenceFields":
        if self.width % 16 or self.height % 16:
            raise ValueError("width and height must be multiples of 16")
        return self


class GenerateRequest(InferenceFields):
    pass


class EditRequest(InferenceFields):
    source_attempt_id: RequestId
    source_image_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    guidance_scale: float = Field(default=1.0, ge=0.0, le=20.0)
    source_image_base64: str | None = None
    source_staged_path: str | None = Field(default=None, min_length=1, max_length=4096)

    @model_validator(mode="after")
    def exactly_one_json_source(self, info: ValidationInfo) -> "EditRequest":
        count = sum(
            value is not None
            for value in (self.source_image_base64, self.source_staged_path)
        )
        if info.context and info.context.get("source_upload"):
            count += 1
        if count != 1:
            raise ValueError(
                "exactly one source image representation is required"
            )
        return self


def validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe: list[dict[str, Any]] = []
    for item in errors:
        location = [str(part) for part in item.get("loc", ()) if part != "body"]
        safe.append(
            {
                "location": location,
                "message": re.sub(r"\s+", " ", str(item.get("msg", "invalid value")))[:300],
                "type": str(item.get("type", "validation_error")),
            }
        )
    return safe
