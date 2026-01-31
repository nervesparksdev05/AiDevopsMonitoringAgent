/**
 * API Service
 * Fetch ALL database data (auto-pagination)
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// You can override these from .env if needed:
const DEFAULT_PAGE_SIZE = Number(import.meta.env.VITE_PAGE_SIZE || 500);
const MAX_PAGES = Number(import.meta.env.VITE_MAX_PAGES || 500); // safety cap

async function fetchJson(url, opts = {}) {
  // Add Authorization header if token exists
  const token = localStorage.getItem('token');
  const headers = {
    ...opts.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...opts, headers });

  // Handle 401 Unauthorized - redirect to login
  if (res.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
    throw new Error('Unauthorized - please login');
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch all pages from an endpoint that supports:
 *   ?limit=<pageSize>&skip=<offset>
 * And returns either:
 *   { [key]: [...] }  OR  [...]
 */
async function fetchAllPages(endpoint, key, pageSize = DEFAULT_PAGE_SIZE) {
  const all = [];
  let skip = 0;

  // To prevent infinite loops when backend ignores skip/limit
  let lastFirstId = null;

  for (let page = 0; page < MAX_PAGES; page++) {
    const qs = new URLSearchParams({
      limit: String(pageSize),
      skip: String(skip),
    }).toString();

    const url = `${API_BASE_URL}/${endpoint}?${qs}`;
    const data = await fetchJson(url);

    const list = Array.isArray(data) ? data : data?.[key] || [];
    if (!Array.isArray(list) || list.length === 0) break;

    // Guard: if backend ignores pagination, it may return same page again
    const firstId = list?.[0]?._id ? String(list[0]._id) : null;
    if (firstId && firstId === lastFirstId) break;
    lastFirstId = firstId;

    all.push(...list);

    // If last page
    if (list.length < pageSize) break;

    skip += pageSize;
  }

  return all;
}

export const api = {
  // ============ HEALTH & STATS ============

  async getHealth() {
    return fetchJson(`${API_BASE_URL}/health`);
  },

  async getStats() {
    return fetchJson(`${API_BASE_URL}/stats`);
  },

  // ============ DATA ENDPOINTS ============

  async getPromMetrics() {
    return fetchJson(`${API_BASE_URL}/prom-metrics`);
  },

  // ✅ Updated: fetch ALL anomalies
  async getAnomalies() {
    const anomalies = await fetchAllPages("anomalies", "anomalies");
    return { anomalies };
  },

  // ✅ Updated: fetch ALL RCA results
  async getRCA() {
    const rca = await fetchAllPages("rca", "rca");
    return { rca };
  },

  // ============ CHAT ENDPOINT ============

  async chat(payload) {
    return fetchJson(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  // ============ SESSION MANAGEMENT ============

  async getSessions() {
    return fetchJson(`${API_BASE_URL}/api/sessions`);
  },

  async getSessionDetails(sessionId) {
    return fetchJson(`${API_BASE_URL}/api/sessions/${sessionId}`);
  },

  async deleteSession(sessionId) {
    return fetchJson(`${API_BASE_URL}/api/sessions/${sessionId}`, {
      method: "DELETE",
    });
  },

  // ============ EMAIL CONFIGURATION ============

  async getEmailConfig() {
    return fetchJson(`${API_BASE_URL}/agent/email-config`);
  },

  async updateEmailConfig(config) {
    return fetchJson(`${API_BASE_URL}/agent/email-config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
  },

  async sendTestEmail() {
    return fetchJson(`${API_BASE_URL}/agent/test-email`, { method: "POST" });
  },

  // ============ SLACK (ENV ONLY) ============

  async getSlackStatus() {
    return fetchJson(`${API_BASE_URL}/agent/slack-status`);
  },

  async sendTestSlack() {
    return fetchJson(`${API_BASE_URL}/agent/test-slack`, { method: "POST" });
  },

  // ============ SERVER / TARGET MANAGEMENT ============

  async getTargets() {
    return fetchJson(`${API_BASE_URL}/agent/targets`);
  },

  async addTarget(target) {
    return fetchJson(`${API_BASE_URL}/agent/targets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(target),
    });
  },

  async removeTarget(endpoint) {
    return fetchJson(
      `${API_BASE_URL}/agent/targets/${encodeURIComponent(endpoint)}`,
      { method: "DELETE" }
    );
  },

  // ============ SLACK CONFIGURATION ============

  async getSlackConfig() {
    return fetchJson(`${API_BASE_URL}/agent/slack-config`);
  },

  async updateSlackConfig(config) {
    return fetchJson(`${API_BASE_URL}/agent/slack-config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
  },

  // ============ LANGFUSE STATUS ============

  async getLangfuseStatus() {
    return fetchJson(`${API_BASE_URL}/langfuse/status`);
  },

  // ============ IP-FILTERED DATA ============
  // These endpoints remain for internal data filtering

  async getMetricsByIP(ip) {
    const metrics = await fetchAllPages(`metrics/by-ip?ip=${encodeURIComponent(ip)}`, "metrics");
    return { metrics };
  },

  async getAnomaliesByIP(ip) {
    const anomalies = await fetchAllPages(`anomalies/by-ip?ip=${encodeURIComponent(ip)}`, "anomalies");
    return { anomalies };
  },

  async getIncidentsByIP(ip) {
    const incidents = await fetchAllPages(`incidents/by-ip?ip=${encodeURIComponent(ip)}`, "incidents");
    return { incidents };
  },

  async getRCAByIP(ip) {
    const rca = await fetchAllPages(`rca/by-ip?ip=${encodeURIComponent(ip)}`, "rca");
    return { rca };
  },

  async getBatchesByIP(ip) {
    const batches = await fetchAllPages(`batches/by-ip?ip=${encodeURIComponent(ip)}`, "batches");
    return { batches };
  },

  async getBatches() {
    const batches = await fetchAllPages("batches", "batches");
    return { batches };
  },

  async getIncidents() {
    const incidents = await fetchAllPages("incidents", "incidents");
    return { incidents };
  },
};
