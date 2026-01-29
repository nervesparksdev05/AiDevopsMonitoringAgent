import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function ServerSettings() {
  const [targets, setTargets] = useState([]);
  const [newTarget, setNewTarget] = useState({ name: '', endpoint: '' });
  const [slackConfig, setSlackConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);
  const [slackTestSending, setSlackTestSending] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [tData, sData] = await Promise.all([
        api.getTargets(),
        api.getSlackConfig()
      ]);
      setTargets(tData);
      setSlackConfig(sData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddServer = async (e) => {
    e.preventDefault();
    if (!newTarget.name || !newTarget.endpoint) return;
    
    try {
      await api.addTarget(newTarget);
      setNewTarget({ name: '', endpoint: '' });
      await fetchData();
      setMsg("Server added successfully");
      setTimeout(() => setMsg(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRemoveServer = async (endpoint) => {
    if (!window.confirm(`Remove server ${endpoint}?`)) return;
    try {
      await api.removeTarget(endpoint);
      await fetchData();
      setMsg("Server removed");
      setTimeout(() => setMsg(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSlackSave = async () => {
    try {
      await api.updateSlackConfig(slackConfig);
      setMsg("Slack configuration saved");
      setTimeout(() => setMsg(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSlackTest = async () => {
    setSlackTestSending(true);
    try {
      await api.sendTestSlack();
      setMsg("Test alert sent to Slack!");
      setTimeout(() => setMsg(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSlackTestSending(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading settings...</div>;

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Server Management</h2>
        <p className="text-gray-600">Configure monitored servers and alert integrations.</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold">×</button>
        </div>
      )}

      {msg && (
        <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-lg">
          {msg}
        </div>
      )}

      {/* --- ADD SERVER --- */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Add New Server</h3>
        <form onSubmit={handleAddServer} className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            placeholder="Server Name (e.g. Prod DB)"
            className="flex-1 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            value={newTarget.name}
            onChange={(e) => setNewTarget({ ...newTarget, name: e.target.value })}
            required
          />
          <input
            type="text"
            placeholder="Endpoint (e.g. 192.168.1.5:9100)"
            className="flex-1 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
            value={newTarget.endpoint}
            onChange={(e) => setNewTarget({ ...newTarget, endpoint: e.target.value })}
            required
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Add Server
          </button>
        </form>
      </div>

      {/* --- SERVER LIST --- */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-800">Monitored Servers</h3>
          <span className="text-sm text-gray-500">{targets.length} active</span>
        </div>
        
        {targets.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No servers configured. Add one above to start monitoring.
          </div>
        ) : (
            <div className="divide-y divide-gray-100">
            {targets.map((t) => (
              <div key={t.endpoint} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div>
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-bold text-gray-700">{t.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      t.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {t.enabled ? 'ACTIVE' : 'DISABLED'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 font-mono mt-1">{t.endpoint}</p>
                </div>
                <button
                  onClick={() => handleRemoveServer(t.endpoint)}
                  className="text-red-500 hover:text-red-700 p-2 hover:bg-red-50 rounded-lg transition-colors"
                  title="Remove Server"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* --- SLACK CONFIG --- */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
            <span className="text-2xl">💬</span>
            <h3 className="text-lg font-semibold text-gray-800">Slack Integration</h3>
        </div>
        
        {slackConfig && (
            <div className="space-y-4">
                <div className="flex items-center space-x-3">
                    <label className="flex items-center cursor-pointer">
                        <div className="relative">
                        <input 
                            type="checkbox" 
                            className="sr-only" 
                            checked={slackConfig.enabled}
                            onChange={(e) => setSlackConfig({...slackConfig, enabled: e.target.checked})}
                        />
                        <div className={`block w-14 h-8 rounded-full transition-colors ${slackConfig.enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                        <div className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition transform ${slackConfig.enabled ? 'translate-x-6' : ''}`}></div>
                        </div>
                        <div className="ml-3 text-gray-700 font-medium">Enable Slack Alerts</div>
                    </label>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
                    <input
                        type="password" // Masked for security
                        value={slackConfig.webhook_url}
                        onChange={(e) => setSlackConfig({...slackConfig, webhook_url: e.target.value})}
                        placeholder="https://hooks.slack.com/services/..."
                        className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                    />
                </div>

                <div className="flex items-center gap-3 pt-2">
                    <button
                        onClick={handleSlackSave}
                        className="bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-gray-900 transition-colors"
                    >
                        Save Configuration
                    </button>
                    {slackConfig.enabled && slackConfig.webhook_url && (
                        <button
                            onClick={handleSlackTest}
                            disabled={slackTestSending}
                            className="text-blue-600 hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors"
                        >
                            {slackTestSending ? "Sending..." : "Test Alert"}
                        </button>
                    )}
                </div>
            </div>
        )}
      </div>
    </div>
  );
}
