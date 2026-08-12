(() => {
  const state = {
    system: 'HEALTHY',
    governor: 'OPERATIONAL',
    policy: 'ACTIVE',
    audit: 'RECORDING',
    api: 'PROTECTED',
    execution: 'GUARDED',
    budget: 'ACTIVE',
    breaker: 'READY'
  };

  const byId = (id) => document.getElementById(id);
  const setText = (id, value) => { const node = byId(id); if (node) node.textContent = value; };

  window.AURELIX_UI = {
    apply(snapshot) {
      if (!snapshot || typeof snapshot !== 'object') return;
      Object.assign(state, snapshot);
      setText('system-state', state.system);
      setText('governor-state', state.governor);
      setText('policy-state', state.policy);
      setText('audit-state', state.audit);
      setText('api-state', state.api);
      setText('execution-state', state.execution);
      setText('budget-state', state.budget);
      setText('breaker-state', state.breaker);
    },
    snapshot() { return { ...state }; }
  };
})();
