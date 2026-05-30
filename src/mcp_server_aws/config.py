"""Server configuration loaded from CLI args and environment."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


@dataclass
class Config:
    allow_writes: bool = False
    region: str = "us-east-1"
    profile: str | None = None
    # Maximum items to collect per paginated call before truncating.
    max_items: int = 100
    # Maximum lines to return from log queries.
    max_log_lines: int = 100


def parse_args(argv: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(
        prog="mcp-server-aws",
        description="MCP server for AWS resource inspection",
    )
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        default=False,
        help="Enable write/mutating tools (tag, stop, restart). Off by default.",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        help="Default AWS region (env: AWS_DEFAULT_REGION)",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("AWS_PROFILE"),
        help="AWS credential profile to use (env: AWS_PROFILE)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=100,
        help="Max items returned per paginated list call",
    )
    args = parser.parse_args(argv)
    return Config(
        allow_writes=args.allow_writes,
        region=args.region,
        profile=args.profile,
        max_items=args.max_items,
    )


# Module-level singleton set by __main__ before server starts.
_config: Config = Config()


def get_config() -> Config:
    return _config


def set_config(cfg: Config) -> None:
    global _config
    _config = cfg
