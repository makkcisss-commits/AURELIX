# AURELIX Research Engine V1

The Research Engine is evidence-first. It separates retrieval from reasoning and never treats an unverified model response as a source.

## Pipeline

```text
Research objective
      ↓
Retriever adapter
      ↓
Normalized sources
      ↓
Evidence-backed findings
      ↓
Confidence
      ↓
Academy / Innovation / Opportunity engines
```

Each finding must reference at least one known source. Confidence is constrained to `0..1` and is an assessment, not proof of truth.

## Source adapters

The core intentionally does not hard-code a web provider. Future adapters can connect approved search APIs, document stores, datasets or internal knowledge while preserving the same evidence contract.

## Safety and governance

Research can inform recommendations but cannot authorize spending, production changes or external execution. Any resulting action must enter the Governor and approval/execution gates.
