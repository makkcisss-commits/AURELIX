# AURELIX Architecture

AURELIX is a private venture intelligence platform composed of a governance core, specialized engines, agents, data/state services, and controlled external interfaces.

```text
Owner / CEO
    |
    v
Governor
    |
    +-- Research Engine
    +-- Academy Engine
    +-- Opportunity Engine
    +-- Innovation Engine
    +-- Build Engine
    +-- Business Engine
    +-- Revenue Engine
    +-- Learning Engine
    |
    +-- Treasury / Approval Layer
    +-- Security / Audit Layer
    +-- Sandbox / Experiment Layer
```

## Design rules
1. Governance is centralized; execution is modular.
2. Engines communicate through explicit contracts rather than hidden shared state.
3. Protected actions pass through authorization gates.
4. Experiments are isolated from critical production state.
5. Every important decision should be explainable through inputs, policy, evidence, and outcome.
6. The web application and future mobile application are clients of the platform, not alternate authorities.

## Initial product boundary
The first implementation is an internal control plane. Public-facing products are future business outputs, not the administrative interface itself.
