import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function EmailSettings() {
  const [config, setConfig] = useState({ enabled: false, recipients: [] });
  const [newEmail, setNewEmail] = useState('');
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sendingTest, setSendingTest] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const data = await api.getEmailConfig();
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
      await api.updateEmailConfig(newConfig);
      setConfig(newConfig);
      setMessage({ 
        type: 'success', 
        text: `Email alerts ${!config.enabled ? 'enabled' : 'disabled'}!` 
      });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const addRecipient = async (e) => {
    e.preventDefault();
    
    // Validate email
    if (!newEmail || !newEmail.includes('@')) {
      setMessage({ type: 'error', text: 'Please enter a valid email address' });
      return;
    }

    // Check for duplicates
    if (config.recipients.includes(newEmail)) {
      setMessage({ type: 'error', text: 'This email is already in the list' });
      return;
    }

    try {
      const newConfig = { ...config, recipients: [...config.recipients, newEmail] };
      await api.updateEmailConfig(newConfig);
      setConfig(newConfig);
      setNewEmail('');
      setMessage({ type: 'success', text: 'Recipient added successfully!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const deleteRecipient = async (email) => {
    if (!window.confirm(`Remove ${email} from recipients?`)) {
      return;
    }

    try {
      const newConfig = { ...config, recipients: config.recipients.filter(e => e !== email) };
      await api.updateEmailConfig(newConfig);
      setConfig(newConfig);
      setMessage({ type: 'success', text: 'Recipient removed!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const sendTestEmail = async () => {
    if (config.recipients.length === 0) {
      setMessage({ type: 'error', text: 'Please add at least one recipient first' });
      return;
    }

    try {
      setSendingTest(true);
      setMessage({ type: 'info', text: 'Sending test email...' });
      await api.sendTestEmail();
      setMessage({ type: 'success', text: 'Test email sent successfully! Check your inbox.' });
      setTimeout(() => setMessage(null), 5000);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setSendingTest(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Email Alerts</h2>
        <p className="text-gray-600">Configure email notifications for anomaly alerts</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg border ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' :
          message.type === 'info' ? 'bg-blue-50 text-blue-700 border-blue-200' :
          'bg-red-50 text-red-700 border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            <span className="font-medium">
              {message.type === 'success' && '✓'}
              {message.type === 'error' && '✕'}
              {message.type === 'info' && 'ℹ'}
            </span>
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Email Toggle */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Email Alerts</h3>
            <p className="text-sm text-gray-600 mt-1">
              {config.enabled 
                ? 'Emails will be sent for critical and high severity anomalies' 
                : 'Email notifications are currently disabled'}
            </p>
          </div>
          <button
            onClick={toggleEmail}
            disabled={loading}
            className={`relative inline-flex h-8 w-16 rounded-full transition-colors ${
              config.enabled ? 'bg-blue-600' : 'bg-gray-300'
            } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition m-1 ${
              config.enabled ? 'translate-x-8' : 'translate-x-0'
            }`} />
          </button>
        </div>
      </div>

      {/* Add Recipient */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Add Recipient</h3>
        <form onSubmit={addRecipient} className="flex space-x-3">
          <input
            type="email"
            placeholder="email@example.com"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button 
            type="submit" 
            className="bg-blue-600 text-white rounded-lg px-6 py-2 hover:bg-blue-700 transition-colors font-medium"
          >
            + Add
          </button>
        </form>
      </div>

      {/* Recipients List */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">
            Recipients ({config.recipients.length})
          </h3>
          {config.recipients.length > 0 && (
            <button
              onClick={sendTestEmail}
              disabled={sendingTest || !config.enabled}
              className={`text-sm px-4 py-2 rounded-lg font-medium transition-colors ${
                sendingTest || !config.enabled
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200 border border-blue-200'
              }`}
            >
              {sendingTest ? 'Sending...' : '📧 Send Test Email'}
            </button>
          )}
        </div>
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          </div>
        ) : config.recipients.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <p className="text-lg mb-2">No recipients configured</p>
            <p className="text-sm text-gray-400">Add an email address above to receive alerts</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {config.recipients.map((email, index) => (
              <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">📧</span>
                    <span className="text-gray-800 font-medium">{email}</span>
                  </div>
                  <button
                    onClick={() => deleteRecipient(email)}
                    className="text-red-600 hover:text-red-800 text-sm font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}