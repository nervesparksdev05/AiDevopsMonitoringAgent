import { useState, useEffect, useMemo } from "react";
import { api } from "../services/api";
import { formatTime, formatDate } from "../utils/time";

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [severity, setSeverity] = useState("");

  useEffect(() => {
    fetchAnomalies(true);
    const interval = setInterval(() => fetchAnomalies(false), 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnomalies = async (initial = false) => {
    try {
      if (initial) setLoading(true);
      else setRefreshing(true);

      const anomaliesData = await api.getAnomalies();
      
      setAnomalies(anomaliesData?.anomalies || []);
      setError(null);
    } catch (err) {
      setError(err?.message || "Failed to load anomalies");
      console.error("Anomalies fetch error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const filtered = useMemo(() => {
    if (!severity) return anomalies;
    return anomalies.filter(
      (a) => (a?.severity || "medium").toLowerCase() === severity
    );
  }, [anomalies, severity]);

  const counts = useMemo(() => {
    const c = { critical: 0, high: 0, medium: 0, low: 0, total: anomalies.length };
    for (const a of anomalies) {
      const s = (a?.severity || "medium").toLowerCase();
      if (c[s] !== undefined) c[s] += 1;
      else c.medium += 1;
    }
    return c;
  }, [anomalies]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-200 border-t-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-blue-100 rounded-xl p-6">
        <p className="text-blue-700 font-semibold mb-1">Failed to load anomalies</p>
        <p className="text-sm text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => fetchAnomalies(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-blue-100 rounded-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Anomalies</h2>
            <p className="text-sm text-gray-600 mt-1">
              AI-detected anomalies and RCA hints
            </p>
          </div>

          <button
            onClick={() => fetchAnomalies(false)}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {/* Filter + count */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              Severity
            </label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="w-full bg-white border border-blue-200 text-gray-900 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All ({counts.total})</option>
              <option value="critical">Critical ({counts.critical})</option>
              <option value="high">High ({counts.high})</option>
              <option value="medium">Medium ({counts.medium})</option>
              <option value="low">Low ({counts.low})</option>
            </select>
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600">Showing</p>
              <p className="text-3xl font-bold text-blue-700">{filtered.length}</p>
              <p className="text-xs text-gray-600">anomalies</p>
            </div>
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
          </div>
        </div>
      </div>

      {/* Empty state */}
      {filtered.length === 0 ? (
        <div className="bg-white border border-blue-100 rounded-xl p-10 text-center">
          <p className="text-gray-900 font-semibold">
            {severity ? "No anomalies match this severity." : "No anomalies detected."}
          </p>
          <p className="text-sm text-gray-600 mt-2">
            {severity ? "Try another filter." : "Everything looks stable right now."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((a, idx) => (
            <AnomalyCard key={a?._id || idx} anomaly={a} />
          ))}
        </div>
      )}

      {/* Footer */}
      {anomalies.length > 0 && (
        <div className="text-center text-xs text-gray-500">
          Auto-refresh every 10 seconds
        </div>
      )}
    </div>
  );
}

function AnomalyCard({ anomaly }) {
  const severity = (anomaly?.severity || "medium").toLowerCase();
  const pill = severityPill(severity);

  const metric = anomaly?.metric || "Unknown Metric";
  const instance = anomaly?.instance;
  const symptom = anomaly?.symptom || anomaly?.reason || "Anomalous behavior detected";

  const observed =
    anomaly?.observed !== undefined
      ? anomaly.observed
      : anomaly?.value !== undefined
      ? anomaly.value
      : null;

  const observedText =
    typeof observed === "number"
      ? observed.toFixed(2)
      : observed !== null
      ? String(observed)
      : "N/A";

  const expectedText = anomaly?.expected || "Normal baseline";

  const ts = anomaly?.timestamp ? new Date(anomaly.timestamp) : null;
  const timeText = ts ? formatTime(ts) : "—";
  const dateText = ts ? formatDate(ts) : "";

  const handleViewGrafana = async () => {
    if (!instance) {
      alert('No instance information available for this anomaly');
      return;
    }
    try {
      const { grafana_url } = await api.getGrafanaUrl(instance);
      window.open(grafana_url, '_blank');
    } catch (error) {
      console.error('Failed to get Grafana URL:', error);
      alert('Failed to open Grafana. Make sure Grafana is running.');
    }
  };

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${pill}`}>
              {severity.toUpperCase()}
            </span>
            <h3 className="font-semibold text-gray-900 truncate">{metric}</h3>
          </div>

          {instance ? (
            <p className="text-xs text-gray-600 mt-2">
              <span className="font-semibold text-gray-700">Instance:</span>{" "}
              <span className="break-all">{instance}</span>
            </p>
          ) : null}

          <p className="text-sm text-gray-800 mt-3 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
            {symptom}
          </p>
        </div>

        <div className="text-right shrink-0">
          <p className="text-xs text-gray-500">Detected</p>
          <p className="text-sm font-semibold text-gray-900">{timeText}</p>
          {dateText ? <p className="text-xs text-gray-500">{dateText}</p> : null}
          {instance && (
            <button
              onClick={handleViewGrafana}
              className="mt-2 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded hover:bg-blue-700 transition-colors"
            >
              📊 Grafana
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="border border-blue-100 rounded-xl p-4">
          <p className="text-xs text-gray-600">Observed</p>
          <p className="text-2xl font-bold text-blue-700 mt-1">{observedText}</p>
        </div>

        <div className="border border-blue-100 rounded-xl p-4">
          <p className="text-xs text-gray-600">Expected</p>
          <p className="text-sm font-semibold text-gray-900 mt-1">{expectedText}</p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-blue-100 text-xs text-gray-500 flex flex-wrap gap-x-4 gap-y-1">
        {anomaly?._id ? <span>ID: {String(anomaly._id).slice(0, 8)}…</span> : null}
        {anomaly?.batch_id ? (
          <span>Batch: {String(anomaly.batch_id).slice(0, 8)}…</span>
        ) : null}
        {anomaly?.incident_id ? (
          <span>Incident: {String(anomaly.incident_id).slice(0, 8)}…</span>
        ) : null}
      </div>
    </div>
  );
}

function severityPill(sev) {
  // Blue + white only (no red/orange/yellow)
  // Higher severity = stronger blue
  const map = {
    critical: "bg-blue-50 text-blue-800 border-blue-300",
    high: "bg-blue-50 text-blue-700 border-blue-200",
    medium: "bg-white text-blue-700 border-blue-200",
    low: "bg-white text-blue-600 border-blue-100",
  };
  return map[sev] || map.medium;
}
