import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function RCAResults() {
  const [rcaResults, setRcaResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [activeRca, setActiveRca] = useState(null);

  useEffect(() => {
    fetchRCA();
    const interval = setInterval(fetchRCA, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchRCA = async () => {
    try {
      if (rcaResults.length === 0) {
        setLoading(true);
      }
      const data = await api.getRCA();
      setRcaResults(data.rca || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching RCA:', err);
    } finally {
      setLoading(false);
    }
  };

  const openChat = (rca) => {
    setActiveRca(rca);
    setChatOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">RCA Results</h2>
          <p className="text-gray-600">AI-powered root cause analysis and recommendations</p>
        </div>
        <button
          onClick={fetchRCA}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50"
        >
          <span>{loading ? '...' : '↻'}</span>
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Banner */}
      <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl p-6 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold mb-2">Total RCA Reports</h3>
            <p className="text-purple-100">AI-generated insights and recommendations</p>
          </div>
          <div className="text-6xl font-bold">{rcaResults.length}</div>
        </div>
      </div>

      {/* RCA List */}
      {loading && rcaResults.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600 mb-2">Error: {error}</p>
          <button 
            onClick={fetchRCA}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      ) : rcaResults.length === 0 ? (
        <div className="bg-white rounded-xl p-12 shadow-sm text-center border border-gray-200">
          <div className="text-6xl mb-4">#</div>
          <p className="text-gray-500 text-lg">No RCA results available</p>
          <p className="text-gray-400 text-sm mt-2">
            RCA reports will appear here once anomalies are analyzed
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {rcaResults.map((rca, idx) => (
            <div
              key={rca._id || idx}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-2xl">🔍</span>
                    <h3 className="text-xl font-bold text-gray-800">{rca.metric}</h3>
                  </div>
                  {rca.instance && (
                    <p className="text-sm text-gray-500 mb-2">Instance: {rca.instance}</p>
                  )}
                  {rca.summary && (
                    <p className="text-sm text-gray-600 bg-blue-50 px-3 py-2 rounded-lg inline-block border border-blue-200">
                      {rca.summary}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Analyzed</p>
                  <p className="text-sm font-medium text-gray-700">
                    {new Date(rca.timestamp).toLocaleString()}
                  </p>
                  <button
                    onClick={() => openChat(rca)}
                    className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center justify-end gap-1"
                  >
                    <span>💬</span> Ask AI
                  </button>
                </div>
              </div>

              {/* SIMPLIFIED EXPLANATION (New) */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-2xl">🎓</span>
                  <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">What does this mean? (Simple)</h4>
                </div>
                <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-4">
                  <p className="text-gray-800 leading-relaxed font-medium">
                    {rca.simplified || "AI is generating a simplified explanation..."}
                  </p>
                  {!rca.simplified && <p className="text-xs text-gray-500 mt-1">(Only available for new anomalies)</p>}
                </div>
              </div>

              {/* Root Cause */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-2xl">🔍</span>
                  <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Technical Root Cause</h4>
                </div>
                <div className="bg-purple-50 border-l-4 border-purple-500 rounded-lg p-4">
                  <p className="text-gray-800 leading-relaxed font-mono text-sm">{rca.cause || 'Analysis in progress...'}</p>
                </div>
              </div>

              {/* Recommended Action */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-2xl">💡</span>
                  <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Recommended Action</h4>
                </div>
                <div className="bg-green-50 border-l-4 border-green-500 rounded-lg p-4">
                  <p className="text-gray-800 font-medium leading-relaxed">{rca.fix || 'Recommendations pending...'}</p>
                </div>
              </div>

              {/* Metadata Footer */}
              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-4">
                    <span>RCA ID: {rca._id}</span>
                    {rca.anomaly_id && <span>Anomaly ID: {rca.anomaly_id}</span>}
                  </div>
                  <span>{new Date(rca.timestamp).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Chat Modal */}
      {chatOpen && activeRca && (
        <ChatModal 
          rca={activeRca} 
          onClose={() => setChatOpen(false)} 
        />
      )}
    </div>
  );
}

function ChatModal({ rca, onClose }) {
  const [messages, setMessages] = useState([
    { role: 'ai', text: `Hi! I analyzed the ${rca.metric} anomaly. How can I help you understand it better?` }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  // Scroll to bottom
  useEffect(() => {
    const el = document.getElementById('chat-box');
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setSending(true);

    try {
        // Construct context for the chat
        const context = {
            metric: rca.metric,
            value: rca.value, // Note: value might not be directly on RCA object depending on backend response, check main.py
            cause: rca.cause,
            fix: rca.fix,
            simplified: rca.simplified
        };
        
        // Use the existing chat endpoint
        const res = await api.chat({
            message: userMsg,
            context: {
                ...context,
                type: "rca_discussion" 
            }
        });
        
        setMessages(prev => [...prev, { role: 'ai', text: res.response }]);
    } catch (err) {
        setMessages(prev => [...prev, { role: 'ai', text: "Sorry, I encountered an error. Please try again." }]);
    } finally {
        setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg flex flex-col max-h-[80vh]">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50 rounded-t-xl">
            <div>
                <h3 className="font-bold text-gray-800">AI Assistant</h3>
                <p className="text-xs text-gray-500">Discussing {rca.metric}</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>
        
        <div id="chat-box" className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 ${
                        m.role === 'user' 
                            ? 'bg-blue-600 text-white rounded-br-none' 
                            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
                    }`}>
                        <p className="text-sm">{m.text}</p>
                    </div>
                </div>
            ))}
            {sending && (
                <div className="flex justify-start">
                    <div className="bg-gray-200 rounded-lg p-3 animate-pulse">
                        <span className="text-xs text-gray-500">Thinking...</span>
                    </div>
                </div>
            )}
        </div>

        <form onSubmit={send} className="p-4 border-t border-gray-200 bg-white rounded-b-xl">
            <div className="flex gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question..."
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={sending}
                />
                <button 
                    type="submit" 
                    disabled={sending || !input.trim()}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                    Send
                </button>
            </div>
        </form>
      </div>
    </div>
  );
}
