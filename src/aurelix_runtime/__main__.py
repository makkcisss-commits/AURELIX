from __future__ import annotations

import argparse
import os

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from .http import serve_private_control
from .system import AurelixSystem, SystemConfig
from .runtime import RuntimeConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="AURELIX autonomous runtime")
    parser.add_argument("--db", default=os.environ.get("AURELIX_DB", "data/aurelix.db"))
    parser.add_argument("--control", action="store_true", help="serve private read-only control endpoint")
    args = parser.parse_args()

    factory = EngineFactory(
        EngineFactoryConfig(runtime=RuntimeConfig(database_path=args.db), register_autonomy=True)
    )
    system = AurelixSystem(SystemConfig(runtime=RuntimeConfig(database_path=args.db)), factory=factory)
    try:
        if args.control:
            server = serve_private_control(factory.runtime)
            server.serve_forever()
        else:
            system.run_forever()
    finally:
        system.close()
        factory.runtime.close()


if __name__ == "__main__":
    main()
