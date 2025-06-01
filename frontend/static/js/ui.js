/**
 * UI Management for MCP Development Platform
 * Handles user interface interactions and state management
 */

class UIManager {
    constructor() {
        this.currentProject = null;
        this.debugSession = null;
        this.websocket = null;
        this.projects = new Map();
        
        this.initializeEventListeners();
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Modal events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideModals();
            }
        });

        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModals();
            }
        });

        // Connection status monitoring
        this.monitorConnection();
    }

    /**
     * Tab management
     */
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        if (!this.currentProject) return;

        switch (tabName) {
            case 'terminal':
                // Terminal is always ready - just ensure it's visible and load tools
                await this.loadTools();
                break;
            case 'deployment':
                await this.loadDeploymentStatus();
                await this.loadDeploymentLogs();
                break;
        }
    }

    /**
     * Project management
     */
    async loadProjects() {
        try {
            const projects = await api.listProjects();
            this.renderProjects(projects);
        } catch (error) {
            console.error('Failed to load projects:', error);
            this.showNotification('Failed to load projects', 'error');
        }
    }

    renderProjects(projects) {
        const container = document.getElementById('projectsContainer');
        
        if (!projects || projects.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-folder-open"></i>
                    <p>No projects yet</p>
                    <small>Create your first MCP project</small>
                </div>
            `;
            return;
        }

        container.innerHTML = projects.map(project => this.renderProjectCard(project)).join('');

        // Store projects for later use
        this.projects.clear();
        projects.forEach(project => {
            this.projects.set(project.id, project);
        });
        
        // Load file statistics for all projects
        this.loadProjectFileStats(projects);
    }

    renderProjectCard(project) {
        // Debug status indicator
        const debugStatus = project.debug_session_active ? 
            '<span class="debug-indicator">🔍 DEBUG</span>' : '';
        
        // Project status with debug indicator
        const statusDisplay = project.debug_session_active ? 
            'debugging' : project.status;
            
        // Additional debug CSS class for styling
        const debugClass = project.debug_session_active ? 'debugging' : '';
        
        return `
            <div class="project-card ${this.currentProject === project.id ? 'active' : ''} ${debugClass}" 
                 onclick="ui.selectProject('${project.id}')">
                <div class="project-name">
                    ${project.name} ${debugStatus}
                </div>
                <div class="project-status">${statusDisplay}</div>
                <small>${project.python_version} • <span id="file-count-${project.id}">Loading...</span> files</small>
            </div>
        `;
    }

    async selectProject(projectId) {
        try {
            this.currentProject = projectId;
            await this.loadProjectInfo(projectId);
            this.updateProjectUI();
            this.updateStatusBar();
            
            // Log project selection
            const project = this.projects.get(projectId);
            if (project) {
                this.addTerminalLog(`📂 Project selected: ${project.name}`, 'info');
                this.addTerminalLog(`📊 Python ${project.python_version} • Status: ${project.status}`, 'info');
            }

            // Load tools for the selected project
            await this.loadTools();
        } catch (error) {
            console.error('Error in selectProject:', error);
            // Still try to update the current project so file stats can load
            this.currentProject = projectId;
        }
        
        // Always try to load file stats for the selected project
        try {
            const project = this.projects.get(projectId);
            if (project) {
                await this.loadProjectFileStats([project]);
            }
        } catch (statsError) {
            console.error('Error loading file stats:', statsError);
        }
    }

    async loadProjectInfo(projectId) {
        try {
            const project = await api.getProject(projectId);
            this.projects.set(projectId, project);
            return project;
        } catch (error) {
            console.error('Failed to load project info:', error);
            return null;
        }
    }

    updateProjectUI() {
        try {
            const project = this.projects.get(this.currentProject);
            if (!project) return;

            // Show project actions for created projects
            const projectActions = document.getElementById('projectActions');
            if (projectActions && project.status === 'created') {
                projectActions.style.display = 'block';
            }

            // Update form fields
            const serviceName = document.getElementById('serviceName');
            if (serviceName) {
                serviceName.value = `mcp-${project.name}`;
            }

            // Update active state of project cards without re-rendering
            document.querySelectorAll('.project-card').forEach(card => {
                card.classList.remove('active');
            });
            
            // Add active class to selected project
            const selectedCard = document.querySelector(`[onclick*="${this.currentProject}"]`);
            if (selectedCard) {
                selectedCard.classList.add('active');
            }

            // Update debug button states
            this.updateDebugButtonStates();
        } catch (error) {
            console.error('Error in updateProjectUI:', error);
        }
    }

    updateDebugButtonStates() {
        if (!this.currentProject) return;
        
        const project = this.projects.get(this.currentProject);
        const isDebugging = project?.debug_session_active || false;
        
        // Update the single debug toggle button in debug controls
        const btn = document.getElementById('debugToggleBtn2');
        const text = document.getElementById('debugToggleText2');
        
        if (btn && text) {
            if (isDebugging) {
                btn.className = 'btn btn-danger';
                btn.querySelector('i').className = 'fas fa-stop';
                text.textContent = 'Stop Debug';
            } else {
                btn.className = 'btn btn-info';
                btn.querySelector('i').className = 'fas fa-bug';
                text.textContent = 'Start Debug';
            }
        }
    }

    /**
     * Debug session management
     */
    async loadDebugResources() {
        // This function is no longer needed since we removed the resources tab
        console.log('Resources tab has been removed');
    }

    async loadServiceLogs() {
        // This function has been moved to deployment logs
        return this.loadDeploymentLogs();
    }

    async loadDeploymentStatus() {
        if (!this.currentProject) return;

        try {
            const status = await api.getDeploymentStatus(this.currentProject);
            this.renderDeploymentStatus(status);
        } catch (error) {
            console.error('Failed to load deployment status:', error);
        }
    }

    renderDeploymentStatus(status) {
        const statusContent = document.querySelector('#deploymentStatus .status-content');

        if (!status.deployed) {
            statusContent.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-cloud"></i>
                    <p>Service not deployed</p>
                </div>
            `;
            return;
        }

        statusContent.innerHTML = `
            <div class="deployment-info">
                <div class="status-item">
                    <strong>Status:</strong> 
                    <span class="status-badge ${status.active ? 'active' : 'inactive'}">
                        ${status.active ? 'Active' : 'Inactive'}
                    </span>
                </div>
                <div class="status-item">
                    <strong>Service:</strong> ${status.service_name}
                </div>
                <div class="status-item">
                    <strong>Port:</strong> ${status.port}
                </div>
                <div class="status-item">
                    <strong>Access URL:</strong> 
                    <a href="${status.access_url}" target="_blank">${status.access_url}</a>
                </div>
                <div class="status-item">
                    <strong>Uptime:</strong> ${this.formatUptime(status.uptime)}
                </div>
                <div class="status-item">
                    <strong>Process ID:</strong> ${status.process_id || 'N/A'}
                </div>
                
                <!-- Service Control Buttons -->
                <div class="deployment-actions" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-muted);">
                    ${status.active ? `
                        <button class="btn btn-danger" onclick="stopService()" style="margin-right: 0.5rem;">
                            <i class="fas fa-stop"></i>
                            Stop Service
                        </button>
                        <button class="btn btn-warning" onclick="restartService()">
                            <i class="fas fa-redo"></i>
                            Restart Service
                        </button>
                    ` : `
                        <button class="btn btn-success" onclick="deployService()">
                            <i class="fas fa-play"></i>
                            Start Service
                        </button>
                    `}
                </div>
            </div>
        `;
        
        // Log deployment status to terminal
        if (status.active) {
            this.addTerminalLog(`🟢 Service is active on port ${status.port} (PID: ${status.process_id})`, 'success');
        } else {
            this.addTerminalLog(`🔴 Service is inactive`, 'warning');
        }
    }

    async loadDeploymentLogs() {
        if (!this.currentProject) return;

        try {
            const response = await api.getServiceLogs(this.currentProject);
            const logs = response.logs || [];
            this.renderDeploymentLogs(logs);
            
            // Also log deployment logs to terminal
            if (logs.length > 0) {
                this.addTerminalLog(`📋 Loaded ${logs.length} deployment log entries`, 'info');
                // Log the most recent entries to terminal
                logs.slice(-3).forEach(log => {
                    this.addTerminalLog(`[DEPLOY] ${log.message}`, log.level.toLowerCase());
                });
            }
        } catch (error) {
            console.error('Failed to load deployment logs:', error);
            this.addTerminalLog(`❌ Failed to load deployment logs: ${error.message}`, 'error');
            const logsContent = document.getElementById('deploymentLogsContent');
            if (logsContent) {
                logsContent.innerHTML = `
                    <div class="no-data">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load logs: ${error.message}</p>
                    </div>
                `;
            }
        }
    }

    renderDeploymentLogs(logs) {
        const logsContent = document.getElementById('deploymentLogsContent');
        if (!logsContent) return;

        if (!logs || logs.length === 0) {
            logsContent.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-file-text"></i>
                    <p>No deployment logs available</p>
                </div>
            `;
            return;
        }

        logsContent.innerHTML = logs.map(log => `
            <div class="log-entry ${log.level.toLowerCase()}">
                <span class="timestamp">${log.timestamp}</span>
                <span class="level ${log.level.toLowerCase()}">${log.level}</span>
                <span class="message">${log.message}</span>
            </div>
        `).join('');
    }

    async refreshDeploymentLogs() {
        await this.loadDeploymentLogs();
        this.showNotification('Deployment logs refreshed', 'info');
    }

    clearDeploymentLogs() {
        const logsContent = document.getElementById('deploymentLogsContent');
        if (logsContent) {
            logsContent.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-file-text"></i>
                    <p>Deployment logs cleared</p>
                </div>
            `;
        }
    }

    /**
     * Modal management
     */
    showCreateProjectModal() {
        document.getElementById('createProjectModal').classList.add('show');
    }

    hideCreateProjectModal() {
        document.getElementById('createProjectModal').classList.remove('show');
        this.clearModalForm();
    }

    hideModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
        this.clearModalForm();
    }

    clearModalForm() {
        document.getElementById('modalProjectName').value = '';
        document.getElementById('modalProjectDescription').value = '';
        document.getElementById('modalPythonVersion').value = '3.11';
    }

    /**
     * Notification system
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;

        container.appendChild(notification);

        // Auto-remove notification
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);

        // Remove on click
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Status bar updates
     */
    updateStatusBar() {
        const project = this.projects.get(this.currentProject);
        
        document.getElementById('currentProject').textContent = 
            project ? project.name : 'No project selected';
        
        // Enhanced debug status with visual indicator
        const debugStatusElement = document.getElementById('debugStatus');
        if (project?.debug_session_active) {
            debugStatusElement.innerHTML = '🔍 <span style="color: var(--accent-info); font-weight: bold;">Debug: Active</span>';
        } else {
            debugStatusElement.textContent = 'Debug: Inactive';
        }
        
        document.getElementById('deploymentStatusFooter').textContent = 
            project?.deployment_active ? 'Deployment: Active' : 'Deployment: None';
    }

    /**
     * Connection monitoring
     */
    async monitorConnection() {
        const statusIndicator = document.getElementById('connectionStatus');
        
        try {
            const health = await api.healthCheck();
            if (health && health.status === 'healthy') {
                statusIndicator.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
                statusIndicator.className = 'status-indicator';
            } else {
                throw new Error('Unhealthy');
            }
        } catch (error) {
            statusIndicator.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
            statusIndicator.className = 'status-indicator error';
        }

        // Check again in 30 seconds
        setTimeout(() => this.monitorConnection(), 30000);
    }

    /**
     * Utility methods
     */
    formatUptime(seconds) {
        if (!seconds) return 'N/A';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${hours}h ${minutes}m ${secs}s`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    setLoading(element, loading = true) {
        if (loading) {
            element.classList.add('loading');
        } else {
            element.classList.remove('loading');
        }
    }

    async loadProjectFileStats(projects) {
        for (const project of projects) {
            try {
                const stats = await api.getProjectStats(project.id);
                const fileCountElement = document.getElementById(`file-count-${project.id}`);
                if (fileCountElement) {
                    fileCountElement.textContent = stats.total_files;
                }
            } catch (error) {
                console.error('Error getting stats for project:', project.id, error);
                const fileCountElement = document.getElementById(`file-count-${project.id}`);
                if (fileCountElement) {
                    fileCountElement.textContent = '?';
                }
            }
        }
    }

    /**
     * Terminal management
     */
    addTerminalLog(message, level = 'info') {
        const terminalContent = document.getElementById('terminalContent');
        if (!terminalContent) return;

        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
        const logLine = document.createElement('div');
        logLine.className = 'terminal-line';
        
        logLine.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="level ${level}">${level.toUpperCase()}</span>
            <span class="message">${message}</span>
        `;

        terminalContent.appendChild(logLine);
        
        // Auto-scroll to bottom
        terminalContent.scrollTop = terminalContent.scrollHeight;
        
        // Keep terminal history manageable (max 1000 lines)
        const lines = terminalContent.children;
        if (lines.length > 1000) {
            terminalContent.removeChild(lines[0]);
        }
    }

    clearTerminal() {
        const terminalContent = document.getElementById('terminalContent');
        if (!terminalContent) return;

        terminalContent.innerHTML = `
            <div class="terminal-line startup">
                <span class="timestamp">[${new Date().toLocaleTimeString('en-US', { hour12: false })}]</span>
                <span class="level info">INFO</span>
                <span class="message">🧹 Terminal cleared</span>
            </div>
        `;
    }

    scrollToBottom() {
        const terminalContent = document.getElementById('terminalContent');
        if (terminalContent) {
            terminalContent.scrollTop = terminalContent.scrollHeight;
        }
    }

    /**
     * Project activity logging
     */
    logProjectCreated(projectName) {
        this.addTerminalLog(`✨ Project created: ${projectName}`, 'success');
    }

    logDependencyInstallStart(projectName) {
        this.addTerminalLog(`⬇️ Installing dependencies for: ${projectName}`, 'info');
    }

    logDependencyInstallComplete(projectName) {
        this.addTerminalLog(`✅ Dependencies installed successfully for: ${projectName}`, 'success');
    }

    logDependencyInstallError(projectName, error) {
        this.addTerminalLog(`❌ Dependency installation failed for: ${projectName} - ${error}`, 'error');
    }

    logDebugStart(projectName) {
        this.addTerminalLog(`🔍 Debug session started for: ${projectName}`, 'info');
    }

    logDebugStop(projectName) {
        this.addTerminalLog(`⏹️ Debug session stopped for: ${projectName}`, 'warning');
    }

    logToolsDiscovered(projectName, toolCount) {
        this.addTerminalLog(`🔧 Discovered ${toolCount} MCP tools in: ${projectName}`, 'success');
    }

    logDeploymentStart(projectName, serviceName) {
        this.addTerminalLog(`🚀 Deploying service: ${serviceName} for project: ${projectName}`, 'info');
    }

    logDeploymentComplete(projectName, serviceName, url) {
        this.addTerminalLog(`✅ Service deployed: ${serviceName} at ${url}`, 'success');
    }

    logDeploymentError(projectName, error) {
        this.addTerminalLog(`❌ Deployment failed for: ${projectName} - ${error}`, 'error');
    }

    logProjectImported(projectName, fileCount) {
        this.addTerminalLog(`📥 Project imported: ${projectName} (${fileCount} files)`, 'success');
    }

    logError(message) {
        this.addTerminalLog(`⚠️ ${message}`, 'error');
    }

    logInfo(message) {
        this.addTerminalLog(`ℹ️ ${message}`, 'info');
    }

    /**
     * Tool testing functionality
     */
    async loadTools() {
        if (!this.currentProject) {
            this.addTerminalLog('⚠️ No project selected for tool testing', 'warning');
            return;
        }

        try {
            this.addTerminalLog('🔍 Loading available tools...', 'info');
            
            // Get tools from debug session if active
            const debugResponse = await api.getDebugTools(this.currentProject);
            if (debugResponse && debugResponse.tools && debugResponse.tools.length > 0) {
                this.populateToolSelect(debugResponse.tools);
                this.addTerminalLog(`🔧 Loaded ${debugResponse.tools.length} tools for testing`, 'success');
            } else {
                this.addTerminalLog('📭 No tools discovered in this project', 'warning');
                this.clearToolSelect();
            }
        } catch (error) {
            console.error('Failed to load tools:', error);
            this.addTerminalLog(`❌ Failed to load tools: ${error.message}`, 'error');
            this.clearToolSelect();
        }
    }

    populateToolSelect(tools) {
        const toolSelect = document.getElementById('toolSelect');
        if (!toolSelect) return;

        // Clear existing options except the first one
        toolSelect.innerHTML = '<option value="">Select a tool to test...</option>';

        // Add tool options
        tools.forEach(tool => {
            const option = document.createElement('option');
            option.value = tool.name;
            option.textContent = `${tool.name} - ${tool.description || 'No description'}`;
            option.dataset.schema = JSON.stringify(tool.inputSchema || {});
            toolSelect.appendChild(option);
        });

        // Enable the test button when a tool is selected
        const testToolBtn = document.getElementById('testToolBtn');
        if (testToolBtn) {
            testToolBtn.disabled = false;
        }
    }

    clearToolSelect() {
        const toolSelect = document.getElementById('toolSelect');
        if (toolSelect) {
            toolSelect.innerHTML = '<option value="">No tools available</option>';
        }

        const testToolBtn = document.getElementById('testToolBtn');
        if (testToolBtn) {
            testToolBtn.disabled = true;
        }

        const toolParams = document.getElementById('toolParams');
        if (toolParams) {
            toolParams.value = '';
        }
    }

    updateToolParams() {
        const toolSelect = document.getElementById('toolSelect');
        const toolParams = document.getElementById('toolParams');
        
        if (!toolSelect || !toolParams) return;

        const selectedOption = toolSelect.options[toolSelect.selectedIndex];
        if (selectedOption && selectedOption.dataset.schema) {
            try {
                const schema = JSON.parse(selectedOption.dataset.schema);
                if (schema.properties) {
                    // Generate example parameters based on schema
                    const exampleParams = {};
                    Object.keys(schema.properties).forEach(prop => {
                        const propSchema = schema.properties[prop];
                        exampleParams[prop] = this.getExampleValue(propSchema);
                    });
                    toolParams.value = JSON.stringify(exampleParams, null, 2);
                } else {
                    toolParams.value = '{}';
                }
            } catch (error) {
                toolParams.value = '{}';
            }
        } else {
            toolParams.value = '';
        }
    }

    getExampleValue(schema) {
        switch (schema.type) {
            case 'string':
                return schema.example || 'example_string';
            case 'number':
            case 'integer':
                return schema.example || 42;
            case 'boolean':
                return schema.example !== undefined ? schema.example : true;
            case 'array':
                return schema.example || [];
            case 'object':
                return schema.example || {};
            default:
                return schema.example || 'example_value';
        }
    }

    async testTool() {
        const toolSelect = document.getElementById('toolSelect');
        const toolParams = document.getElementById('toolParams');
        const testResults = document.getElementById('testResults');

        if (!toolSelect || !toolParams || !testResults) return;

        const toolName = toolSelect.value;
        if (!toolName) {
            this.addTerminalLog('⚠️ Please select a tool to test', 'warning');
            return;
        }

        let params = {};
        try {
            if (toolParams.value.trim()) {
                params = JSON.parse(toolParams.value);
            }
        } catch (error) {
            this.addTerminalLog(`❌ Invalid JSON parameters: ${error.message}`, 'error');
            return;
        }

        if (!this.currentProject) {
            this.addTerminalLog('⚠️ No project selected for tool testing', 'warning');
            return;
        }

        try {
            this.addTerminalLog(`🧪 Testing tool: ${toolName}`, 'info');
            this.addTerminalLog(`📋 Parameters: ${JSON.stringify(params, null, 2)}`, 'info');
            this.addTerminalLog(`🚀 Starting MCP server process...`, 'info');
            
            // Show loading state
            testResults.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                    <i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; margin-bottom: 1rem;"></i>
                    <p>Testing tool via MCP protocol...</p>
                    <small>Check terminal for detailed logs</small>
                </div>
            `;

            const response = await api.testTool(this.currentProject, toolName, params);
            
            // Log detailed information about the response
            this.addTerminalLog(`📥 Tool test completed`, 'info');
            
            if (response.success) {
                this.addTerminalLog(`✅ Tool test successful: ${toolName}`, 'success');
                
                // Log detailed result information
                if (response.result && typeof response.result === 'object') {
                    if (response.result.execution_method) {
                        this.addTerminalLog(`🔧 Execution method: ${response.result.execution_method}`, 'info');
                    }
                    if (response.result.mcp_server_stderr) {
                        this.addTerminalLog(`📝 MCP Server output:`, 'info');
                        response.result.mcp_server_stderr.split('\n').forEach(line => {
                            if (line.trim()) {
                                this.addTerminalLog(`   ${line}`, 'info');
                            }
                        });
                    }
                    if (response.result.result) {
                        this.addTerminalLog(`🎯 Tool result: ${JSON.stringify(response.result.result, null, 2)}`, 'success');
                    }
                } else {
                    this.addTerminalLog(`🎯 Tool result: ${JSON.stringify(response.result, null, 2)}`, 'success');
                }
                
                this.displayTestResults(response.result, 'success');
            } else {
                this.addTerminalLog(`❌ Tool test failed: ${toolName} - ${response.error}`, 'error');
                this.displayTestResults(response.error, 'error');
            }
        } catch (error) {
            console.error('Tool test failed:', error);
            this.addTerminalLog(`❌ Tool test error: ${toolName} - ${error.message}`, 'error');
            this.addTerminalLog(`📋 Error details: ${error.stack || 'No stack trace available'}`, 'error');
            this.displayTestResults(error.message, 'error');
        }
    }

    displayTestResults(result, type = 'success') {
        const testResults = document.getElementById('testResults');
        if (!testResults) return;

        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        const color = type === 'success' ? '#4CAF50' : '#F44336';

        testResults.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; color: ${color};">
                <i class="fas ${icon}"></i>
                <strong>${type === 'success' ? 'Success' : 'Error'}</strong>
                <span style="color: var(--text-muted); font-size: 0.8rem;">[${timestamp}]</span>
            </div>
            <pre style="white-space: pre-wrap; font-family: var(--font-mono); font-size: 0.8rem; line-height: 1.4; color: var(--text-primary); margin: 0;">${typeof result === 'object' ? JSON.stringify(result, null, 2) : result}</pre>
        `;
    }
}

// Global UI manager instance
const ui = new UIManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
}

// Attach to window for global access
window.ui = ui; 