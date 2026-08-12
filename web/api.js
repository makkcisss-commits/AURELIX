(() => {
  const DEFAULT_BASE = '/';

  function baseUrl() {
    const configured = window.AURELIX_API_BASE;
    return (configured || DEFAULT_BASE).replace(/\/$/, '');
  }

  async function getSnapshot(secret) {
    const response = await fetch(`${baseUrl()}/v1/control/snapshot`, {
      method: 'GET',
      credentials: 'include',
      headers: secret ? { 'X-AURELIX-SECRET': secret } : {},
      cache: 'no-store'
    });

    if (!response.ok) {
      throw new Error(`snapshot_request_failed:${response.status}`);
    }

    return response.json();
  }

  window.AURELIX_API = { getSnapshot };
})();
