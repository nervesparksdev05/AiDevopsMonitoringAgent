/**
 * API Service
 * Matches endpoints from main.py backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
    // ============ HEALTH & STATS ============

    async getHealth() {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error('Failed to fetch health status');
        return response.json();
    },

    async getStats() {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        return response.json();
    },

    // ============ DATA ENDPOINTS ============

    async getPromMetrics() {
        const response = await fetch(`${API_BASE_URL}/prom-metrics`);
        if (!response.ok) throw new Error('Failed to fetch Prometheus metrics');
        return response.json();
    },

    async getAnomalies() {
        const response = await fetch(`${API_BASE_URL}/anomalies`);
        if (!response.ok) throw new Error('Failed to fetch anomalies');
        return response.json();
    },

    async getRCA() {
        const response = await fetch(`${API_BASE_URL}/rca`);
        if (!response.ok) throw new Error('Failed to fetch RCA');
        return response.json();
    },

    // ============ CHAT ENDPOINT ============

    async chat(payload) {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Chat failed');
        }
        return response.json();
    },

    // ============ SESSION MANAGEMENT ============

    async getSessions() {
        const response = await fetch(`${API_BASE_URL}/api/sessions`);
        if (!response.ok) throw new Error('Failed to fetch sessions');
        return response.json();
    },

    async getSessionDetails(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
        if (!response.ok) throw new Error('Failed to fetch session details');
        return response.json();
    },

    async deleteSession(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to delete session');
        }
        return response.json();
    },

    // ============ EMAIL CONFIGURATION ============

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
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Failed to update email config');
        }
        return response.json();
    },

    async sendTestEmail() {
        const response = await fetch(`${API_BASE_URL}/agent/test-email`, {
            method: 'POST'
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Failed to send test email');
        }
        return response.json();
    },

    // ============ SLACK (ENV ONLY) ============

    async getSlackStatus() {
        const response = await fetch(`${API_BASE_URL}/agent/slack-status`);
        if (!response.ok) throw new Error('Failed to fetch Slack status');
        return response.json();
    },

    async sendTestSlack() {
        const response = await fetch(`${API_BASE_URL}/agent/test-slack`, {
            method: 'POST'
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Failed to send test Slack message');
        }
        return response.json();
    },

    // ============ SERVER / TARGET MANAGEMENT ============

    async getTargets() {
        const response = await fetch(`${API_BASE_URL}/agent/targets`);
        if (!response.ok) throw new Error('Failed to fetch targets');
        return response.json();
    },

    async addTarget(target) {
        const response = await fetch(`${API_BASE_URL}/agent/targets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(target)
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Failed to add target');
        }
        return response.json();
    },

    async removeTarget(endpoint) {
        const response = await fetch(`${API_BASE_URL}/agent/targets/${encodeURIComponent(endpoint)}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Failed to remove target');
        }
        return response.json();
    },

    // ============ SLACK CONFIGURATION ============

    async getSlackConfig() {
        const response = await fetch(`${API_BASE_URL}/agent/slack-config`);
        if (!response.ok) throw new Error('Failed to fetch Slack config');
        return response.json();
    },

    async updateSlackConfig(config) {
        const response = await fetch(`${API_BASE_URL}/agent/slack-config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || 'Failed to update Slack config');
        }
        return response.json();
    },

    // ============ LANGFUSE STATUS ============

    async getLangfuseStatus() {
        const response = await fetch(`${API_BASE_URL}/langfuse/status`);
        if (!response.ok) throw new Error('Failed to fetch Langfuse status');
        return response.json();
    }
};