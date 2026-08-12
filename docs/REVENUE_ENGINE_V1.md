# AURELIX Revenue Engine V1

The Revenue Engine records observed revenue by private business activity. It is deliberately separated from payment execution.

## Revenue record

- activity ID
- amount in EUR
- source
- optional external reference
- timestamp

## Rules

- Revenue observations are positive amounts only.
- Revenue is attributed to an activity.
- Recording revenue does not move money.
- Payment providers and bank integrations are outside this V1 boundary.
- Treasury remains the financial-state authority.
- Learning can consume revenue results to evaluate business experiments.

```text
Business Activity
      ↓
Observed Revenue
      ↓
Revenue Record
      ↓
Performance Metrics
      ↓
Learning
```
