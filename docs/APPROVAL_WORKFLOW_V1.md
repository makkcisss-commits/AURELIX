# AURELIX Approval Workflow V1

The Control Center now has a workflow boundary around the existing `OwnerApproval` domain. The domain remains the source of truth for whether an approval is valid.

```text
Agent / Research / Business
          ↓
   DecisionRequest
          ↓
 ApprovalWorkflow.submit
          ↓
       PENDING
          ↓
     OWNER DECISION
       ↙       ↘
   REJECT      APPROVE
                ↓
        OwnerApproval scope
        request + amount + expiry
                ↓
       apply_owner_approval
                ↓
          APPROVED/REJECTED
                ↓
             AUDIT
```

A request that exceeds the approved amount, has the wrong request ID, or has expired cannot become approved. Rejected requests remain visible in the pending workflow when the scoped approval itself fails, so the owner can see that the attempted authorization did not satisfy the Governor boundary.

No payment, external side effect, or production mutation is performed by this workflow. A future execution gate must consume an approved decision and re-check authorization immediately before any side effect.
