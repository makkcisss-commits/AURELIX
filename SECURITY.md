# Security Policy

AURELIX is a private entrepreneurial system. Security issues can affect owner identity, capital, proprietary information, and production infrastructure.

## Reporting

Do not publish sensitive vulnerability details in a public issue. Until a private security reporting channel is configured, do not include credentials, exploit payloads containing secrets, personal data, or production access details in GitHub issues.

## Security Principles

- Assume breach rather than relying on obscurity.
- Protect identity and authorization before adding capability.
- Keep secrets out of Git.
- Fail closed for protected actions when mandatory security controls are unavailable.
- Preserve audit evidence during incidents.
- Rotate compromised credentials immediately.

## Scope

Security-sensitive components include the Governor, policy engine, owner authorization, Treasury, authentication, API, agent tool permissions, CI/CD, deployment infrastructure, and audit storage.

## Related Documents

- `constitution/SECURITY_POLICY.md`
- `constitution/AUTONOMY_POLICY.md`
- `docs/THREAT_MODEL.md`
- `docs/SECURITY_BASELINE_V1.md`
- `docs/IDENTITY_AND_ACCESS_MODEL.md`
