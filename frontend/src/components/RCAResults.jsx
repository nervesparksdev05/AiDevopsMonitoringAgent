import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function RCAResults() {
  const [rcaResults, setRcaResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
                </div>
              </div>

              {/* Root Cause */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-2xl">🔍</span>
                  <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Root Cause</h4>
                </div>
                <div className="bg-purple-50 border-l-4 border-purple-500 rounded-lg p-4">
                  <p className="text-gray-800 leading-relaxed">{rca.cause || 'Analysis in progress...'}</p>
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
    </div>
  );
}