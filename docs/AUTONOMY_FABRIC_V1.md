# AURELIX Autonomy Fabric V1

The autonomy fabric is the single execution boundary for the first complete AURELIX loop.

```text
objective -> research -> academy -> knowledge -> innovation -> experiment
          -> evaluation -> opportunity -> business approval
```

Every run has one durable execution ID and is persisted through the runtime execution store. Engine state is persisted through the same runtime state boundary so knowledge, experiments, opportunities, and audit history survive process restart.

The business boundary remains proposal/approval gated. Research evidence remains data and provenance; engine output does not grant credentials, budget, production access, or authorization.

This is the integration chassis. Provider adapters, scheduler triggers, retrieval workers, evaluation execution, approval workflows, and commercial actions attach to this fabric rather than creating independent lifecycle systems.
