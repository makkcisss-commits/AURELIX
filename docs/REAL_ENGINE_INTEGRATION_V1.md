# AURELIX — Real Engine Integration V1

AURELIX now defines executable, provider-agnostic implementations for the complete intelligence-to-business chain:

`Governor → Research → Academy → Knowledge → Innovation → Experiment → Evaluation → Opportunity → Business`

## Engine responsibilities

- **Governor:** policy, priorities, permissions and approval boundaries.
- **Research:** obtains evidence through an explicit provider adapter.
- **Academy:** converts verified evidence into lessons and identifies gaps.
- **Knowledge:** persists institutional learning through the storage boundary.
- **Innovation:** generates proposals from knowledge; proposals are not permissions.
- **Experiment:** creates bounded experiments with explicit success criteria.
- **Evaluation:** records measured outcomes and refuses to claim success without evidence.
- **Opportunity:** turns evaluated information into economic candidates with risk/confidence fields.
- **Business:** remains approval-gated and cannot execute financial/production actions merely because a model requested them.

## Production adapter rule

External search, model, payment, deployment, and communication providers must be implemented as explicit adapters behind the Execution Plane. Secrets must never be embedded in prompts, source files, or engine state.

## Autonomy boundary

AURELIX may autonomously research, learn, store knowledge, propose innovations, and prepare experiments. High-impact business, financial, security, and production actions remain policy/approval controlled.

## Completion criterion

The system is considered operational only when these engines are connected to durable persistence, the worker supervisor, policy enforcement, audit, health checks, and real provider adapters, and when integration tests verify the full lifecycle after restart/failure.
