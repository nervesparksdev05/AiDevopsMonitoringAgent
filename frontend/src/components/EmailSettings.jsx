import { useState, useEffect } from 'react';

export default function EmailSettings() {
  const [config, setConfig] = useState({ enabled: false, recipients: [] });
  const [newEmail, setNewEmail] = useState('');
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch('http://localhost:8000/agent/email-config');
      const data = await response.json();
      setConfig(data);
      setLoading(false);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
      setLoading(false);
    }
  };

  const toggleEmail = async () => {
    try {
      const newConfig = { ...config, enabled: !config.enabled };
      await fetch('http://localhost:8000/agent/email-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      setConfig(newConfig);
      setMessage({ type: 'success', text: `Email alerts ${!config.enabled ? 'enabled' : 'disabled'}!` });
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const addRecipient = async (e) => {
    e.preventDefault();
    if (!newEmail || !newEmail.includes('@')) {
      setMessage({ type: 'error', text: 'Please enter a valid email' });
      return;
    }
    try {
      const newConfig = { ...config, recipients: [...config.recipients, newEmail] };
      await fetch('http://localhost:8000/agent/email-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      setConfig(newConfig);
      setNewEmail('');
      setMessage({ type: 'success', text: 'Recipient added!' });
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const deleteRecipient = async (email) => {
    try {
      const newConfig = { ...config, recipients: config.recipients.filter(e => e !== email) };
      await fetch('http://localhost:8000/agent/email-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      setConfig(newConfig);
      setMessage({ type: 'success', text: 'Recipient removed!' });
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const sendTestEmail = async () => {
    try {
      setMessage({ type: 'info', text: 'Sending test email...' });
      const response = await fetch('http://localhost:8000/agent/test-email', { method: 'POST' });
      const data = await response.json();
      setMessage({ type: 'success', text: data.message });
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Email Alerts</h2>
        <p className="text-gray-600">Configure email notifications for anomaly alerts</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-700' :
          message.type === 'info' ? 'bg-blue-50 text-blue-700' :
          'bg-red-50 text-red-700'
        }`}>
          {message.text}
        </div>
      )}

      {/* Email Toggle */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Email Alerts</h3>
            <p className="text-sm text-gray-600 mt-1">
              {config.enabled ? 'Emails will be sent for critical and high severity anomalies' : 'Email notifications are disabled'}
            </p>
          </div>
          <button
            onClick={toggleEmail}
            className={`relative inline-flex h-8 w-16 rounded-full transition-colors ${
              config.enabled ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition m-1 ${
              config.enabled ? 'translate-x-8' : 'translate-x-0'
            }`} />
          </button>
        </div>
      </div>

      {/* Add Recipient */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Add Recipient</h3>
        <form onSubmit={addRecipient} className="flex space-x-3">
          <input
            type="email"
            placeholder="email@example.com"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2"
            required
          />
          <button type="submit" className="bg-blue-600 text-white rounded-lg px-6 py-2 hover:bg-blue-700">
            Add
          </button>
        </form>
      </div>

      {/* Recipients List */}
<div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">
            Recipients ({config.recipients.length})
          </h3>
          {config.recipients.length > 0 && (
            <button
              onClick={sendTestEmail}
              className="text-sm bg-blue-100 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-200"
            >
              📧 Send Test Email
            </button>
          )}
        </div>
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          </div>
        ) : config.recipients.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No recipients configured. Add an email address above.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {config.recipients.map((email, index) => (
              <div key={index} className="p-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">📧</span>
                  <span className="text-gray-800">{email}</span>
                </div>
                <button
                  onClick={() => deleteRecipient(email)}
                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
