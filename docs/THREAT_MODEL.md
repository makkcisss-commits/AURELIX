# AURELIX Threat Model V1

## Objective

Identify the failure modes that could compromise AURELIX, its owner, its capital, its data, or its decision integrity.

The model follows a resource-centric, least-privilege approach. Network location alone is never treated as a trust boundary.

## Crown Jewels

1. Owner identity and authentication factors.
2. Financial authority and payment integrations.
3. Production credentials and service identities.
4. Governor policies and autonomy controls.
5. Audit records and decision history.
6. Proprietary research, strategy, customer, and business data.
7. Production systems and deployment authority.

## Primary Threats

| Threat | Impact | Primary controls |
|---|---|---|
| Stolen owner session | Critical | MFA/passkey, short-lived sessions, step-up auth, revocation |
| Credential/secret leak | Critical | secret isolation, scanning, push protection, rotation |
| Prompt/tool injection | High | untrusted-input boundaries, tool allowlists, policy gate |
| Agent privilege escalation | Critical | scoped identities, capability allowlists, Governor enforcement |
| Unauthorized spending | Critical | Treasury approval, amount limits, separation of duties |
| Malicious dependency | High | pinned/controlled dependencies, review, scanning |
| Supply-chain compromise | High | protected CI, minimal workflow permissions, review gates |
| Production tampering | Critical | protected deployment, review, audit, rollback |
| Data exfiltration | High | data classification, egress controls, least privilege |
| Audit tampering | High | append-oriented records, restricted write access, backups |
| Web/API abuse | High | authentication, authorization, rate limiting, validation, monitoring |
| Model hallucination | Medium/High | evidence requirements, confidence/uncertainty, human review for critical decisions |
| Availability failure | Medium/High | health checks, backups, recovery runbooks, fail-closed protected actions |

## AI-Specific Rule

AURELIX treats external content, retrieved documents, web pages, customer text, tool output, and model-generated text as potentially untrusted input. No instruction embedded in untrusted content may change system authority, policies, credentials, or tool permissions.

## Security Invariants

- No agent can grant itself permission.
- No agent can become Owner through a model response.
- No financial action can be inferred from a recommendation alone.
- No protected execution occurs without its required authorization record.
- No secret is required to be present in source code.
- If a required security control is unavailable, protected operations fail closed.

## Review Cycle

Threat assumptions must be revisited whenever AURELIX adds a new external integration, payment capability, privileged agent, public endpoint, data class, or deployment path.
