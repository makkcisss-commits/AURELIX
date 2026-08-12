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
  }

  function showError(error) {
    setText('connection-state', `ERROR: ${error.message || error}`);
  }

  window.AURELIX_UI = { apply, refresh, connect, snapshot: () => ({ ...state }) };

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
