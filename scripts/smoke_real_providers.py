"""Smoke-test configured real model and research providers.

This script never invents research results or experiment observations. It requires
real provider credentials in the environment and stops after proving that the
external providers can be reached and that their outputs can enter AURELIX.
"""
from __future__ import annotations

import os
import sys

from aurelix_core.engine_factory import EngineFactory
from aurelix_core.model_gateway import GenerationRequest
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def main() -> int:
    os.environ.setdefault("AURELIX_RESEARCH_PROVIDER", "tavily")
    missing = [
        name
        for name in (
            "AURELIX_MODEL_BASE_URL",
            "AURELIX_MODEL_API_KEY",
            "AURELIX_RESEARCH_API_KEY",
        )
        if not os.getenv(name)
    ]
    if missing:
        print("Missing required real-provider environment variables:")
        for name in missing:
            print(f"  - {name}")
        return 2

    runtime = AurelixRuntime(RuntimeConfig(database_path=":memory:"))
    factory = EngineFactory(runtime=runtime, knowledge=InMemoryKnowledgeRepository())

    if factory.model_provider is None or factory.model_gateway is None:
        print("FAIL: model provider was not configured")
        return 1
    if factory.research_provider is None:
        print("FAIL: research provider was not configured")
        return 1
    if not factory.model_gateway.health():
        print("FAIL: model provider health check failed")
        return 1

    evidence = factory.research_and_store("current trends in bounded workflow automation")
    if not evidence.evidence:
        print("FAIL: Tavily returned no source-backed evidence")
        return 1

    request = GenerationRequest(
        prompt=(
            "Summarize the following source-backed research evidence in one concise sentence.\n"
            + "\n".join(item.claim for item in evidence.evidence[:5])
        ),
        action="smoke.real_provider",
        actor_id="smoke-test",
    )
    summary = factory.model_gateway.generate(request)
    if not summary.strip():
        print("FAIL: model provider returned an empty response")
        return 1

    print("PASS: real research provider returned source-backed evidence")
    print(f"Evidence count: {len(evidence.evidence)}")
    print("PASS: real model provider generated a non-empty response")
    print(f"Model response: {summary.strip()}")
    print("STOP: no experiment observations were fabricated by this smoke test.")
    print("Next step: execute an experiment with measurements from a real observation source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
