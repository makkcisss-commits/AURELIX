# AURELIX Budget Guard V1

The Budget Guard provides a deterministic spending boundary for operations that carry a measurable cost.

## Principles

- Money is represented with `Decimal`, never binary floating-point arithmetic.
- A budget has an explicit currency and limit.
- An operation must be authorized before its amount is consumed.
- A rejected operation does not consume budget.
- Negative limits and negative consumption are invalid.
- Budget enforcement is separate from owner approval and financial execution.

## Example

```text
Research task
  budget = EUR 20.00
  estimated call = EUR 2.50
        ↓
Budget Guard
        ↓
remaining = EUR 20.00
        ↓
allow
```

If an operation would exceed the remaining amount:

```text
REQUEST
  ↓
Budget Guard
  ↓
BudgetExceeded
  ↓
NO EXECUTION
```

## Important Boundary

The Budget Guard does not authorize a payment by itself. It only determines whether the requested cost fits within an already-defined budget. Treasury policy and owner approval remain separate gates for financial actions.

## Future Extensions

Before production financial use, add:

- immutable budget decisions;
- per-task and per-agent budgets;
- currency conversion policy;
- reservations for concurrent operations;
- refunds/credits;
- recurring budget windows;
- owner approval integration;
- Treasury adapter with independent authorization;
- audit correlation;
- concurrency-safe persistence.
