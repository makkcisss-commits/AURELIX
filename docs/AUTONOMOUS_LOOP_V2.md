# AURELIX Autonomous Loop V2

The runtime is now designed around an explicit capability registry. A scheduled job can invoke only a registered capability, and submission passes through Governor routing before entering the queue.

## Operating loop

```text
SCHEDULER
  -> ORCHESTRATOR
  -> GOVERNOR
  -> CAPABILITY
  -> WORKER
  -> AUDIT
  -> KNOWLEDGE / RESULT
  -> NEXT JOB
```

## Intelligence loop

```text
ACADEMY KNOWLEDGE
  -> GAP DETECTION
  -> RESEARCH PLAN
  -> EVIDENCE
  -> VERIFIED FINDING
  -> INNOVATION PROPOSAL
  -> EXPERIMENT
  -> EVALUATION
  -> LESSON
  -> ACADEMY
```

Innovation proposals are proposals only. Capital, production changes, and other high-impact actions remain outside autonomous execution until the applicable Governor and owner-approval gates authorize them.

This design follows NIST's continuous Govern/Map/Measure/Manage lifecycle and OWASP's least-privilege and transaction-safeguard guidance for agentic systems.
