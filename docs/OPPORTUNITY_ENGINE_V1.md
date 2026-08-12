# AURELIX Opportunity Engine V1

The Opportunity Engine converts research findings into comparable business opportunities.

## Required dimensions

- evidence/finding IDs
- cost
- estimated monthly revenue
- time to first result
- complexity
- risk
- confidence
- lifecycle stage

## Scoring principle

The V1 score is intentionally transparent. It rewards estimated upside and confidence and discounts cost, time, complexity and risk.

The score is a **recommendation aid only**. It cannot approve an opportunity, spend money, or execute an operation.

## Zero-to-first-revenue loop

```text
Research finding
      ↓
Opportunity
      ↓
Score + compare
      ↓
Recommendation
      ↓
Governor
      ↓
Owner decision
      ↓
Build / test
      ↓
Measure actual result
      ↓
Learning Engine
```

Any opportunity involving financial spend remains behind Owner Approval, Execution Gate and Treasury controls.
