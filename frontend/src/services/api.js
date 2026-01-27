const API_BASE_URL = 'http://localhost:8000';

export const api = {
    // Health & Stats
    async getHealth() {
        const response = await fetch(`${API_BASE_URL}/`);
        if (!response.ok) throw new Error('Failed to fetch health status');
        return response.json();
    },

    async getStats() {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        return response.json();
    },

    // Anomalies
    async getAnomalies(params = {}) {
        const response = await fetch(`${API_BASE_URL}/anomalies`);
        if (!response.ok) throw new Error('Failed to fetch anomalies');
        return response.json();
    },

    // RCA
    async getRCA(params = {}) {
        const response = await fetch(`${API_BASE_URL}/rca`);
        if (!response.ok) throw new Error('Failed to fetch RCA');
        return response.json();
    },


    // Email Config
    async getEmailConfig() {
        const response = await fetch(`${API_BASE_URL}/agent/email-config`);
        if (!response.ok) throw new Error('Failed to fetch email config');
        return response.json();
    },

    async updateEmailConfig(config) {
        const response = await fetch(`${API_BASE_URL}/agent/email-config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!response.ok) throw new Error('Failed to update email config');
        return response.json();
    },

    async sendTestEmail() {
        const response = await fetch(`${API_BASE_URL}/agent/test-email`, {
            method: 'POST'
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to send test email');
        }
        return response.json();
    },

    // Chat
    async chat(payload) {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error('Chat failed');
        return response.json();
    }
};