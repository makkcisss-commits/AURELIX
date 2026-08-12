# AURELIX Security Baseline V1

This baseline defines the minimum security posture before AURELIX can become an internet-accessible control plane.

## 1. Repository

- Repository must be private before proprietary implementation is stored.
- No secrets in Git.
- `.env` and runtime secret files are ignored.
- Pull requests and CI are required for normal production changes once the team workflow is established.
- Security-sensitive changes require explicit review.

GitHub secret scanning and push protection should be enabled where the account/plan supports them. Push protection can block supported secrets before they reach the repository.

## 2. Identity

- Individual human identities only.
- Owner account is not shared.
- Strong authentication required for administration.
- MFA/passkeys are preferred for the owner control plane.
- Sessions are short-lived and revocable.
- Privileged actions use step-up authentication where appropriate.

## 3. Authorization

- Deny by default.
- Least privilege.
- Explicit role and capability assignments.
- Service identities are separate from human identities.
- Agent permissions are scoped to tools, resources, environments, and actions.
- Protected actions require the Governor authorization path.

## 4. Application/API

- HTTPS only in production.
- Strict request validation.
- Rate limiting and abuse controls.
- Secure session/cookie configuration where applicable.
- CSRF protection for cookie-authenticated browser flows.
- Centralized authorization checks.
- No direct browser-to-database or browser-to-worker privileged access.
- Structured security logging without logging secrets.

## 5. AI/Agent Security

- Treat external text and retrieved content as untrusted.
- Separate model instructions from untrusted data.
- Tool access is allowlisted.
- Tool arguments are validated independently of model output.
- High-impact actions require policy checks and, when protected, owner approval.
- Sandbox untrusted experiments.
- Never expose unrestricted shell, network, filesystem, or credential access to a general-purpose agent.

## 6. Secrets

Use a dedicated secret-management mechanism in production. Rotate credentials after suspected exposure. Never place API keys, banking credentials, private keys, recovery codes, or production tokens in source control.

## 7. Supply Chain

- Minimize dependencies.
- Review dependency changes.
- Keep runtime and CI dependencies current.
- Use automated vulnerability/code scanning where available.
- Keep CI permissions minimal.
- Treat third-party actions and packages as supply-chain dependencies.

## 8. Data

Classify data before connecting it to agents. Restrict access by purpose. Define retention and deletion rules. Prevent sensitive data from being sent to external models or services unless the integration has been explicitly approved.

## 9. Production

Production deployment must be separated from development and experiments. Protected changes require review, tests, security checks, and a rollback path.

## 10. Observability

Monitor authentication failures, privilege changes, protected decisions, financial requests, deployment events, suspicious tool use, and security-control failures.

## 11. Recovery

Maintain backups and recovery procedures for critical state. Test restoration periodically. Security and availability failures must have documented containment and recovery paths.

## Gate

AURELIX should not be exposed as a public administrative application until the minimum controls above are implemented and tested in the target deployment environment.
