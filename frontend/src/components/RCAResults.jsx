import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function RCAResults() {
  const [rcaResults, setRcaResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ severity: '', limit: 20 });

  useEffect(() => {
    fetchRCA();
  }, [filter]);

  const fetchRCA = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filter.severity) params.severity = filter.severity;
      if (filter.limit) params.limit = filter.limit;

      const data = await api.getRCA(params);
      setRcaResults(data.rca_results || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-700 border-red-300',
      high: 'bg-orange-100 text-orange-700 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      low: 'bg-blue-100 text-blue-700 border-blue-300',
    };
    return colors[severity] || colors.low;
  };

  const getInstanceInfo = (instance) => {
    const instanceMap = {
      'localhost:9090': { name: 'Prometheus', icon: '📊', color: 'bg-blue-100 text-blue-700 border-blue-300' },
      'localhost:8083': { name: 'FastAPI Backend', icon: '🚀', color: 'bg-green-100 text-green-700 border-green-300' },
      'localhost:8081': { name: 'FastAPI Service 2', icon: '⚡', color: 'bg-purple-100 text-purple-700 border-purple-300' },
      'localhost:9182': { name: 'Windows Exporter', icon: '💻', color: 'bg-orange-100 text-orange-700 border-orange-300' },
    };
    return instanceMap[instance] || { name: instance, icon: '🔧', color: 'bg-gray-100 text-gray-700 border-gray-300' };
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-gray-600">AI-powered root cause analysis and recommendations</p>
        <button
          onClick={fetchRCA}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
        >
          <span>🔄</span>
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Severity</label>
            <select
              value={filter.severity}
              onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Limit</label>
            <select
              value={filter.limit}
              onChange={(e) => setFilter({ ...filter, limit: e.target.value })}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>
      </div>

      {/* RCA List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">Error: {error}</p>
        </div>
      ) : rcaResults.length === 0 ? (
        <div className="bg-white rounded-xl p-12 shadow-sm text-center">
          <p className="text-gray-500 text-lg">No RCA results found</p>
        </div>
      ) : (
        <div className="space-y-6">
          {rcaResults.map((rca) => (
            <div
              key={rca.rca_id}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-800">{rca.metric}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(rca.severity)}`}>
                      {rca.severity?.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center space-x-2 px-3 py-1 rounded-lg text-xs font-medium border ${getInstanceInfo(rca.instance).color}`}>
                      <span>{getInstanceInfo(rca.instance).icon}</span>
                      <span>{getInstanceInfo(rca.instance).name}</span>
                      <span className="text-gray-500">({rca.instance})</span>
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    {new Date(rca.analyzed_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Root Cause */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-2xl">🔍</span>
                  <h4 className="text-sm font-semibold text-gray-700">Root Cause Analysis</h4>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-gray-700">{rca.root_cause}</p>
                </div>
              </div>

              {/* Recommended Action */}
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-2xl">💡</span>
                  <h4 className="text-sm font-semibold text-gray-700">Recommended Action</h4>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-gray-700 font-medium">{rca.action}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
