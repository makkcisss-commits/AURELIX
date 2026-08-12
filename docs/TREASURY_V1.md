# AURELIX Treasury V1

AURELIX now has a guarded financial-state boundary.

## Principles

- Starting capital may be zero.
- The Treasury records available, reserved and spent balances.
- A reservation can never exceed free funds.
- A reservation is not a payment.
- No payment provider, bank account or external financial side effect is connected.
- Financial execution remains behind owner approval, Governor policy and the Execution Gate.

## Flow

```text
Opportunity
   ↓
Cost / ROI proposal
   ↓
Owner approval
   ↓
Governor + Execution Gate
   ↓
Treasury availability check
   ↓
Reservation
   ↓
[future external payment adapter]
```

The Treasury is deliberately read-first in V1. External payment execution will be implemented only as a separately authorized adapter with explicit limits, auditability and a kill switch.
