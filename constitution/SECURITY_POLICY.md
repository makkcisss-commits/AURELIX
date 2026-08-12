# Security Policy

AURELIX is intended to be private, but obscurity is never a security boundary.

## Required controls
- strong authentication for all administrative access;
- least-privilege authorization;
- secret isolation;
- encrypted transport and storage where applicable;
- dependency and vulnerability management;
- immutable or tamper-evident audit records for protected actions;
- isolated experimentation/sandbox environments;
- backups and recovery procedures;
- monitoring and alerting for privileged activity.

## Sensitive data
Do not commit credentials, private keys, access tokens, payment data, personal data, or production secrets.

## Internet-facing services
Any future AURELIX web application must use authentication, authorization, rate limiting, secure session handling, input validation, logging, and a hardened deployment boundary. A hidden URL is not an access-control mechanism.

## Incident principle
When a security boundary is uncertain, isolate first, preserve evidence, then investigate.
