# AURELIX Authentication V1

The private Control Center is being built around a server-side session boundary.

## Security rules

- Credentials are never stored in browser JavaScript or committed to Git.
- Stored login secrets are hashed; plaintext secrets are not persisted.
- Login attempts are rate-limited.
- Sessions use an HttpOnly, Secure, SameSite=Strict cookie.
- Session tokens are short-lived and revocable.
- Dashboard reads do not grant execution authority.
- Authorization remains a separate Governor/Control Plane concern.

## Production requirement

The current V1 session store is in-memory. It is suitable for the application contract and tests, but not for a multi-instance production deployment. Before production, use a hardened server-side session store or an established identity provider, add CSRF protection for state-changing requests, audit authentication events, define recovery/rotation procedures, and put the service behind TLS and private network/access controls.
