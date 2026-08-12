# AURELIX Dashboard Service V1

The dashboard now has a dedicated read-only service boundary.

## Contract

```text
Control Plane state
        ↓
DashboardService
        ↓
Narrow read model
        ↓
Authenticated Private API
        ↓
Control Center
```

`DashboardService` can return health and the public `SystemSnapshot`. It cannot execute, approve, mutate, or bypass Governor controls.

This is intentionally the first real connection between the Core and the web layer: **read before write**.

## Next transport step

A framework-specific HTTPS adapter can expose the read-only endpoints after authentication and authorization middleware are in place. The browser should never connect directly to Python/Core internals.
