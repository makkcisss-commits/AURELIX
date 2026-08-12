# AURELIX Research + Academy Architecture V1

Research agents are designed around the strongest recurring pattern in modern deep-research systems: plan the question, decompose it, retrieve from explicit sources, verify evidence, synthesize, and preserve citations/limitations. OpenAI's Deep Research documentation describes multi-step web research, source selection, progress/review, and citation-backed reports; its system card also identifies prompt injection, privacy, hallucination and tool-use risks. Independent surveys similarly describe planning, question development, web exploration and report generation as core stages.

## AURELIX design

```text
Governor
   ↓
Research request
   ↓
PLAN
   ├── question
   ├── subquestions
   └── source policy
   ↓
RETRIEVE (tool adapters)
   ├── web search
   ├── documents/PDFs
   ├── approved APIs
   └── internal sources
   ↓
VERIFY
   ├── source identity
   ├── publication/retrieval metadata
   ├── cross-source comparison
   └── uncertainty / caveats
   ↓
SYNTHESIZE
   ↓
REPORT + FINDINGS
   ↓
Opportunity / Learning / Academy
```

## Evidence rules

1. A claim must reference a stored source.
2. A model-generated statement is not itself a source.
3. Confidence is explicit.
4. Limitations are retained rather than hidden.
5. Source policy can restrict domains or source classes.
6. Retrieval and execution are separate capabilities.
7. Untrusted web content is treated as data, not instructions to the agent.

## Academy loop

```text
Research findings
      ↓
Experiment results
      ↓
Learning
      ↓
Academy Agent
      ↓
Traceable knowledge
      ↓
Innovation / future research
```

The Academy Agent cannot authorize spending, production changes, deployments, or external commitments.

## Agent boundaries

The LLM is an orchestrator/reasoner. Deterministic code owns identity, source references, scopes, validation and state transitions. Tool adapters own retrieval. The Governor owns policy routing. Owner approval remains mandatory for capital and critical production changes.

This architecture intentionally does not attempt to reproduce a proprietary model or service. It reproduces the useful architectural pattern while keeping AURELIX's governance and evidence model explicit.
