from __future__ import annotations

import argparse
import os

from .runtime import AurelixRuntime, RuntimeConfig
from .http import serve_private_control


def main() -> None:
    parser = argparse.ArgumentParser(description="AURELIX autonomous runtime")
    parser.add_argument("--db", default=os.environ.get("AURELIX_DB", "data/aurelix.db"))
    parser.add_argument("--control", action="store_true", help="serve private read-only control endpoint")
    args = parser.parse_args()

    runtime = AurelixRuntime(RuntimeConfig(database_path=args.db))
    if args.control:
        server = serve_private_control(runtime)
        server.serve_forever()
    else:
        runtime.serve_forever()


if __name__ == "__main__":
    main()
