# AURELIX Agent Identity & Authorization V1

AURELIX treats each autonomous role as a declared software identity rather than as an anonymous model invocation.

## Identity contract

An identity is derived from:

- role
- owner
- declared tools
- execution environment

Changing the declared tool set changes the derived identity. This makes capability drift visible instead of silently inheriting authority.

## Authorization model

```text
AGENT IDENTITY
     ↓
TASK SCOPE
     ↓
DECLARED TOOLS
     ↓
POLICY CHECK
     ↓
EXECUTION
     ↓
AUDIT
```

Sensitive mutations use a separate approval boundary. Authentication alone never grants permission to spend capital, deploy production changes, or modify governance/security controls.

## Design basis

NIST's 2026 software/AI-agent identity work highlights identification, authorization, auditing and non-repudiation as core concerns. OWASP's current agent-security guidance recommends per-tool least privilege, explicit authorization for sensitive operations, human approval for high-risk actions, and limits on cost, retries and tool chaining.

## Current boundary

This module establishes the identity contract and approval primitive. Production deployment still requires a real authentication provider, short-lived credentials, secret management, network policy, durable audit storage, key rotation, and independent security testing.
