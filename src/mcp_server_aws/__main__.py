"""Entry point for `python -m mcp_server_aws` and the mcp-server-aws console script."""

import sys

from .config import parse_args, set_config
from .server import mcp


def main() -> None:
    cfg = parse_args()
    set_config(cfg)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
