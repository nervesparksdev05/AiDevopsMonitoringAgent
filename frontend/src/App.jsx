import { BrowserRouter as Router, Routes, Route, NavLink } from "react-router-dom";
import "./index.css";
import Dashboard from "./components/Dashboard";
import Anomalies from "./components/Anomalies";
import RCAResults from "./components/RCAResults";
import EmailSettings from "./components/EmailSettings";

function App() {
  const navItems = [
    { path: "/", name: "Dashboard", icon: "📊" },
    { path: "/anomalies", name: "Anomalies", icon: "🚨" },
    { path: "/rca", name: "RCA Results", icon: "🔍" },
  ];

  // Backend supports alert rules (not email-config endpoints)
  const settingsItems = [{ path: "/settings/alert-rules", name: "Alert Rules", icon: "⚙️" }];

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
              <h3 className="text-xs font-semibold text-blue-300 uppercase tracking-wider mb-2 px-4">
                Monitoring
              </h3>
              <ul className="space-y-2">
                {navItems.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      end={item.path === "/"}
                      className={({ isActive }) =>
                        `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          isActive ? "bg-white text-blue-600 shadow-md" : "text-blue-100 hover:bg-blue-700"
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
                          isActive ? "bg-white text-blue-600 shadow-md" : "text-blue-100 hover:bg-blue-700"
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

          <div className="p-4 text-xs text-blue-200 border-t border-blue-500">
            <p className="font-semibold">Enterprise Edition</p>
            <p>Real-time monitoring + AI RCA</p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/anomalies" element={<Anomalies />} />
              <Route path="/rca" element={<RCAResults />} />
              <Route path="/settings/alert-rules" element={<EmailSettings />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
