# AURELIX Engine Runtime V1

The central business-learning loop is now represented as an executable pipeline:

```text
Governor → Research → Academy → Knowledge → Innovation → Experiment → Evaluation → Opportunity → Business
```

## Runtime contract

Every engine is an explicitly registered capability. The runtime does not import or execute arbitrary code based on model-generated names.

Each stage receives the accumulated state and returns a structured dictionary. The next stage receives that state plus the previous engine identifier.

## Business gate

`business` is disabled by default. Enabling it requires an explicit runtime policy. This is intentional: research and learning may be autonomous, while high-impact external action remains governed.

## Safety properties

- allowlisted capabilities
- no dynamic code execution from model output
- explicit pipeline ordering
- bounded number of steps
- business execution gate
- structured results
- test coverage for ordering and gating

This design follows least-privilege and explicit authorization principles for agentic systems. External content must remain data, not authority; high-impact actions require an appropriate approval boundary.
