from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "qwen_dual_backend.app:app",
        host="0.0.0.0",
        port=18080,
        workers=1,
        access_log=True,
        log_level="info",
        timeout_keep_alive=10,
        timeout_graceful_shutdown=30,
        limit_concurrency=128,
        server_header=False,
    )


if __name__ == "__main__":
    main()
