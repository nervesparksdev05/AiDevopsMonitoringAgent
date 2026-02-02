import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function SessionManagement() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const data = await api.getAuthSessions();
      setSessions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    if (!confirm('Are you sure you want to revoke this session?')) return;

    try {
      await api.revokeSession(sessionId);
      await loadSessions();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!confirm('Are you sure you want to revoke all other sessions?')) return;

    try {
      await api.revokeAllSessions(true);
      await loadSessions();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Active Sessions</h2>
        {sessions.length > 1 && (
          <button
            onClick={handleRevokeAllSessions}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Revoke All Other Sessions
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {sessions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No active sessions</p>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className={`border rounded-lg p-4 ${
                session.is_current ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">
                      {session.device.device_type === 'mobile' ? '📱' : 
                       session.device.device_type === 'tablet' ? '📱' : '🖥️'}
                    </span>
                    <h3 className="font-semibold text-gray-800">
                      {session.device.browser} on {session.device.os}
                      {session.is_current && (
                        <span className="ml-2 text-xs bg-blue-600 text-white px-2 py-1 rounded-full">
                          Current Session
                        </span>
                      )}
                    </h3>
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>
                      <span className="font-medium">IP Address:</span> {session.ip_address}
                    </p>
                    <p>
                      <span className="font-medium">Last Active:</span> {session.last_active_str}
                    </p>
                    <p>
                      <span className="font-medium">Created:</span> {session.created_at_str}
                    </p>
                  </div>
                </div>

                {!session.is_current && (
                  <button
                    onClick={() => handleRevokeSession(session.session_id)}
                    className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded text-sm font-medium transition-colors"
                  >
                    Revoke
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold text-gray-800 mb-2">About Sessions</h3>
        <p className="text-sm text-gray-600">
          Sessions represent your active logins across different devices and browsers. 
          You can revoke any session to log out that device remotely. Your current session 
          cannot be revoked from here - use the logout button instead.
        </p>
      </div>
    </div>
  );
}
