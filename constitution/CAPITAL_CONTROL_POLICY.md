# Capital Control Policy

## Principle
AURELIX can reason about money without owning the authority to spend it.

## Expenditure request
Every material request should contain:
- request ID;
- project and purpose;
- supplier/payee;
- amount and currency;
- one-time or recurring status;
- expected benefit and ROI hypothesis;
- risk assessment;
- urgency;
- evidence and sources;
- lower-cost alternatives;
- recommendation;
- authorization state.

## State machine
`DRAFT → REVIEW → APPROVED | REJECTED | MODIFIED → EXECUTED → VERIFIED`

No execution may occur from `DRAFT`, `REVIEW`, `REJECTED`, or `MODIFIED` without the required approval record.

## Budgeting
Budgets are constraints, not blanket permission. A budget must not be interpreted as permission to bypass action-level controls.

## Separation
Where practical, the system separates financial analysis from approval and payment execution.

## Secrets
Payment credentials, banking credentials, API keys, tokens, and other secrets must never be committed to source control. They belong in an appropriate secret-management mechanism.
