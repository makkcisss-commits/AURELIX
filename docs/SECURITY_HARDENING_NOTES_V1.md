# AURELIX security hardening notes V1

- All protected endpoints authenticate the presented secret before business logic.
- Action endpoints require explicit resource/operation/scope authorization.
- Financial outcome admission remains separate from authentication and requires Governor provenance.
- External research/model content is treated as untrusted data, never as execution authority.
- The browser client must expose only routes that exist on the server.
- CI must remain the final proof; code changes are not considered production-ready until the relevant checks pass.

Security basis: least privilege, complete mediation, human approval for high-impact actions, and auditability align with current OWASP guidance for agentic systems.
