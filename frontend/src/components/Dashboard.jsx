import { useState, useEffect } from "react";
import { api } from "../services/api";

/**
 * Dashboard (Blue + White)
 * Update: left side made simpler (no long Prometheus/LLM/Langfuse lines)
 * - Left: title + small status lines only
 * - Right: status pill
 */
export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const [statsData, healthData] = await Promise.all([
        api.getStats(),
        api.getHealth(),
      ]);
      setStats(statsData);
      setHealth(healthData);
      setError(null);
    } catch (err) {
      setError(err?.message || "Failed to connect");
      console.error("Dashboard error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-200 border-t-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-blue-100 rounded-xl p-4">
        <p className="text-blue-700 font-medium mb-2">Connection error</p>
        <p className="text-sm text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const metricsTotal = stats?.collections?.metrics_batches?.total ?? 0;
  const anomaliesTotal = stats?.collections?.anomalies?.total ?? 0;
  const openIssues = stats?.collections?.anomalies?.open ?? 0;
  const rcaDone = stats?.collections?.anomalies?.analyzed ?? 0;

  const emailEnabled = !!stats?.notifications?.email?.enabled;
  const slackEnabled =
    !!stats?.notifications?.slack?.enabled &&
    !!stats?.notifications?.slack?.configured;

  const systemOnline = health?.status === "running";

  // Simple left-side summary lines
  const line1 = systemOnline ? "" : "Some checks need attention.";
  const line2 =
    (health?.current_time || health?.timezone)
      ? `${health?.current_time ? `Time: ${health.current_time}` : ""}${
          health?.current_time && health?.timezone ? " • " : ""
        }${health?.timezone ? `TZ: ${health.timezone}` : ""}`
      : null;

  return (
    <div className="space-y-6">
      {/* Header (Simplified Left Side) */}
      <div className="bg-white border border-blue-100 rounded-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {systemOnline ? "AiDevopsMonitoringDashboard" : "System Status"}
            </h2>
            <p className="text-sm text-gray-600 mt-1">{line1}</p>
            {line2 ? <p className="text-xs text-gray-500 mt-2">{line2}</p> : null}
          </div>

          <div className="flex items-center gap-3">
            <a
              href="http://localhost:3001/d/server-monitoring"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              📊 View Live Metrics
            </a>
            <StatusPill ok={systemOnline} />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Metric Batches" value={metricsTotal} />
        <StatCard title="Total Anomalies" value={anomaliesTotal} />
        <StatCard title="Open Issues" value={openIssues} />
        <StatCard title="RCA Complete" value={rcaDone} />
      </div>

      {/* Notifications */}
      <div className="bg-white border border-blue-100 rounded-xl p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Notifications
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <SimpleRow
            label="Email Alerts"
            value={emailEnabled ? "Active" : "Inactive"}
            ok={emailEnabled}
            sub={
              emailEnabled
                ? `${stats?.notifications?.email?.recipients ?? 0} recipient(s)`
                : null
            }
          />
          <SimpleRow
            label="Slack Alerts"
            value={slackEnabled ? "Active" : "Inactive"}
            ok={slackEnabled}
            sub={slackEnabled ? "Webhook configured" : null}
          />
        </div>
      </div>

      {/* Components */}
      <div className="bg-white border border-blue-100 rounded-xl p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Components
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <HealthIndicator label="API Server" ok />
          <HealthIndicator label="MongoDB" ok={!!stats?.collections} />
          <HealthIndicator label="Prometheus" ok={!!health?.prometheus} />
          <HealthIndicator label="LLM Service" ok={!!health?.llm} />
        </div>
      </div>
    </div>
  );
}

function StatusPill({ ok }) {
  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${
        ok
          ? "bg-blue-50 border-blue-200 text-blue-700"
          : "bg-white border-blue-200 text-blue-700"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          ok ? "bg-blue-600 animate-pulse" : "bg-blue-300"
        }`}
      />
      <span className="text-sm font-semibold">{ok ? "Online" : "Check"}</span>
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5">
      <p className="text-sm text-gray-600">{title}</p>
      <p className="text-3xl font-bold text-blue-700 mt-2">{value}</p>
    </div>
  );
}

function SimpleRow({ label, value, ok, sub }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-xl border border-blue-100 bg-white">
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {sub ? <p className="text-xs text-gray-500 mt-1">{sub}</p> : null}
      </div>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${ok ? "bg-blue-600" : "bg-blue-200"}`} />
        <span className="text-sm font-semibold text-blue-700">{value}</span>
      </div>
    </div>
  );
}

function HealthIndicator({ label, ok }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-xl border border-blue-100 bg-white">
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            ok ? "bg-blue-600 animate-pulse" : "bg-blue-200"
          }`}
        />
        <span className="text-sm font-medium text-gray-800">{label}</span>
      </div>
      <span className="text-xs font-semibold text-blue-700">
        {ok ? "Healthy" : "Warning"}
      </span>
    </div>
  );
}
