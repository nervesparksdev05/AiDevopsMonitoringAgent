import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  const StatCard = ({ title, value, subtitle, icon, color }) => (
    <div className={`bg-white rounded-xl p-6 border-l-4 ${color} shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-800">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-2">{subtitle}</p>}
        </div>
        <div className="text-4xl opacity-20">{icon}</div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Anomalies"
          value={stats?.collections?.anomalies?.total || 0}
          icon="🚨"
          color="border-red-500"
        />
        <StatCard
          title="Open Anomalies"
          value={stats?.collections?.anomalies?.open || 0}
          subtitle="Pending RCA"
          icon="⚠️"
          color="border-orange-500"
        />
        <StatCard
          title="Analyzed"
          value={stats?.collections?.anomalies?.analyzed || 0}
          subtitle="RCA Complete"
          icon="✅"
          color="border-green-500"
        />
        <StatCard
          title="RCA Results"
          value={stats?.collections?.rca_results?.total || 0}
          icon="🔍"
          color="border-blue-500"
        />
      </div>

      {/* Metrics Collection */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Metrics Collection</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <span className="text-gray-700">Total Data Points</span>
            <span className="text-2xl font-bold text-blue-600">
              {stats?.collections?.prom_rollup_1m?.total || 0}
            </span>
          </div>
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <span className="text-gray-700">Collection Status</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-700 font-semibold">Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <HealthIndicator label="API Server" status="healthy" />
          <HealthIndicator label="MongoDB" status="healthy" />
          <HealthIndicator label="Prometheus" status="healthy" />
          <HealthIndicator label="LLM Service" status="healthy" />
        </div>
      </div>
    </div>
  );
}

function HealthIndicator({ label, status }) {
  const statusConfig = {
    healthy: { color: 'bg-green-500', text: 'Healthy', textColor: 'text-green-700', bgColor: 'bg-green-50' },
    warning: { color: 'bg-yellow-500', text: 'Warning', textColor: 'text-yellow-700', bgColor: 'bg-yellow-50' },
    error: { color: 'bg-red-500', text: 'Error', textColor: 'text-red-700', bgColor: 'bg-red-50' },
  };

  const config = statusConfig[status] || statusConfig.healthy;

  return (
    <div className={`flex items-center justify-between p-3 ${config.bgColor} rounded-lg`}>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 ${config.color} rounded-full animate-pulse`}></div>
        <span className="font-medium text-gray-700">{label}</span>
      </div>
      <span className={`text-sm font-semibold ${config.textColor}`}>{config.text}</span>
    </div>
  );
}
