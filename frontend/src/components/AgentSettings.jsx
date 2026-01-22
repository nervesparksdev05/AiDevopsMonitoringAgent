import { useState, useEffect } from 'react';

export default function AgentSettings() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTarget, setNewTarget] = useState({ name: '', endpoint: '', job: '' });
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchTargets();
  }, []);

  const fetchTargets = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/agent/targets');
      const data = await response.json();
      setTargets(data.targets || []);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const addTarget = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/agent/targets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTarget)
      });
      if (response.ok) {
        setMessage({ type: 'success', text: 'Target added successfully!' });
        setNewTarget({ name: '', endpoint: '', job: '' });
        fetchTargets();
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const deleteTarget = async (id) => {
    try {
      await fetch(`http://localhost:8000/agent/targets/${id}`, { method: 'DELETE' });
      setMessage({ type: 'success', text: 'Target deleted!' });
      fetchTargets();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const toggleTarget = async (id, enabled) => {
    try {
      await fetch(`http://localhost:8000/agent/targets/${id}?enabled=${!enabled}`, { method: 'PUT' });
      fetchTargets();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Agent Configuration</h2>
        <p className="text-gray-600">Manage monitoring targets and endpoints</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {message.text}
        </div>
      )}

      {/* Add Target Form */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Add New Target</h3>
        <form onSubmit={addTarget} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Name (e.g., My Service)"
            value={newTarget.name}
            onChange={(e) => setNewTarget({...newTarget, name: e.target.value})}
            className="border border-gray-300 rounded-lg px-4 py-2"
            required
          />
          <input
            type="text"
            placeholder="Endpoint (e.g., localhost:8080)"
            value={newTarget.endpoint}
            onChange={(e) => setNewTarget({...newTarget, endpoint: e.target.value})}
            className="border border-gray-300 rounded-lg px-4 py-2"
            required
          />
          <input
            type="text"
            placeholder="Job (e.g., my-service)"
            value={newTarget.job}
            onChange={(e) => setNewTarget({...newTarget, job: e.target.value})}
            className="border border-gray-300 rounded-lg px-4 py-2"
            required
          />
          <button type="submit" className="bg-blue-600 text-white rounded-lg px-6 py-2 hover:bg-blue-700">
            Add Target
          </button>
        </form>
      </div>

      {/* Targets List */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">Current Targets ({targets.length})</h3>
        </div>
        {loading ? (
          <div className="p-12 text-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div></div>
        ) : (
          <div className="divide-y divide-gray-200">
            {targets.map((target) => (
              <div key={target.id} className="p-6 flex items-center justify-between hover:bg-gray-50">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800">{target.name}</h4>
                  <p className="text-sm text-gray-600">{target.endpoint} • {target.job}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => toggleTarget(target.id, target.enabled)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium ${
                      target.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {target.enabled ? '✓ Enabled' : 'Disabled'}
                  </button>
                  <button
                    onClick={() => deleteTarget(target.id)}
                    className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
