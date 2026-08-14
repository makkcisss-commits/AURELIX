# Issue #37 — canonical capability escalation

## Problem
The autonomous runtime can detect an unknown required capability, but the canonical `EngineFactory` did not inject a `CapabilityEscalator`. That meant the production composition could stop at `capability_escalation_unavailable` instead of sending the gap to the Academy learning path.

## Required invariant
`unknown capability → controlled block → deduplicated gap → Academy objective → learning/evaluation → validated capability → governed execution`

The escalation path must use the same intelligence registry owned by the canonical composition and must never grant execution authority by itself.
