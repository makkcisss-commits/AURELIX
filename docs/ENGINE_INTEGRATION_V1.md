# AURELIX Engine Integration V1

The engineering loop now has typed, first-party runtime contracts for:

`Governor → Research → Academy → Knowledge → Innovation → Experiment → Evaluation → Opportunity → Business`

## Boundary

Engine adapters exchange an `EngineContext`. Evidence is provenance-bearing data; proposals are not permissions. An adapter cannot grant itself tools, credentials, budget, or production access.

## Safety defaults

- Business is proposal-only by default.
- Experiments declare sandbox requirements and do not execute arbitrary code through this adapter layer.
- External research providers must be connected behind explicit tool policies.
- External content is data, not system instructions.
- Approval and authorization remain outside the model/adapter output.

## Next integration layer

Connect real provider clients (search, model inference, storage) behind the existing Execution Plane and persist each context transition as an auditable event. Provider credentials must remain outside prompts and engine-generated content.
