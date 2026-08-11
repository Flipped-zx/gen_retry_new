# Source Provenance

- Source host role: `model_deploy_10099` Generate service
- Export date: 2026-08-11
- Export archive: `qwen_dual_backend_sanitized_20260811.tar.gz`
- Archive SHA-256: `4ccbf1ddfa6f28d9b18edfb61177101f2d3f3cf9a5ff207c3e2cfb0f5765d9ea`
- Imported files: 25
- Evidence class: local deployment implementation, copied with user authorization

The archive itself is not committed. `UPSTREAM_SHA256SUMS` preserves the exact
second export manifest after the deployment source received its generic Edit
contract fixes. RL-side review then aligned input-versus-normalized source
digests with `RemoteQwenImageAdapter` and added an Edit-only readiness role.
These changes do not install or enable Edit on model_deploy_10099.

Credentials, model weights, runtime state, generated images, logs, caches,
virtual environments, host paths, and deployment backups are excluded.
