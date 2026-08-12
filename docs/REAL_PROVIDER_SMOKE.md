# Real provider validation

AURELIX can be validated against real external providers without committing secrets.

## Required environment

```text
AURELIX_RESEARCH_PROVIDER=tavily
AURELIX_RESEARCH_API_KEY=<real Tavily key>
AURELIX_MODEL_BASE_URL=<OpenAI-compatible HTTPS endpoint>
AURELIX_MODEL_API_KEY=<real model key>
AURELIX_MODEL_NAME=<model name>
```

Never put these values in Git.

## Validation rule

The real-provider smoke test must prove:

1. the configured model endpoint is reachable;
2. Tavily returns source-backed evidence;
3. AURELIX persists that evidence in its knowledge repository;
4. the model gateway can consume the resulting evidence and return a non-empty response.

The smoke test must stop before experiment evaluation unless observations come from a real observation source. It must not invent measurements merely to make the test pass.

## Run

From the repository root:

```bash
python scripts/smoke_real_providers.py
```

Exit code `0` means both external providers were reached successfully. Exit code `2` means required configuration is missing. Any provider or parsing failure exits non-zero.

A successful smoke test is **real-provider evidence**, but it is not proof that production deployment is complete.
