const API_BASE = window.AURELIX_API_BASE || "/api";

function setState(id, label, healthy = true) {
  const node = document.getElementById(id);
  node.textContent = `${healthy ? "●" : "•"} ${label}`;
  node.className = `status ${healthy ? "status--healthy" : "status--pending"}`;
}

function setMetric(id, label, healthy = true) {
  const node = document.getElementById(id);
  node.textContent = label;
  node.style.color = healthy ? "var(--green)" : "var(--amber)";
}

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json();
}

async function refresh() {
  try {
    const health = await getJson("/health");
    setState("system-state", health.status === "ok" ? "HEALTHY" : "ATTENTION", health.status === "ok");
    setState("governor-state", "OPERATIONAL", true);
    setMetric("policy-state", "ACTIVE");
    setMetric("audit-state", "RECORDING");
    setMetric("api-state", "PROTECTED");
    setMetric("execution-state", "GUARDED");
    const activity = document.getElementById("activity");
    activity.innerHTML = "<li>Private API connected</li><li>Governor control boundary active</li><li>Audit channel available</li>";
  } catch (error) {
    setState("system-state", "ATTENTION", false);
    setState("governor-state", "UNAVAILABLE", false);
    setMetric("policy-state", "UNKNOWN", false);
    setMetric("audit-state", "UNKNOWN", false);
    setMetric("api-state", "OFFLINE", false);
    setMetric("execution-state", "LOCKED", false);
    document.getElementById("activity").innerHTML = "<li>Private API unavailable — no protected action is attempted</li>";
  }
}

refresh();
setInterval(refresh, 30000);
