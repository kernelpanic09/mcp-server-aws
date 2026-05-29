"""Lambda tool: list functions."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from ..auth import get_client
from ..config import get_config


def list_lambda_functions(region: str | None = None) -> dict[str, Any]:
    """List Lambda functions with runtime, memory, and last-modified info."""
    client = get_client("lambda", region)
    cfg = get_config()
    functions: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("list_functions")
        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                functions.append(
                    {
                        "name": fn.get("FunctionName"),
                        "arn": fn.get("FunctionArn"),
                        "runtime": fn.get("Runtime"),
                        "handler": fn.get("Handler"),
                        "code_size": fn.get("CodeSize"),
                        "memory_mb": fn.get("MemorySize"),
                        "timeout_seconds": fn.get("Timeout"),
                        "last_modified": fn.get("LastModified"),
                        "role": fn.get("Role"),
                        "description": fn.get("Description", ""),
                    }
                )
                if len(functions) >= cfg.max_items:
                    return {"functions": functions, "truncated": True}
    except ClientError as e:
        return {"error": e.response["Error"]["Code"], "message": str(e)}

    return {"functions": functions, "truncated": False}
