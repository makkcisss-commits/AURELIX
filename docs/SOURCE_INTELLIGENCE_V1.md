# AURELIX Source Intelligence V1

Source Intelligence ranks evidence without pretending that a numerical score proves truth.

## Dimensions

- authority: an estimate of publisher/source authority for the research domain
- freshness: relevance of the source's age to the question
- independence_group: groups sources that may derive from the same publisher or underlying report
- provenance: URI, publisher, source type, publication and retrieval timestamps

## Principle

A high score is a prioritization signal, not a truth guarantee.

Independent corroboration matters more than repeatedly finding the same claim copied across mirrors.

```text
SOURCE
  ↓
PROFILE
  ├── authority
  ├── freshness
  ├── provenance
  └── independence
  ↓
PRIORITIZE
  ↓
EVIDENCE ENGINE
  ↓
SUPPORTED / CONFLICTED / INCONCLUSIVE / UNVERIFIED
```

Future versions should add domain-specific authority models, canonical-document detection, duplicate-content fingerprints, claim-level freshness, citation-graph analysis and human review for high-impact findings.
