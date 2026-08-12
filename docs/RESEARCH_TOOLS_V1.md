# AURELIX Research Tools V1

AURELIX treats external research as an evidence pipeline, not as trusted instructions.

## Pipeline

```text
Research Plan
  ↓
Source Discovery
  ↓
HTTP(S) Retrieval Adapter
  ↓
Normalize / Hash
  ↓
Untrusted Content
  ↓
Extraction
  ↓
Claim + Source IDs
  ↓
Cross-check / Confidence
  ↓
Research Finding
  ↓
Academy / Opportunity / Innovation
```

## Trust boundary

Web pages, documents and datasets are **data**. Instructions embedded in retrieved content must never become AURELIX system instructions or tool permissions.

This boundary is required because indirect prompt injection can arrive through websites or files and can manipulate agent behavior. OWASP identifies prompt injection and excessive agency as major LLM/agent risks.

## Adapter contract

`ResearchAdapter.fetch(uri)` returns:

- normalized source metadata
- content
- content hash
- security warnings

The adapter itself has no authority to spend money, modify production, deploy code, change governance, or access secrets.

## V1 implementation

`StaticResearchAdapter` is deliberately deterministic and offline. It provides a safe test boundary before production network adapters are connected.

Production adapters must additionally enforce TLS validation, redirects policy, content-size/time limits, MIME validation, sandboxed parsing, SSRF protections, secret isolation, logging and rate limits.
