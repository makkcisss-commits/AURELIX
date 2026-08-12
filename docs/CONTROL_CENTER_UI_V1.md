# AURELIX Control Center UI V1

The Control Center is the private visual layer above the Control Plane. It is a read-first command center: visibility is broad, authority is narrow.

## Visual status language

AURELIX uses a calm status language rather than decorative error crosses:

- **Green check** = verified healthy / operational.
- **Amber attention** = something needs review; it is not an execution authorization.
- **Neutral pending** = waiting for a decision, approval, or verification.

A red cross is not used as the normal dashboard status symbol. Security-critical failures still remain machine-readable and auditable; the visual system should communicate them clearly without turning the dashboard into a wall of red.

## Governor visibility

The Governor must be a first-class Control Center section. The owner should be able to see:

- current Governor state;
- active policy version;
- autonomy level;
- decisions awaiting owner approval;
- blocked actions and reasons;
- budget checks;
- resource-scope checks;
- circuit-breaker state;
- recent audit events.

The dashboard must never imply that a green visual status means unrestricted autonomy. Green means the displayed component has passed its defined health checks.

## First screen

```text
AURELIX CONTROL CENTER

SYSTEM                    ✓ HEALTHY
GOVERNOR                  ✓ OPERATIONAL
POLICY                    ✓ ACTIVE
AUDIT                     ✓ RECORDING
PRIVATE API              ✓ PROTECTED
EXECUTION                ✓ GUARDED
TREASURY                  • OWNER CONTROL

DECISIONS REQUIRING YOU
  [review] ...

RECENT ACTIVITY
  ✓ research completed
  ✓ policy check completed
  • approval pending
```

## Security boundary

The UI never talks directly to execution primitives. All actions go through the Private API and then the Control Plane. A visual control cannot bypass Governor, approval, budget, scope, circuit-breaker, or audit gates.
