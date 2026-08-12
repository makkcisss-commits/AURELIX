# Change Management

AURELIX evolves through controlled change.

## Change classes
- **C0 — Documentation:** policies/docs with no runtime effect.
- **C1 — Reversible internal:** tests, prompts, non-critical workflows.
- **C2 — Operational:** changes affecting normal service behavior.
- **C3 — Critical:** security, identity, capital controls, governance, production infrastructure.

## Required path
`PROPOSE → REVIEW → TEST → EVIDENCE → APPROVAL GATE → DEPLOY → OBSERVE → VERIFY`

Critical changes must be reversible where technically possible and must have an identified rollback procedure.

## Self-improvement
AURELIX may generate change proposals and run isolated experiments. It must not silently promote its own critical changes into production.
