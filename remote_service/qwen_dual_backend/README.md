# Qwen Image Remote Service

Portable source for the `qwen_dual_backend@1` asynchronous HTTP service used by
the RL `remote_http` adapter. Model weights, credentials, state, generated
images, logs, caches, and host-specific deployment data are intentionally
excluded.

## API

- `GET /healthz`
- `GET /readyz`
- `GET /openapi.json`
- `GET /v1/capabilities`
- `POST /v1/generate`
- `POST /v1/edit` (returns `503 edit_model_unavailable` without edit weights)
- `GET /v1/jobs/{request_id}`
- `GET /v1/results/{request_id}`

All `/v1/*` routes use Bearer authentication when
`QWEN_BACKEND_BEARER_TOKEN` is set. Submissions are asynchronous and
`request_id` is the idempotency key. Reusing an ID with a different canonical
payload returns HTTP 409.

## Deployment

Prerequisites are Python 3.11, a vendor PyTorch/accelerator runtime compatible
with `requirements.vendor.txt`, and local Qwen-Image-2512 weights. Do not use
`bootstrap.sh` until the pinned vendor torch build has been installed by the
machine image.

1. Place this directory at the chosen service root.
2. Put Qwen-Image-2512 weights under `models/Qwen-Image-2512`, or set
   `QWEN_GENERATE_MODEL_PATH` in `.service-env`.
3. Create `.service-env` from `service-env.example` and generate a new token.
4. If needed, set `DTK_ENV_FILE` to the vendor environment script path.
5. Run `./bin/bootstrap.sh`, then `./bin/preflight.sh --load --kind generate --devices all`.
6. Start with `./bin/start.sh` and verify `./bin/status.sh`.

Install `requirements.test.txt` into a development environment before running
`python -m pytest`. Tests use fake runtimes and do not load model weights.

The service binds to `0.0.0.0:18080`. Restrict ingress to the RL hosts and use
a TLS reverse proxy for traffic crossing an untrusted network.

The default deployment role is Generate. A dedicated Edit host uses the same
service code with `QWEN_PRELOAD_KIND=edit`, `QWEN_READY_KIND=edit`, and a local
`QWEN_EDIT_MODEL_PATH`. Do not point both logical routes at one host merely to
hide missing weights; the RL model config owns the two endpoint bindings.

Edit JSON requests include `source_attempt_id`, `source_image_base64`, the
lowercase `source_image_sha256`, and `guidance_scale`. The declared digest is
verified before queue admission. The service normalizes the source to RGB PNG
for inference while returning both the verified input digest and normalized
artifact digest.

## Adapter Smoke Test

Submit a 256x256, one-step canary with a unique `request_id`, poll
`/v1/jobs/{request_id}` until it succeeds, download `/v1/results/{request_id}`,
and compare the response SHA-256 with `result.sha256`. Repeat the same request
to verify idempotent replay, then change the prompt under the same ID to verify
HTTP 409.

## Excluded Runtime Data

Never commit `.service-env`, `models/`, `state/`, `logs/`, `run/`, `.venv/`,
`wheelhouse/`, generated images, or deployment backups.

## Imported Snapshot

`UPSTREAM_SHA256SUMS` records the 25 files in the exact sanitized export from
model_deploy_10099. Files changed during RL-side contract review intentionally
no longer match that upstream manifest; see `SOURCE_PROVENANCE.md`.
