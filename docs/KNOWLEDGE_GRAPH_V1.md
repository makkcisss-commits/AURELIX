# AURELIX Knowledge Graph V1

The Academy memory is a graph, not a pile of generated notes.

## Nodes

- SOURCE
- CLAIM
- FINDING
- CONCEPT
- EXPERIMENT
- LESSON
- OPPORTUNITY

## Relations

- SUPPORTS
- CONTRADICTS
- DERIVED_FROM
- RELATES_TO
- TESTED_BY
- LEADS_TO
- LEARNED_FROM

Example:

```text
SOURCE
  │ SUPPORTS
  ▼
CLAIM
  │ DERIVED_FROM
  ▼
FINDING
  │ TESTED_BY
  ▼
EXPERIMENT
  │ LEADS_TO
  ▼
LESSON
  │ RELATES_TO
  ▼
OPPORTUNITY
```

## Governance

The graph is an evidence and learning memory. It does not grant execution authority. External content cannot create privileged instructions, change Governor policy, spend capital, deploy production code, or alter security controls merely by being stored in the graph.

Future versions should add persistence, provenance hashes, versioned edges, contradiction resolution workflows, retention rules, search/indexing, and human review for high-impact knowledge.
