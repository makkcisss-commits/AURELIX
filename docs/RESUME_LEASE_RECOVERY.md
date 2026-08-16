# Resume lease recovery

Mission resume reservations are coordination state, not execution state.

- `reserved` carries a short `lease_until` deadline.
- A valid reservation prevents a second resume from being claimed.
- An expired reservation can be replaced by a fresh `execution_id`.
- `running` is considered owned only while the corresponding Runtime execution is running with an active Runtime lease.
- A completed execution remains the durable result for that execution and is never deleted by resume recovery.
- The business `mission_id` remains stable across resume attempts.
