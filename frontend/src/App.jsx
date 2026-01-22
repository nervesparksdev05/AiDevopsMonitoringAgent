import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import './index.css';
import Dashboard from './components/Dashboard';
import Anomalies from './components/Anomalies';
import RCAResults from './components/RCAResults';
import Metrics from './components/Metrics';
import AgentSettings from './components/AgentSettings';
import EmailSettings from './components/EmailSettings';

function App() {
  const navItems = [
    { path: '/', name: 'Dashboard', icon: '📊' },
    { path: '/anomalies', name: 'Anomalies', icon: '🚨' },
    { path: '/rca', name: 'RCA Results', icon: '🔍' },
    { path: '/metrics', name: 'Metrics', icon: '📋' },
  ];

  const settingsItems = [
    { path: '/settings/agent', name: 'Agent Config', icon: '⚙️' },
    { path: '/settings/email', name: 'Email Alerts', icon: '📧' },
  ];

  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        {/* Left Sidebar */}
        <aside className="w-64 bg-blue-600 text-white flex flex-col shadow-xl">
          {/* Logo/Header */}
          <div className="p-6 bg-blue-700">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <span className="text-2xl">🤖</span>
              </div>
              <div>
                <h1 className="text-lg font-bold">AI DevOps</h1>
                <p className="text-xs text-blue-200">Monitoring</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-blue-300 uppercase tracking-wider mb-2 px-4">Monitoring</h3>
              <ul className="space-y-2">
                {navItems.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      end={item.path === '/'}
                      className={({ isActive }) =>
                        `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          isActive
                            ? 'bg-white text-blue-600 shadow-md'
                            : 'text-blue-100 hover:bg-blue-700'
                        }`
                      }
                    >
                      <span className="text-xl">{item.icon}</span>
                      <span className="font-medium">{item.name}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold text-blue-300 uppercase tracking-wider mb-2 px-4">Settings</h3>
              <ul className="space-y-2">
                {settingsItems.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={({ isActive }) =>
                        `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          isActive
                            ?'bg-white text-blue-600 shadow-md'
                            : 'text-blue-100 hover:bg-blue-700'
                        }`
                      }
                    >
                      <span className="text-xl">{item.icon}</span>
                      <span className="font-medium">{item.name}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          </nav>

          {/* Footer */}
          <div className="p-4 bg-blue-700">
            <div className="flex items-center justify-between bg-blue-800 px-3 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-blue-100">Live</span>
              </div>
              <span className="text-xs text-blue-200">Active</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          {/* Top Bar */}
          <header className="bg-white border-b border-gray-200 px-8 py-4 sticky top-0 z-10 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">AI DevOps Monitoring</h2>
                <p className="text-sm text-gray-600">Intelligent Anomaly Detection & Root Cause Analysis</p>
              </div>
              <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-blue-700">
                  {new Date().toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
              </div>
            </div>
          </header>

          {/* Page Content */}
          <div className="p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/anomalies" element={<Anomalies />} />
              <Route path="/rca" element={<RCAResults />} />
              <Route path="/metrics" element={<Metrics />} />
              <Route path="/settings/agent" element={<AgentSettings />} />
              <Route path="/settings/email" element={<EmailSettings />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
