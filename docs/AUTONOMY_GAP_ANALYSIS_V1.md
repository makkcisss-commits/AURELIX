# AURELIX Autonomy Gap Analysis V1

## Can AURELIX currently run itself end-to-end?

**No.** The repository has strong core boundaries and several engines, but it is not yet a self-running production system.

Current capabilities include policy routing, read-only control aggregation, revenue observation, research-source safety, evidence relationships, source intelligence, and an auditable knowledge graph.

## Missing runtime layers

1. Durable persistence for state and knowledge.
2. Scheduler/event loop for recurring work.
3. Agent runtime with explicit tool permissions.
4. Research provider adapters and controlled retrieval workers.
5. Academy curriculum and knowledge-maintenance loops.
6. Experiment registry, evaluation, and rollback.
7. Opportunity scoring and prioritization.
8. Build/deployment sandbox with approval gates.
9. Real authentication, authorization, audit logging, secrets management, and network isolation.
10. Observability: health, metrics, traces, alerts, and failure recovery.
11. Human approval queue for capital, production, security, and high-impact decisions.
12. Web Control Center.

## Target autonomous loop

```text
SCHEDULER
   ↓
GOVERNOR
   ↓
RESEARCH
   ↓
EVIDENCE / VERIFICATION
   ↓
ACADEMY MEMORY
   ↓
KNOWLEDGE GAP DETECTION
   ↓
INNOVATION / OPPORTUNITY
   ↓
EXPERIMENT
   ↓
EVALUATION
   ├── FAIL → LEARNING → ACADEMY
   └── PASS → GOVERNOR
                  ↓
          OWNER APPROVAL when required
                  ↓
               BUILD
                  ↓
              BUSINESS
                  ↓
              REVENUE
                  ↓
              LEARNING
                  ↺
```

## Autonomy rule

AURELIX may autonomously research, organize knowledge, identify gaps, propose experiments, evaluate outcomes, and prepare recommendations. It may not autonomously spend capital, change production-critical controls, deploy sensitive changes, or alter its own security/governance rules.

## Definition of done for autonomous V1

The system should survive restarts, preserve provenance, recover failed jobs, prevent unauthorized tool use, expose an auditable approval queue, and demonstrate the complete loop in a sandbox before any production autonomy is enabled.
