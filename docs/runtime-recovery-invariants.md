# Runtime recovery invariants

AURELIX runtime execution state is durable and must remain correct across crashes and retries.

## Invariants

1. A job can transition from `queued` to `running`, then to `completed` or `failed`.
2. A stale `running` job is recovered without being treated as successful.
3. A retry reuses the same `job_id`/execution identifier and may not create a second durable result.
4. A successful terminal state is committed atomically with its durable result.
5. A failed terminal state records a durable failure result.
6. A terminal job cannot be completed again with a different result.
7. Concurrent workers may not claim the same queued job.
8. Runtime state is stored on a persistent Docker named volume in the production Compose deployment.

These invariants are intentionally stronger than process-local state: restarting the process or recreating the container must not invent success or silently duplicate execution.