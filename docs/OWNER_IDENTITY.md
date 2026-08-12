# AURELIX Owner Identity

## Purpose

This document defines the ownership boundary for AURELIX. It describes the role of the owner without storing secrets, passwords, tokens, private keys, or other credentials in the repository.

## Owner Role

**Owner / CEO:** Makan Sissoko

The owner is the final human authority for protected AURELIX decisions, subject to the security controls and approval procedures implemented by the system.

## Security Boundary

The owner's real authentication identity must be maintained outside source code. AURELIX source code must reference a stable internal owner identifier rather than hard-code credentials or authentication material.

Recommended production model:

```text
Identity Provider
      ↓
Authenticated Owner Account
      ↓
Owner Identity / Role Claim
      ↓
AURELIX Authorization Layer
      ↓
Governor
      ↓
Protected Action
```

## Protected Capabilities

Owner authorization may be required for:

- material financial expenditure;
- production deployment of protected changes;
- security configuration changes;
- governance changes;
- creation or elevation of privileged identities;
- high-risk external integrations;
- other actions explicitly classified as protected by policy.

## No Secrets in Git

Never commit:

- passwords;
- API keys;
- access tokens;
- private keys;
- session cookies;
- recovery codes;
- payment credentials;
- production connection strings containing credentials.

Production credentials belong in an appropriate secret-management system and are injected into runtime environments only when required.

## Future Human Team

Additional employees and collaborators must never inherit owner privileges by default. Each human receives a distinct identity, role, permissions, and audit trail.

The owner role is not a shared account.
