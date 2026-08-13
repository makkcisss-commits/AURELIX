from __future__ import annotations

import argparse
import os

from .http import serve_private_control
from .integrated_engines import ResearchEngine
from .pipeline_runner import GovernedPipeline
from .research_provider import HttpResearchProvider
from .runtime import AurelixRuntime, RuntimeConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="AURELIX autonomous runtime")
    parser.add_argument("--db", default=os.environ.get("AURELIX_DB", "data/aurelix.db"))
    parser.add_argument("--control", action="store_true", help="serve private read-only control endpoint")
    args = parser.parse_args()

    runtime = AurelixRuntime(RuntimeConfig(database_path=args.db))
    provider = HttpResearchProvider.from_env()
    pipeline = GovernedPipeline(research_engine=ResearchEngine(provider=provider))
    runtime.register_pipeline(pipeline)
    # Mount the complete autonomy fabric on the same RuntimeStore and worker loop.
    # This prevents scheduler/worker/autonomy from creating independent lifecycles.
    runtime.register_autonomy()
    if args.control:
        server = serve_private_control(runtime)
        server.serve_forever()
    else:
        runtime.serve_forever()


if __name__ == "__main__":
    main()
