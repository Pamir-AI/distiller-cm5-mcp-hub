/**
 * API Client for MCP Development Platform
 * Handles all HTTP requests and WebSocket connections
 */

class APIClient {
    constructor() {
        this.baseURL = '';
        this.websockets = new Map();
    }

    /**
     * Utility method for making HTTP requests
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    /**
     * Health Check
     */
    async healthCheck() {
        return await this.request('/health');
    }

    /**
     * Project Management API
     */
    async listProjects() {
        return await this.request('/api/projects');
    }

    async getProject(projectId) {
        return await this.request(`/api/projects/${projectId}`);
    }

    async createProject(projectData) {
        return await this.request('/api/projects', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    }

    async installDependencies(projectId) {
        return await this.request(`/api/projects/${projectId}/install`, {
            method: 'POST'
        });
    }

    async getProjectStats(projectId) {
        return await this.request(`/api/projects/${projectId}/stats`);
    }

    /**
     * Debug Session API
     */
    async startDebugSession(projectId) {
        return await this.request(`/api/debug/${projectId}/start`, {
            method: 'POST'
        });
    }

    async stopDebugSession(projectId) {
        return await this.request(`/api/debug/${projectId}/stop`, {
            method: 'POST'
        });
    }

    async getDebugStatus(projectId) {
        return await this.request(`/api/debug/${projectId}/status`);
    }

    async getDebugInfo(projectId) {
        return await this.request(`/api/debug/${projectId}/info`);
    }

    async getDebugTools(projectId) {
        return await this.request(`/api/debug/${projectId}/tools`);
    }

    async testTool(projectId, toolName, parameters) {
        return await this.request(`/api/debug/${projectId}/test`, {
            method: 'POST',
            body: JSON.stringify({
                tool_name: toolName,
                parameters
            })
        });
    }

    async executeTool(projectId, toolName, parameters) {
        return await this.request(`/api/debug/${projectId}/execute`, {
            method: 'POST',
            body: JSON.stringify({
                tool_name: toolName,
                parameters
            })
        });
    }

    /**
     * Deployment API
     */
    async deployService(projectId, deploymentConfig) {
        return await this.request(`/api/deploy/${projectId}`, {
            method: 'POST',
            body: JSON.stringify(deploymentConfig)
        });
    }

    async stopService(projectId) {
        return await this.request(`/api/deploy/${projectId}/stop`, {
            method: 'POST'
        });
    }

    async restartService(projectId) {
        return await this.request(`/api/deploy/${projectId}/restart`, {
            method: 'POST'
        });
    }

    async getDeploymentStatus(projectId) {
        return await this.request(`/api/deploy/${projectId}/status`);
    }

    async getServiceLogs(projectId, lines = 50) {
        return await this.request(`/api/deploy/${projectId}/logs?lines=${lines}`);
    }

    async getAvailablePorts() {
        return await this.request('/api/deploy/ports/available');
    }

    /**
     * WebSocket connections
     */
    createDebugWebSocket(projectId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/debug/${projectId}/ws`;
        
        const ws = new WebSocket(wsUrl);
        this.websockets.set(projectId, ws);
        
        return ws;
    }

    closeWebSocket(projectId) {
        const ws = this.websockets.get(projectId);
        if (ws) {
            ws.close();
            this.websockets.delete(projectId);
        }
    }

    closeAllWebSockets() {
        this.websockets.forEach((ws, projectId) => {
            ws.close();
        });
        this.websockets.clear();
    }
}

// Create global API instance
const api = new APIClient();

// Attach to window for global access
window.api = api;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
} 