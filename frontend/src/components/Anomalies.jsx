import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ severity: '' });

  useEffect(() => {
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 10000); // Refresh every 10s
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
      console.error('Anomalies fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const sev = (severity || 'medium').toLowerCase();
    const colors = {
      critical: 'bg-red-100 text-red-700 border-red-300',
      high: 'bg-orange-100 text-orange-700 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      low: 'bg-blue-100 text-blue-700 border-blue-300',
    };
    return colors[sev] || colors.medium;
  };

  const getSeverityIcon = (severity) => {
    const sev = (severity || 'medium').toLowerCase();
    const icons = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🔵'
    };
    return icons[sev] || icons.medium;
  };

  const filteredAnomalies = filter.severity
    ? anomalies.filter(a => (a.severity || 'medium').toLowerCase() === filter.severity)
    : anomalies;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">🚨 Anomalies</h2>
          <p className="text-gray-600">AI-detected anomalies with root cause analysis</p>
        </div>
        <button
          onClick={fetchAnomalies}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span className={loading ? 'animate-spin' : ''}>↻</span>
          <span>{loading ? 'Loading...' : 'Refresh'}</span>
        </button>
      </div>

      {/* Filters and Stats */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Severity Filter */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Severity</label>
            <select
              value={filter.severity}
              onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities ({anomalies.length})</option>
              <option value="critical">🔴 Critical ({anomalies.filter(a => (a.severity || '').toLowerCase() === 'critical').length})</option>
              <option value="high">🟠 High ({anomalies.filter(a => (a.severity || '').toLowerCase() === 'high').length})</option>
              <option value="medium">🟡 Medium ({anomalies.filter(a => (a.severity || '').toLowerCase() === 'medium').length})</option>
              <option value="low">🔵 Low ({anomalies.filter(a => (a.severity || '').toLowerCase() === 'low').length})</option>
            </select>
          </div>

          {/* Count Display */}
          <div className="flex items-end">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-4 py-3 rounded-lg w-full border border-blue-200">
              <p className="text-sm text-gray-600">Displaying</p>
              <p className="text-3xl font-bold text-blue-600">{filteredAnomalies.length}</p>
              <p className="text-xs text-gray-500">anomalies</p>
            </div>
          </div>
        </div>
      </div>

      {/* Anomalies List */}
      {loading && anomalies.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 bg-white rounded-xl shadow-sm">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-500">Loading anomalies...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">⚠️</span>
            <div className="flex-1">
              <p className="text-red-700 font-semibold mb-2">Failed to load anomalies</p>
              <p className="text-red-600 text-sm mb-4">{error}</p>
              <button 
                onClick={fetchAnomalies}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      ) : filteredAnomalies.length === 0 ? (
        <div className="bg-white rounded-xl p-12 shadow-sm text-center border border-gray-200">
          <div className="text-6xl mb-4">
            {filter.severity ? '🔍' : '✅'}
          </div>
          <p className="text-gray-700 text-lg font-semibold mb-2">
            {filter.severity ? 'No anomalies match your filter' : 'No anomalies detected'}
          </p>
          <p className="text-gray-500 text-sm">
            {filter.severity 
              ? 'Try selecting a different severity level' 
              : 'All systems are operating normally'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAnomalies.map((anomaly, idx) => (
            <div
              key={anomaly._id || idx}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-all"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-2xl">{getSeverityIcon(anomaly.severity)}</span>
                    <h3 className="text-lg font-bold text-gray-800">
                      {anomaly.metric || 'Unknown Metric'}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getSeverityColor(anomaly.severity)}`}>
                      {(anomaly.severity || 'MEDIUM').toUpperCase()}
                    </span>
                  </div>
                  
                  {anomaly.instance && (
                    <p className="text-sm text-gray-600 mb-2">
                      <span className="font-medium">Instance:</span> {anomaly.instance}
                    </p>
                  )}
                  
                  <p className="text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 inline-block">
                    {anomaly.symptom || anomaly.reason || "Anomalous behavior detected"}
                  </p>
                </div>
                
                <div className="text-right ml-4">
                  <p className="text-xs text-gray-500">Detected</p>
                  <p className="text-sm font-medium text-gray-700">
                    {anomaly.timestamp ? new Date(anomaly.timestamp).toLocaleTimeString() : 'Just now'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {anomaly.timestamp ? new Date(anomaly.timestamp).toLocaleDateString() : ''}
                  </p>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                  <p className="text-xs text-gray-600 mb-1 font-medium">Observed Value</p>
                  <p className="text-2xl font-bold text-gray-800">
                    {anomaly.observed !== undefined 
                      ? (typeof anomaly.observed === 'number' ? anomaly.observed.toFixed(2) : anomaly.observed)
                      : (typeof anomaly.value === 'number' ? anomaly.value.toFixed(2) : (anomaly.value || 'N/A'))
                    }
                  </p>
                </div>
                
                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4 border border-yellow-200">
                  <p className="text-xs text-gray-600 mb-1 font-medium">Expected Range</p>
                  <p className="text-sm font-semibold text-yellow-700">
                    {anomaly.expected || 'Normal baseline'}
                  </p>
                </div>

                {anomaly.cluster && (
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                    <p className="text-xs text-gray-600 mb-1 font-medium">Cluster</p>
                    <p className="text-sm font-semibold text-purple-700">
                      {anomaly.cluster}
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>ID: {anomaly._id?.substring(0, 8)}...</span>
                    {anomaly.batch_id && <span>Batch: {anomaly.batch_id.substring(0, 8)}...</span>}
                    {anomaly.incident_id && <span>Incident: {anomaly.incident_id.substring(0, 8)}...</span>}
                  </div>
                  <p className="text-xs text-gray-500">
                    {anomaly.timestamp || 'Recent'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Auto-refresh indicator */}
      {!loading && anomalies.length > 0 && (
        <div className="text-center text-xs text-gray-500">
          <p>🔄 Auto-refreshing every 10 seconds</p>
        </div>
      )}
    </div>
  );
}