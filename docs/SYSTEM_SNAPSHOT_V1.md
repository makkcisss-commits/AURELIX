# AURELIX System Snapshot V1

The Control Center receives a deliberately narrow public snapshot from the Core.

The snapshot is a **read model**, not an authorization object. It contains dashboard-safe state only and grants no execution authority.

```text
Core state
   ↓
Public snapshot
   ↓
Private API / authenticated transport
   ↓
Control Center
```

The browser must never infer permission from a green state. Authorization remains server-side in the Control Plane and Governor.

As the system grows, richer read models can be added for tasks, approvals, budgets and audit activity without exposing internal secrets or control primitives.
