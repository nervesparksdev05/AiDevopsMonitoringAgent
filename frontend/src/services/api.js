const API_BASE_URL = 'http://localhost:8000';

export const api = {
    // Get stats
    async getStats() {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        return response.json();
    },

    // Get anomalies
    async getAnomalies(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const url = `${API_BASE_URL}/anomalies${queryParams ? `?${queryParams}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch anomalies');
        return response.json();
    },

    // Get RCA results
    async getRCA(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const url = `${API_BASE_URL}/rca${queryParams ? `?${queryParams}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch RCA');
        return response.json();
    },

    // Get Prometheus metrics
    async getPromMetrics(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const url = `${API_BASE_URL}/prom-metrics${queryParams ? `?${queryParams}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        return response.json();
    },
};
