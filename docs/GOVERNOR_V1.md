# AURELIX Central Governor V1

The Governor is the central routing boundary for autonomous proposals.

```text
Research / Opportunity / Experiment / Innovation / Business
                         ↓
                      GOVERNOR
                  ↙      ↓       ↘
             ALLOWED   OWNER     BLOCKED
                       REQUIRED
                         ↓
                 EXECUTION GATE
                         ↓
                      TREASURY
```

## Routing rules

- High-risk requests (8/10 or above) are blocked by default.
- Capital requests require owner review.
- Production changes require controlled review.
- Elevated risk (5/10 or above) requires owner review.
- A policy-allowed route does not itself authorize execution.

The Governor is an orchestrator and policy boundary, not a payment executor.
