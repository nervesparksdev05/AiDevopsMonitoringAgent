import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const [statsData, healthData] = await Promise.all([
        api.getStats(),
        api.getHealth()
      ]);
      setStats(statsData);
      setHealth(healthData);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Dashboard error:', err);
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
        <p className="text-red-600 mb-2">⚠️ Error: {error}</p>
        <button 
          onClick={fetchStats}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry Connection
        </button>
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
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      {health && (
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold mb-2">
                {health.status === "running" ? "🟢 System Online" : "⚠️ System Status"}
              </h3>
              <div className="space-y-1 text-blue-100">
                <p>📊 Prometheus: {health.prometheus || 'Not configured'}</p>
                <p>🤖 LLM: {health.llm || 'Not configured'}</p>
                {health.current_time && (
                  <p>🕐 Current Time: {health.current_time}</p>
                )}
                {health.timezone && (
                  <p>🌍 Timezone: {health.timezone}</p>
                )}
                {health.langfuse && (
                  <p>📈 Langfuse: {health.langfuse}</p>
                )}
                {health.slack && (
                  <p>💬 Slack: {health.slack === "enabled" ? "✅ Enabled" : "❌ Disabled"}</p>
                )}
              </div>
            </div>
            <div className="text-6xl">
              {health.status === "running" ? "✓" : "⚠"}
            </div>
          </div>
        </div>
      )}

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Metrics"
          value={stats?.collections?.metrics?.total || 0}
          subtitle="Prometheus snapshots"
          icon="📊"
          color="border-blue-500"
        />
        <StatCard
          title="Total Anomalies"
          value={stats?.collections?.anomalies?.total || 0}
          subtitle="AI detected issues"
          icon="🚨"
          color="border-red-500"
        />
        <StatCard
          title="Open Issues"
          value={stats?.collections?.anomalies?.open || 0}
          subtitle="Critical + High severity"
          icon="⚠"
          color="border-orange-500"
        />
        <StatCard
          title="RCA Complete"
          value={stats?.collections?.anomalies?.analyzed || 0}
          subtitle="AI analysis done"
          icon="✓"
          color="border-green-500"
        />
      </div>

      {/* Incidents Summary */}
      {stats?.collections?.incidents && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">📋 Incidents Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <p className="text-sm text-gray-600 mb-1">Total Incidents</p>
              <p className="text-3xl font-bold text-purple-600">
                {stats.collections.incidents.total || 0}
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <p className="text-sm text-gray-600 mb-1">Metrics Batches</p>
              <p className="text-3xl font-bold text-blue-600">
                {stats.collections.metrics_batches?.total || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Chat Sessions */}
      {stats?.collections?.chat_sessions && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">💬 AI Chat Sessions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg border border-purple-200">
              <span className="text-gray-700 font-medium">Total Sessions</span>
              <span className="text-2xl font-bold text-purple-600">
                {stats.collections.chat_sessions.total || 0}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
              <span className="text-gray-700 font-medium">Active (Last Hour)</span>
              <span className="text-2xl font-bold text-green-600">
                {stats.collections.chat_sessions.active || 0}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Notifications Status */}
      {stats?.notifications && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🔔 Notification Channels</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Email Status */}
            <div className={`p-4 rounded-lg border-2 ${
              stats.notifications.email?.enabled 
                ? 'bg-green-50 border-green-200' 
                : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-700">📧 Email Alerts</span>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                  stats.notifications.email?.enabled 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-400 text-white'
                }`}>
                  {stats.notifications.email?.enabled ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
              {stats.notifications.email?.enabled && (
                <p className="text-sm text-gray-600">
                  {stats.notifications.email.recipients || 0} recipient(s) configured
                </p>
              )}
            </div>

            {/* Slack Status */}
            <div className={`p-4 rounded-lg border-2 ${
              stats.notifications.slack?.enabled && stats.notifications.slack?.configured
                ? 'bg-green-50 border-green-200' 
                : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-700">💬 Slack Alerts</span>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                  stats.notifications.slack?.enabled && stats.notifications.slack?.configured
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-400 text-white'
                }`}>
                  {stats.notifications.slack?.enabled && stats.notifications.slack?.configured ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
              {stats.notifications.slack?.configured && (
                <p className="text-sm text-gray-600">Webhook configured ✓</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* System Components Health */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">🔧 System Components</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <HealthIndicator 
            label="API Server" 
            status="healthy" 
          />
          <HealthIndicator 
            label="MongoDB" 
            status={stats?.collections ? "healthy" : "warning"} 
          />
          <HealthIndicator 
            label="Prometheus" 
            status={health?.prometheus ? "healthy" : "error"} 
          />
          <HealthIndicator 
            label="LLM Service" 
            status={health?.llm ? "healthy" : "warning"} 
          />
        </div>
      </div>
    </div>
  );
}

function HealthIndicator({ label, status }) {
  const statusConfig = {
    healthy: { 
      color: 'bg-green-500', 
      text: 'Healthy', 
      textColor: 'text-green-700', 
      bgColor: 'bg-green-50',
      icon: '✓'
    },
    warning: { 
      color: 'bg-yellow-500', 
      text: 'Warning', 
      textColor: 'text-yellow-700', 
      bgColor: 'bg-yellow-50',
      icon: '⚠'
    },
    error: { 
      color: 'bg-red-500', 
      text: 'Error', 
      textColor: 'text-red-700', 
      bgColor: 'bg-red-50',
      icon: '✕'
    },
  };

  const config = statusConfig[status] || statusConfig.healthy;

  return (
    <div className={`flex items-center justify-between p-3 ${config.bgColor} rounded-lg border border-gray-200`}>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 ${config.color} rounded-full ${status === 'healthy' ? 'animate-pulse' : ''}`}></div>
        <span className="font-medium text-gray-700 text-sm">{label}</span>
      </div>
      <div className="flex items-center space-x-1">
        <span className="text-lg">{config.icon}</span>
        <span className={`text-xs font-semibold ${config.textColor}`}>{config.text}</span>
      </div>
    </div>
  );
}