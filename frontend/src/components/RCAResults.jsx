import { useState, useEffect} from "react";
import { api } from "../services/api";
import { formatDateTime } from "../utils/time";

export default function RCAResults() {
  const [rcaResults, setRcaResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const [chatOpen, setChatOpen] = useState(false);
  const [activeRca, setActiveRca] = useState(null);

  useEffect(() => {
    fetchRCA(true);
    const interval = setInterval(() => fetchRCA(false), 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchRCA = async (initial = false) => {
    try {
      if (initial) setLoading(true);
      else setRefreshing(true);

      const rcaData = await api.getRCA();
      
      setRcaResults(rcaData?.rca || []);
      setError(null);
    } catch (err) {
      setError(err?.message || "Failed to load RCA results");
      console.error("Error fetching RCA:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const openChat = (rca) => {
    setActiveRca(rca);
    setChatOpen(true);
  };

  const total = rcaResults.length;

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
        <p className="text-blue-700 font-semibold mb-1">Failed to load RCA results</p>
        <p className="text-sm text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => fetchRCA(true)}
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
            <h2 className="text-xl font-bold text-gray-900">RCA Results</h2>
            <p className="text-sm text-gray-600 mt-1">
              Root cause analysis and recommended actions
            </p>
          </div>

          <button
            onClick={() => fetchRCA(false)}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {/* IP Filter + count banner */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Removed IP Filter dropdown */}
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600">Total reports</p>
              <p className="text-3xl font-bold text-blue-700">{total}</p>
            </div>
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
          </div>
        </div>
      </div>

      {/* Empty */}
      {rcaResults.length === 0 ? (
        <div className="bg-white border border-blue-100 rounded-xl p-10 text-center">
          <p className="text-gray-900 font-semibold">No RCA results available</p>
          <p className="text-sm text-gray-600 mt-2">
            Reports will appear once anomalies are analyzed.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {rcaResults.map((rca, idx) => (
            <RcaCard key={rca?._id || idx} rca={rca} onAsk={() => openChat(rca)} />
          ))}
        </div>
      )}

      {rcaResults.length > 0 && (
        <div className="text-center text-xs text-gray-500">
          Auto-refresh every 15 seconds
        </div>
      )}

      {/* Chat Modal */}
      {chatOpen && activeRca && (
        <ChatModal rca={activeRca} onClose={() => setChatOpen(false)} />
      )}
    </div>
  );
}

/* ---------- RCA Card ---------- */

function RcaCard({ rca, onAsk }) {
  const metric = rca?.metric || "Batch Analysis";
  const instance = rca?.instance;

  const summary = rca?.summary;
  const cause = rca?.cause || "Analysis in progress...";
  const fix =
    Array.isArray(rca?.fix) ? rca.fix.join(", ") : rca?.fix || "Recommendations pending...";

  const ts = rca?.timestamp ? new Date(rca.timestamp) : null;
  const tsText = ts ? formatDateTime(ts) : "—";

  return (
    <div className="bg-white border border-blue-100 rounded-xl p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-bold border bg-blue-50 text-blue-800 border-blue-200">
              RCA
            </span>
            <h3 className="font-semibold text-gray-900 truncate">{metric}</h3>
          </div>

          {instance ? (
            <p className="text-xs text-gray-600 mt-2">
              <span className="font-semibold text-gray-700">Instance:</span>{" "}
              <span className="break-all">{instance}</span>
            </p>
          ) : null}

          {summary ? (
            <p className="text-sm text-gray-800 mt-3 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
              {summary}
            </p>
          ) : null}
        </div>

        <button
          onClick={onAsk}
          className="px-3 py-2 rounded-lg border border-blue-200 text-blue-700 hover:bg-blue-50 text-sm font-semibold"
        >
          Ask AI
        </button>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="border border-blue-100 rounded-xl p-4">
          <p className="text-xs text-gray-600">Root cause</p>
          <p className="text-sm font-medium text-gray-900 mt-1 whitespace-pre-wrap">{cause}</p>
        </div>

        <div className="border border-blue-100 rounded-xl p-4">
          <p className="text-xs text-gray-600">Recommended action</p>
          <p className="text-sm font-medium text-gray-900 mt-1 whitespace-pre-wrap">{fix}</p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-blue-100 text-xs text-gray-500 flex flex-wrap gap-x-4 gap-y-1">
        {rca?._id ? <span>RCA: {String(rca._id).slice(0, 8)}…</span> : null}
        {rca?.anomaly_id ? <span>Anomaly: {String(rca.anomaly_id).slice(0, 8)}…</span> : null}
        <span>{tsText}</span>
      </div>
    </div>
  );
}

/* ---------- Chat Modal (Blue + White) ---------- */

function ChatModal({ rca, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: `Hi! I analyzed the ${rca?.metric || "anomaly"} RCA. What do you want to understand?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    const el = document.getElementById("chat-box");
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInput("");
    setSending(true);

    try {
      const context = {
        metric: rca?.metric,
        instance: rca?.instance,
        cause: rca?.cause,
        fix: rca?.fix,
        summary: rca?.summary,
        ...(rca?.simplified ? { simplified: rca.simplified } : {}),
      };

      const res = await api.chat({
        message: userMsg,
        context,
        session_id: sessionId,
      });

      if (res?.session_id) setSessionId(res.session_id);

      setMessages((prev) => [
        ...prev,
        { role: "ai", text: res?.response || "No response received." },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "Sorry — something went wrong. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white border border-blue-100 rounded-xl shadow-xl w-full max-w-lg flex flex-col max-h-[80vh]">
        <div className="p-4 border-b border-blue-100 flex justify-between items-center">
          <div>
            <h3 className="font-bold text-gray-900">AI Assistant</h3>
            <p className="text-xs text-gray-600 truncate max-w-[22rem]">
              {rca?.metric ? `Discussing: ${rca.metric}` : "Discussing RCA"}
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg border border-blue-100 text-gray-600 hover:bg-blue-50"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div id="chat-box" className="flex-1 overflow-y-auto p-4 space-y-3 bg-white">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-xl p-3 text-sm whitespace-pre-wrap border ${
                  m.role === "user"
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-900 border-blue-100"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-3 text-xs text-gray-600">
                Thinking…
              </div>
            </div>
          )}
        </div>

        <form onSubmit={send} className="p-4 border-t border-blue-100 bg-white">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about the RCA..."
              className="flex-1 border border-blue-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={sending}
              autoFocus
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
