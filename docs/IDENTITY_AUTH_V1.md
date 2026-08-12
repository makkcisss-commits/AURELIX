# AURELIX Private Identity & Authentication V1

AURELIX must know which principal is requesting an action before authorization can begin.

## Model

```text
Credential
   ↓
Authentication
   ↓
Identity
   ↓
Role / Autonomy
   ↓
Resource Scope
   ↓
Governor
```

The identity layer does not grant permissions. It only establishes an authenticated principal that downstream policy can evaluate.

## Current Foundation

V1 provides:

- explicit identity IDs;
- active/revoked/disabled states;
- salted `scrypt` password-equivalent credential hashing;
- constant-time digest comparison;
- credential-to-identity binding;
- fail-closed authentication for inactive identities.

The implementation is deliberately independent of the web framework and should not be treated as a complete production IAM system.

## Production Requirements

Before exposing a public or private API, add:

- authenticated owner account/session management;
- secure secret storage and rotation;
- MFA/passkeys for owner access;
- session/token expiry and revocation;
- rate limiting and lockout controls;
- service-to-service identity;
- least-privilege credentials;
- secret redaction;
- security event audit;
- recovery procedures;
- HTTPS/TLS at the network boundary.

Never commit plaintext credentials, API keys, signing keys, or generated secrets to the repository.
