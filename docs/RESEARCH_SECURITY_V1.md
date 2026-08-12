# AURELIX Research Security V1

Research agents consume hostile or untrusted external content. AURELIX therefore treats retrieved pages and documents as data, never as instructions.

## Fetch boundary

V1 policy:

- HTTPS only.
- Reject embedded URL credentials.
- Reject direct private, loopback, link-local and reserved IP targets.
- Enforce response-size limits.
- Enforce request timeouts.
- Bound redirect count and revalidate every redirect target before following it.
- Prefer explicit domain allowlists for sensitive deployments.
- Never forward internal credentials, cookies or authorization headers to research targets.

These controls address SSRF and excessive-agency risks; URL validation alone is not sufficient for a production crawler. OWASP recommends allowlisting trusted domains where possible and careful handling of DNS resolution and redirects.

## Agent boundary

Retrieved content cannot:

- change system policy;
- grant permissions;
- authorize payments;
- deploy production code;
- reveal secrets;
- invoke arbitrary tools.

The agent may extract claims from content, but claims require provenance and confidence before entering the Academy.

## Production hardening still required

Before exposing a real crawler, add network egress controls, isolated parsing/sandboxing, DNS-rebinding-resistant resolution, MIME/content validation, rate limiting, audit logs, secret isolation and adversarial tests.
