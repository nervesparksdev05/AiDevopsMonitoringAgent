import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Metrics() {
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('grouped'); // 'grouped' or 'table'
  const [filter, setFilter] = useState({ metric: '', instance: '', limit: 500 }); // Increased limit

  useEffect(() => {
    fetchMetrics();
    // Auto-refresh every 30 seconds (increased from 10s to avoid conflicts)
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  // Separate effect for filter changes to avoid conflicts
  useEffect(() => {
    if (!loading) {  // Only fetch if not already loading
      fetchMetrics();
    }
  }, [filter.metric, filter.instance]);

  const fetchMetrics = async () => {
    try {
      // Don't show loading spinner on refresh, only on initial load
      if (metrics.length === 0) {
        setLoading(true);
      }
      
      const params = {};
      if (filter.metric) params.metric = filter.metric;
      if (filter.instance) params.instance = filter.instance;
      if (filter.limit) params.limit = filter.limit;

      const data = await api.getPromMetrics(params);
      setMetrics(data.metrics || []);
      setError(null);
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message);
      // Don't clear metrics on error, keep showing old data
    } finally {
      setLoading(false);
    }
  };

  // Group metrics by instance
  const groupedMetrics = metrics.reduce((acc, metric) => {
    const instance = metric.instance || 'unknown';
    if (!acc[instance]) {
      acc[instance] = [];
    }
    acc[instance].push(metric);
    return acc;
  }, {});

  // Get instance info
  const getInstanceInfo = (instance) => {
    const instanceMap = {
      'localhost:9090': { name: 'Prometheus', icon: '📊', color: 'blue', description: 'Metrics Server' },
      'localhost:8083': { name: 'FastAPI Backend', icon: '🚀', color: 'green', description: 'Main API Service' },
      'localhost:8081': { name: 'FastAPI Service 2', icon: '⚡', color: 'purple', description: 'Secondary API' },
      'localhost:9182': { name: 'Windows Exporter', icon: '💻', color: 'orange', description: 'System Metrics' },
    };
    return instanceMap[instance] || { name: instance, icon: '🔧', color: 'gray', description: 'Service' };
  };

  const metricNames = [
    // FastAPI
    'process_resident_memory_bytes',
    'process_virtual_memory_bytes',
    'process_cpu_seconds_total',
    'http_requests_total',
    'http_request_duration_seconds_bucket',
    // Prometheus
    'go_goroutines',
    'go_memstats_alloc_bytes',
    'prometheus_tsdb_head_samples_appended_total',
    // Windows
    'windows_cpu_time_total',
    'windows_os_physical_memory_free_bytes',
    'windows_logical_disk_free_bytes',
    'windows_net_bytes_received_total',
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600">Real-time metrics from all endpoints</p>
          <p className="text-sm text-gray-500 mt-1">
            {Object.keys(groupedMetrics).length} instances • {metrics.length} metrics
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {/* View Mode Toggle */}
          <div className="bg-white rounded-lg p-1 shadow-sm border border-gray-200">
            <button
              onClick={() => setViewMode('grouped')}
              className={`px-4 py-2 rounded-md transition-colors ${
                viewMode === 'grouped'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              📦 Grouped
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 rounded-md transition-colors ${
                viewMode === 'table'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              📋 Table
            </button>
          </div>
          <button
            onClick={fetchMetrics}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <span>🔄</span>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Metric</label>
            <select
              value={filter.metric}
              onChange={(e) => setFilter({ ...filter, metric: e.target.value })}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Metrics</option>
              {metricNames.map((name) => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Instance</label>
            <select
              value={filter.instance}
              onChange={(e) => setFilter({ ...filter, instance: e.target.value })}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Instances</option>
              {Object.keys(groupedMetrics).map((instance) => {
                const info = getInstanceInfo(instance);
                return (
                  <option key={instance} value={instance}>
                    {info.icon} {info.name} ({instance})
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      {loading && metrics.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">Error: {error}</p>
        </div>
      ) : metrics.length === 0 ? (
        <div className="bg-white rounded-xl p-12 shadow-sm text-center">
          <p className="text-gray-500 text-lg">No metrics found</p>
          <p className="text-gray-400 text-sm mt-2">Try adjusting your filters or wait for data collection</p>
        </div>
      ) : viewMode === 'grouped' ? (
        <div className="space-y-6">
          {Object.entries(groupedMetrics).map(([instance, instanceMetrics]) => {
            const info = getInstanceInfo(instance);
            const colorClasses = {
              blue: 'from-blue-500 to-blue-600',
              green: 'from-green-500 to-green-600',
              purple: 'from-purple-500 to-purple-600',
              orange: 'from-orange-500 to-orange-600',
              gray: 'from-gray-500 to-gray-600',
            };

            return (
              <div key={instance} className="bg-white rounded-xl shadow-sm overflow-hidden">
                {/* Instance Header */}
                <div className={`bg-gradient-to-r ${colorClasses[info.color]} p-4 text-white`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-3xl">{info.icon}</span>
                      <div>
                        <h3 className="text-lg font-bold">{info.name}</h3>
                        <p className="text-sm opacity-90">{info.description} • {instance}</p>
                      </div>
                    </div>
                    <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg">
                      <p className="text-sm font-semibold">{instanceMetrics.length} metrics</p>
                    </div>
                  </div>
                </div>

                {/* Metrics Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          Metric
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          Value
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          Min
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          Max
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                          Avg
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {instanceMetrics.map((metric, index) => (
                        <tr key={index} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {new Date(metric.ts).toLocaleTimeString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-800 font-medium">
                            {metric.metric}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-mono font-semibold">
                            {metric.value?.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                            {metric.min?.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                            {metric.max?.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                            {metric.avg?.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Metric
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Instance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Min
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Max
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Avg
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {metrics.map((metric, index) => (
                  <tr key={index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(metric.ts).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-800 font-medium">
                      {metric.metric}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="inline-flex items-center space-x-1">
                        <span>{getInstanceInfo(metric.instance).icon}</span>
                        <span className="text-gray-600">{metric.instance}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-mono font-semibold">
                      {metric.value?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                      {metric.min?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                      {metric.max?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                      {metric.avg?.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
