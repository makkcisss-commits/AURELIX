(() => {
  const state = {};
  const byId = (id) => document.getElementById(id);
  const setText = (id, value) => {
    const node = byId(id);
    if (node) node.textContent = value == null ? '—' : String(value);
  };

  function renderActivity(events) {
    const node = byId('activity');
    if (!node) return;
    node.replaceChildren();
    const items = Array.isArray(events) ? events.slice(0, 8) : [];
    if (!items.length) {
      const empty = document.createElement('li');
      empty.textContent = 'No audit events recorded yet.';
      node.appendChild(empty);
      return;
    }
    for (const event of items) {
      const item = document.createElement('li');
      const type = event.event_type || event.type || 'audit.event';
      const outcome = event.outcome || 'recorded';
      item.textContent = `${type} — ${outcome}`;
      node.appendChild(item);
    }
  }

  function apply(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return;
    Object.assign(state, snapshot);
    for (const id of ['system', 'governor', 'policy', 'audit', 'api', 'execution', 'budget', 'breaker']) {
      setText(`${id}-state`, snapshot[id]);
    }

    const experiments = snapshot.experiments || {};
    const knowledge = snapshot.knowledge || {};
    setText('experiment-total', experiments.total ?? 0);
    setText('experiment-active', experiments.active ?? 0);
    setText('experiment-completed', experiments.completed ?? 0);
    setText('knowledge-total', knowledge.total_items ?? 0);
    setText('knowledge-backend', snapshot.providers?.knowledge_backend || 'unknown');
    setText('model-provider', snapshot.providers?.model_configured ? 'CONFIGURED' : 'NOT CONFIGURED');
    setText('research-provider', snapshot.providers?.research_configured ? 'CONFIGURED' : 'NOT CONFIGURED');
    renderActivity(snapshot.audit_events);
  }

  async function refresh(secret) {
    const snapshot = await window.AURELIX_API.getSnapshot(secret);
    apply(snapshot);
    return snapshot;
  }

  function storedSecret() {
    return window.sessionStorage.getItem('AURELIX_OWNER_SECRET') || '';
  }

  async function connect(secret) {
    const value = (secret || '').trim();
    if (!value) throw new Error('owner_secret_required');
    await refresh(value);
    window.sessionStorage.setItem('AURELIX_OWNER_SECRET', value);
    const input = byId('owner-secret');
    if (input) input.value = '';
    setText('connection-state', 'CONNECTED');
    const result = byId('research-result');
    if (result) result.textContent = 'Connected. The intelligence pipeline is ready.';
  }

  async function runResearch() {
    const secret = storedSecret();
    const query = (byId('research-query')?.value || '').trim();
    if (!secret) throw new Error('authentication_required');
    if (!query) throw new Error('research_query_required');
    const result = byId('research-result');
    if (result) result.textContent = 'Running governed intelligence pipeline…';
    const payload = await window.AURELIX_API.research(secret, query);
    if (result) {
      result.textContent = JSON.stringify({
        query: payload.query,
        evidence_count: payload.evidence_count,
        knowledge_ids: payload.knowledge_ids,
        experiment: payload.experiment,
        evaluation: payload.evaluation,
        opportunity: payload.opportunity,
        business: payload.business
      }, null, 2);
    }
    await refresh(secret);
  }

  function showError(error) {
    setText('connection-state', `ERROR: ${error.message || error}`);
    const result = byId('research-result');
    if (result) result.textContent = `ERROR: ${error.message || error}`;
  }

  window.AURELIX_UI = { apply, refresh, connect, runResearch, snapshot: () => ({ ...state }) };

  document.addEventListener('DOMContentLoaded', async () => {
    const form = byId('access-form');
    if (form) {
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
          await connect(byId('owner-secret')?.value || '');
        } catch (error) {
          showError(error);
        }
      });
    }

    const researchForm = byId('research-form');
    if (researchForm) {
      researchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
          await runResearch();
        } catch (error) {
          showError(error);
        }
      });
    }

    const secret = storedSecret();
    if (secret) {
      try {
        await refresh(secret);
        setText('connection-state', 'CONNECTED');
      } catch (error) {
        window.sessionStorage.removeItem('AURELIX_OWNER_SECRET');
        showError(error);
      }
    } else {
      setText('connection-state', 'AUTHENTICATION REQUIRED');
    }
  });
})();
