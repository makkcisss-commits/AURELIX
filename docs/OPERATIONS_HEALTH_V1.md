# AURELIX Operations Health V1

The runtime exposes a small internal health model so the Control Plane can distinguish healthy, degraded, and unknown states.

## States

- `ok`: every registered component reports `ok`.
- `degraded`: at least one registered component is not `ok`.
- `unknown`: no components have reported yet.

Health is observational only. It does not grant an agent permission to restart production systems, change policy, or alter security controls.

## Production direction

The next operations layer should connect this registry to durable persistence, worker heartbeats, scheduler state, queue depth, database connectivity, model/provider availability, audit integrity, metrics, alerting, and a real external liveness/readiness endpoint.

The control plane must remain fail-closed for privileged operations: an unhealthy or unknown component must not silently become an authorization signal.
