/**
 * Main Application Controller for MCP Development Platform
 * Coordinates API client and UI manager, handles all user interactions
 */

class MCPDevApp {
    constructor() {
        this.currentProject = null;
        this.debugWebSocket = null;
    }

    async init() {
        // Get fresh references to global objects
        this.api = window.api;
        this.ui = window.ui;
        
        // Load initial data
        await this.loadProjects();
        
        // Setup periodic updates
        this.setupPeriodicUpdates();
    }

    async loadProjects() {
        await this.ui.loadProjects();
    }

    /**
     * Project Management Functions
     */
    async createProject() {
        const name = document.getElementById('modalProjectName').value.trim();
        const description = document.getElementById('modalProjectDescription').value.trim();
        const pythonVersion = document.getElementById('modalPythonVersion').value;

        if (!name) {
            this.ui.showNotification('Project name is required', 'warning');
            return;
        }

        try {
            this.ui.showNotification('Creating project...', 'info');
            this.ui.logInfo(`Creating project: ${name} (Python ${pythonVersion})`);
            
            const project = await this.api.createProject({
                name,
                description: description || null,
                python_version: pythonVersion
            });

            this.ui.showNotification(`Project "${name}" created successfully`, 'success');
            this.ui.logProjectCreated(name);
            this.ui.hideCreateProjectModal();
            
            // Reload projects and select the new one
            await this.loadProjects();
            await this.ui.selectProject(project.id);
            
        } catch (error) {
            this.ui.showNotification(`Failed to create project: ${error.message}`, 'error');
            this.ui.logError(`Failed to create project: ${error.message}`);
        }
    }

    async installDependencies() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        try {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            this.ui.showNotification('Installing dependencies...', 'info');
            this.ui.logDependencyInstallStart(projectName);
            
            await this.api.installDependencies(this.ui.currentProject);
            this.ui.showNotification('Dependencies installed successfully', 'success');
            this.ui.logDependencyInstallComplete(projectName);
            
            // Refresh project info
            await this.ui.loadProjectInfo(this.ui.currentProject);
            
        } catch (error) {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            this.ui.showNotification(`Failed to install dependencies: ${error.message}`, 'error');
            this.ui.logDependencyInstallError(projectName, error.message);
        }
    }

    /**
     * Debug Session Functions
     */
    async toggleDebugSession() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        try {
            // Get current project state
            const project = this.ui.projects.get(this.ui.currentProject);
            const isDebugging = project?.debug_session_active || false;
            
            if (isDebugging) {
                await this.stopDebugSession();
            } else {
                await this.startDebugSession();
            }
            
            // Update button states after action
            this.ui.updateDebugButtonStates();
            
        } catch (error) {
            console.error('Error toggling debug session:', error);
            this.ui.showNotification(`Debug toggle failed: ${error.message}`, 'error');
        }
    }

    async startDebugSession() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        try {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            this.ui.showNotification('Starting debug session...', 'info');
            this.ui.logDebugStart(projectName);
            
            await this.api.startDebugSession(this.ui.currentProject);
            this.ui.showNotification('Debug session started', 'success');
            
            // Setup WebSocket connection for real-time communication
            this.setupDebugWebSocket();
            
            // Refresh project info and update status
            await this.ui.loadProjectInfo(this.ui.currentProject);
            this.ui.updateStatusBar();
            
            // Get debug info to log tools discovered
            try {
                const debugInfo = await this.api.getDebugInfo(this.ui.currentProject);
                if (debugInfo && debugInfo.tools) {
                    this.ui.logToolsDiscovered(projectName, debugInfo.tools.length);
                }
            } catch (debugError) {
                console.error('Failed to get debug info:', debugError);
            }
            
            // Reload projects to update debug indicators
            await this.ui.loadProjects();
            
        } catch (error) {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            this.ui.showNotification(`Failed to start debug session: ${error.message}`, 'error');
            this.ui.logError(`Failed to start debug session for ${projectName}: ${error.message}`);
        }
    }

    async stopDebugSession() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        try {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            await this.api.stopDebugSession(this.ui.currentProject);
            this.ui.showNotification('Debug session stopped', 'success');
            this.ui.logDebugStop(projectName);
            
            // Close WebSocket connection
            if (this.debugWebSocket) {
                this.debugWebSocket.close();
                this.debugWebSocket = null;
            }
            
            // Refresh project info
            await this.ui.loadProjectInfo(this.ui.currentProject);
            this.ui.updateStatusBar();
            
            // Reload projects to update debug indicators
            await this.ui.loadProjects();
            
        } catch (error) {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            this.ui.showNotification(`Failed to stop debug session: ${error.message}`, 'error');
            this.ui.logError(`Failed to stop debug session for ${projectName}: ${error.message}`);
        }
    }

    setupDebugWebSocket() {
        if (this.debugWebSocket) {
            this.debugWebSocket.close();
        }

        try {
            this.debugWebSocket = this.api.createDebugWebSocket(this.ui.currentProject);
            
            this.debugWebSocket.onopen = () => {
                console.log('🔌 Debug WebSocket connected');
            };
            
            this.debugWebSocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleDebugMessage(message);
            };
            
            this.debugWebSocket.onclose = () => {
                console.log('🔌 Debug WebSocket disconnected');
                this.debugWebSocket = null;
            };
            
            this.debugWebSocket.onerror = (error) => {
                console.error('🔌 Debug WebSocket error:', error);
                this.ui.showNotification('Debug WebSocket connection failed', 'error');
            };
            
        } catch (error) {
            console.error('Failed to setup debug WebSocket:', error);
        }
    }

    handleDebugMessage(message) {
        // Simplified debug message handling - log to terminal instead
        switch (message.type) {
            case 'tool_response':
                this.ui.logInfo(`Tool response received: ${message.data?.tool || 'Unknown'}`);
                break;
            case 'tools_list':
                if (message.data && message.data.length > 0) {
                    this.ui.logInfo(`${message.data.length} tools available for debugging`);
                }
                break;
            default:
                console.log('Unknown debug message:', message);
        }
    }

    async executeTool() {
        const toolName = document.getElementById('toolSelect').value;
        const parametersText = document.getElementById('toolParameters').value.trim();

        if (!toolName) {
            this.ui.showNotification('Please select a tool', 'warning');
            return;
        }

        let parameters = {};
        if (parametersText) {
            try {
                parameters = JSON.parse(parametersText);
            } catch (error) {
                this.ui.showNotification('Invalid JSON parameters', 'error');
                return;
            }
        }

        try {
            this.ui.showNotification('Executing tool...', 'info');
            
            const response = await this.api.executeTool(this.ui.currentProject, toolName, parameters);
            this.displayToolResponse(response);
            
        } catch (error) {
            this.ui.showNotification(`Failed to execute tool: ${error.message}`, 'error');
        }
    }

    displayToolResponse(response) {
        const resultsContent = document.querySelector('#testResults .results-content');
        
        const timestamp = new Date().toLocaleTimeString();
        const statusClass = response.success ? 'success' : 'error';
        
        const resultHtml = `
            <div class="tool-result ${statusClass}">
                <div class="result-header">
                    <strong>${response.success ? '✅' : '❌'} Tool Execution</strong>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="result-timing">
                    Execution time: ${response.execution_time.toFixed(3)}s
                </div>
                ${response.success ? `
                    <div class="result-data">
                        <pre>${JSON.stringify(response.result, null, 2)}</pre>
                    </div>
                ` : `
                    <div class="result-error">
                        <strong>Error:</strong> ${response.error}
                    </div>
                `}
            </div>
        `;
        
        resultsContent.innerHTML = resultHtml;
    }

    async refreshDebugInfo() {
        if (!this.ui.currentProject) return;
        
        // Get debug status and log it
        try {
            const debugInfo = await this.api.getDebugInfo(this.ui.currentProject);
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            if (debugInfo && debugInfo.tools) {
                this.ui.logInfo(`Debug info refreshed - ${debugInfo.tools.length} tools available in ${projectName}`);
            }
        } catch (error) {
            this.ui.logError(`Failed to refresh debug info: ${error.message}`);
        }
        
        this.ui.showNotification('Debug info refreshed', 'info');
    }

    /**
     * Deployment Functions
     */
    async deployService() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        const serviceName = document.getElementById('serviceName').value.trim();
        const port = parseInt(document.getElementById('servicePort').value) || 3000;
        const autoStart = document.getElementById('autoStart').checked;
        const enableLogging = document.getElementById('enableLogging').checked;

        if (!serviceName) {
            this.ui.showNotification('Service name is required', 'warning');
            this.ui.addTerminalLog('⚠️ Service name is required for deployment', 'warning');
            return;
        }

        try {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            this.ui.showNotification('Deploying service...', 'info');
            this.ui.logDeploymentStart(projectName, serviceName);
            this.ui.addTerminalLog(`🚀 Starting deployment of ${serviceName} on port ${port}...`, 'info');
            
            const result = await this.api.deployService(this.ui.currentProject, {
                service_name: serviceName,
                port: port,
                auto_start: autoStart,
                enable_logging: enableLogging
            });

            this.ui.showNotification(`Service deployed successfully on port ${result.port}`, 'success');
            this.ui.logDeploymentComplete(projectName, serviceName, `http://localhost:${result.port}`);
            this.ui.addTerminalLog(`✅ Service deployed successfully!`, 'success');
            this.ui.addTerminalLog(`🌐 Access URL: ${result.access_url}`, 'info');
            this.ui.addTerminalLog(`🔧 Process ID: ${result.process_id}`, 'info');
            
            // Refresh project info and deployment status
            await this.ui.loadProjectInfo(this.ui.currentProject);
            await this.ui.loadDeploymentStatus();
            await this.ui.loadDeploymentLogs();
            this.ui.updateStatusBar();
            
        } catch (error) {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            this.ui.showNotification(`Failed to deploy service: ${error.message}`, 'error');
            this.ui.logDeploymentError(projectName, error.message);
            this.ui.addTerminalLog(`❌ Deployment failed: ${error.message}`, 'error');
        }
    }

    async stopService() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        try {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            this.ui.addTerminalLog(`⏹️ Stopping service for ${projectName}...`, 'info');
            
            await this.api.stopService(this.ui.currentProject);
            this.ui.showNotification('Service stopped successfully', 'success');
            this.ui.addTerminalLog(`✅ Service stopped successfully`, 'success');
            
            // Refresh project info and deployment status
            await this.ui.loadProjectInfo(this.ui.currentProject);
            await this.ui.loadDeploymentStatus();
            await this.ui.loadDeploymentLogs();
            this.ui.updateStatusBar();
            
        } catch (error) {
            this.ui.showNotification(`Failed to stop service: ${error.message}`, 'error');
            this.ui.addTerminalLog(`❌ Failed to stop service: ${error.message}`, 'error');
        }
    }

    async restartService() {
        if (!this.ui.currentProject) {
            this.ui.showNotification('Please select a project first', 'warning');
            return;
        }

        try {
            const project = this.ui.projects.get(this.ui.currentProject);
            const projectName = project ? project.name : 'Unknown';
            
            this.ui.addTerminalLog(`🔄 Restarting service for ${projectName}...`, 'info');
            
            await this.api.restartService(this.ui.currentProject);
            this.ui.showNotification('Service restarted successfully', 'success');
            this.ui.addTerminalLog(`✅ Service restarted successfully`, 'success');
            
            // Refresh deployment status
            await this.ui.loadDeploymentStatus();
            await this.ui.loadDeploymentLogs();
            
        } catch (error) {
            this.ui.showNotification(`Failed to restart service: ${error.message}`, 'error');
            this.ui.addTerminalLog(`❌ Failed to restart service: ${error.message}`, 'error');
        }
    }

    /**
     * Utility Functions
     */
    async refreshLogs() {
        await this.ui.loadDeploymentLogs();
        this.ui.showNotification('Deployment logs refreshed', 'info');
    }

    clearLogs() {
        this.ui.clearDeploymentLogs();
    }

    setupPeriodicUpdates() {
        // Update connection status every 30 seconds
        setInterval(async () => {
            await this.ui.monitorConnection();
        }, 30000);

        // Refresh current project info every 60 seconds
        setInterval(async () => {
            if (this.ui.currentProject) {
                await this.ui.loadProjectInfo(this.ui.currentProject);
            }
        }, 60000);
    }
}

// Global functions for HTML onclick handlers
function showCreateProjectModal() {
    ui.showCreateProjectModal();
}

function hideCreateProjectModal() {
    ui.hideCreateProjectModal();
}

function createProject() {
    app.createProject();
}

function installDependencies() {
    app.installDependencies();
}

function toggleDebugSession() {
    app.toggleDebugSession();
}

function startDebugSession() {
    app.startDebugSession();
}

function stopDebugSession() {
    app.stopDebugSession();
}

// function executeTool() {
//     app.executeTool();
// }

function refreshDebugInfo() {
    app.refreshDebugInfo();
}

function deployService() {
    app.deployService();
}

function stopService() {
    app.stopService();
}

function restartService() {
    app.restartService();
}

function refreshLogs() {
    app.refreshLogs();
}

function clearLogs() {
    app.clearLogs();
}

function refreshDeploymentLogs() {
    ui.refreshDeploymentLogs();
}

function clearDeploymentLogs() {
    ui.clearDeploymentLogs();
}

function switchTab(tabName) {
    ui.switchTab(tabName);
}

function clearTerminal() {
    ui.clearTerminal();
}

// Tool testing functions
function updateToolParams() {
    ui.updateToolParams();
}

function testTool() {
    ui.testTool();
}

function scrollToBottom() {
    ui.scrollToBottom();
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    window.app = new MCPDevApp();
    await window.app.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MCPDevApp;
} 