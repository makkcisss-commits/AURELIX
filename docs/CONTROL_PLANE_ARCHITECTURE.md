# AURELIX Control Plane Architecture

The Control Plane is the private administrative interface for AURELIX. It is an interface to the system, not the system itself.

```text
Browser / Future Mobile App
          |
          v
   Authentication Layer
          |
          v
      Private API
          |
     Authorization
          |
          v
       Governor
      /   |    \
     /    |     \
  Audit Policy  Core State
     |     |      |
     +-----+------+
           |
       Engine APIs
           |
     Agents / Workers
```

## Design Rules

1. The browser never receives privileged infrastructure credentials.
2. The UI never bypasses the API and Governor for protected actions.
3. Authentication and authorization are separate concerns.
4. Treasury actions pass through explicit financial policy gates.
5. Every protected action has an audit event and correlation ID.
6. The API is designed to support a future mobile client without duplicating business logic.
7. Internal services communicate through authenticated service identities.
8. Secrets are injected at runtime from a secret-management mechanism; they are not stored in Git.

## Initial Control Center Areas

- Overview / system health
- Decisions awaiting owner approval
- Opportunity pipeline
- Research queue
- Academy / knowledge
- Experiments
- Agent status
- Treasury requests
- Audit trail
- Security / access

## Deployment Boundary

The first production deployment should place the Control Plane behind strong authentication and HTTPS. Administrative endpoints should not be publicly usable without authentication, and sensitive operations should have additional authorization and, where appropriate, step-up authentication.

## Fail-Closed Principle

AURELIX may operate continuously, but availability never overrides authorization. If an authorization service, audit mechanism, or required security control is unavailable, protected actions should fail closed rather than silently downgrade security.
