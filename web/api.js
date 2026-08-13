(() => {
  const DEFAULT_BASE = '/';

  function baseUrl() {
    const configured = window.AURELIX_API_BASE;
    return (configured || DEFAULT_BASE).replace(/\/$/, '');
  }

  function headers(secret, json = false) {
    return {
      ...(json ? { 'Content-Type': 'application/json' } : {}),
      ...(secret ? { 'X-AURELIX-SECRET': secret } : {})
    };
  }

  async function request(path, secret, options = {}) {
    const response = await fetch(`${baseUrl()}${path}`, {
      credentials: 'include',
      cache: 'no-store',
      ...options,
      headers: { ...headers(secret, Boolean(options.body)), ...(options.headers || {}) }
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || body.error || `request_failed:${response.status}`);
    }
    return body;
  }

  const getSnapshot = (secret) => request('/v1/control/snapshot', secret);
  const getExperiments = (secret, status) => request(`/v1/control/experiments${status ? `?status=${encodeURIComponent(status)}` : ''}`, secret);
  const getKnowledge = (secret, query = '', limit = 20) => request(`/v1/control/knowledge?q=${encodeURIComponent(query)}&limit=${limit}`, secret);
  const getAudit = (secret, limit = 50) => request(`/v1/control/audit?limit=${limit}`, secret);
  const research = (secret, query) => request('/v1/actions/research', secret, {
    method: 'POST',
    body: JSON.stringify({ query })
  });
  const executeExperiment = (secret, experimentId, observations = []) => request(
    `/v1/actions/experiments/${encodeURIComponent(experimentId)}/execute`,
    secret,
    { method: 'POST', body: JSON.stringify({ observations }) }
  );

  window.AURELIX_API = { getSnapshot, getExperiments, getKnowledge, getAudit, research, executeExperiment };
})();
