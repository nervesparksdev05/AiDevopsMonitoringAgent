import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ severity: '' });

  useEffect(() => {
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnomalies = async () => {
    try {
      if (anomalies.length === 0) {
        setLoading(true);
      }
      const data = await api.getAnomalies();
      setAnomalies(data.anomalies || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching anomalies:', err);
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

  const filteredAnomalies = filter.severity
    ? anomalies.filter(a => a.severity === filter.severity)
    : anomalies;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Anomalies</h2>
          <p className="text-gray-600">Detected anomalies with AI analysis</p>
        </div>
        <button
          onClick={fetchAnomalies}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50"
        >
          <span>{loading ? '...' : '↻'}</span>
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Severity Filter</label>
            <select
              value={filter.severity}
              onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All ({anomalies.length})</option>
              <option value="critical">Critical ({anomalies.filter(a => a.severity === 'critical').length})</option>
              <option value="high">High ({anomalies.filter(a => a.severity === 'high').length})</option>
              <option value="medium">Medium ({anomalies.filter(a => a.severity === 'medium').length})</option>
              <option value="low">Low ({anomalies.filter(a => a.severity === 'low').length})</option>
            </select>
          </div>
          <div className="flex items-end">
            <div className="bg-blue-50 px-4 py-3 rounded-lg w-full border border-blue-200">
              <p className="text-sm text-gray-600">Showing</p>
              <p className="text-2xl font-bold text-blue-600">{filteredAnomalies.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Anomalies List */}
      {loading && anomalies.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600 mb-2">Error: {error}</p>
          <button 
            onClick={fetchAnomalies}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      ) : filteredAnomalies.length === 0 ? (
        <div className="bg-white rounded-xl p-12 shadow-sm text-center border border-gray-200">
          <div className="text-6xl mb-4">✓</div>
          <p className="text-gray-500 text-lg">No anomalies found</p>
          <p className="text-gray-400 text-sm mt-2">
            {filter.severity ? 'Try changing the severity filter' : 'All systems operating normally'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAnomalies.map((anomaly, idx) => (
            <div
              key={anomaly._id || idx}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-800">{anomaly.metric}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(anomaly.severity)}`}>
                      {anomaly.severity?.toUpperCase()}
                    </span>
                  </div>
                  {anomaly.instance && (
                    <p className="text-sm text-gray-500 mb-2">Instance: {anomaly.instance}</p>
                  )}
                  <p className="text-sm text-gray-600">{anomaly.reason}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    {new Date(anomaly.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-xs text-gray-600 mb-1">Metric Value</p>
                  <p className="text-2xl font-bold text-gray-800">
                    {typeof anomaly.value === 'number' ? anomaly.value.toFixed(2) : anomaly.value}
                  </p>
                </div>
                <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                  <p className="text-xs text-gray-600 mb-1">Issue</p>
                  <p className="text-sm font-semibold text-red-600">{anomaly.reason}</p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>ID: {anomaly._id}</span>
                  <span>Detected: {new Date(anomaly.timestamp).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}