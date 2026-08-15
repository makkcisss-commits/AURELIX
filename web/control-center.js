const API_BASE = (window.AURELIX_API_BASE || "").replace(/\/$/, "");

function setState(id, label, healthy = true) {
  const node = document.getElementById(id);
  node.textContent = `${healthy ? "●" : "•"} ${label}`;
  node.className = `status ${healthy ? "status--healthy" : "status--pending"}`;
}

function setMetric(id, label, healthy = false) {
  const node = document.getElementById(id);
  node.textContent = label;
  node.style.color = healthy ? "var(--green)" : "var(--amber)";
}

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json();
}

function resetProtectedState(label = "UNVERIFIED") {
  setState("governor-state", label, false);
  setMetric("policy-state", "UNVERIFIED");
  setMetric("audit-state", "UNVERIFIED");
  setMetric("api-state", "HEALTHY", true);
  setMetric("execution-state", "UNVERIFIED");
  document.getElementById("approval-count").textContent = "UNAVAILABLE";
  document.getElementById("budget-count").textContent = "UNAVAILABLE";
}

async function refresh() {
  const activity = document.getElementById("activity");
  try {
    const [health, readiness] = await Promise.all([
      getJson("/health"),
      getJson("/ready"),
    ]);

    const healthy = health.status === "ok";
    const ready = readiness.status === "ready";
    setState("system-state", ready ? "READY" : healthy ? "HEALTHY" : "ATTENTION", ready || healthy);
    resetProtectedState(ready ? "AUTHENTICATION REQUIRED" : "NOT READY");

    activity.innerHTML = "";
    const events = [
      `Liveness: ${healthy ? "OK" : "FAILED"}`,
      `Readiness: ${ready ? "READY" : "NOT READY"}`,
      "Protected control data: not exposed without owner authentication",
    ];
    for (const event of events) {
      const item = document.createElement("li");
      item.textContent = event;
      activity.appendChild(item);
    }
  } catch (error) {
    setState("system-state", "ATTENTION", false);
    resetProtectedState("UNAVAILABLE");
    document.getElementById("api-state").textContent = "OFFLINE";
    activity.textContent = "";
    const item = document.createElement("li");
    item.textContent = "Private API unavailable — no protected action is attempted";
    activity.appendChild(item);
  }
}

refresh();
setInterval(refresh, 30000);
