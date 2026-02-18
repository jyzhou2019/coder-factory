/**
 * API Client for Coder-Factory
 */

const API_BASE = '/api';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
    }

    async request(method, path, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${this.baseUrl}${path}`, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || 'Request failed');
        }

        return response.json();
    }

    get(path) {
        return this.request('GET', path);
    }

    post(path, data) {
        return this.request('POST', path, data);
    }

    put(path, data) {
        return this.request('PUT', path, data);
    }

    patch(path, data) {
        return this.request('PATCH', path, data);
    }

    delete(path) {
        return this.request('DELETE', path);
    }

    // Requirements API
    async submitRequirement(text, sessionId = null) {
        return this.post('/requirements', { text, session_id: sessionId });
    }

    async getRequirement(sessionId) {
        return this.get(`/requirements/${sessionId}`);
    }

    async getRequirementTasks(sessionId) {
        return this.get(`/requirements/${sessionId}/tasks`);
    }

    // Dialog API
    async getDialogStatus(sessionId) {
        return this.get(`/dialog/${sessionId}/status`);
    }

    async getCurrentQuestion(sessionId) {
        return this.get(`/dialog/${sessionId}/question`);
    }

    async answerQuestion(sessionId, answer) {
        return this.post(`/dialog/${sessionId}/answer`, { answer });
    }

    async approveRequirement(sessionId) {
        return this.post(`/dialog/${sessionId}/approve`);
    }

    async modifyRequirement(sessionId, field, value, reason = '') {
        return this.post(`/dialog/${sessionId}/modify`, { field, value, reason });
    }

    async cancelDialog(sessionId, reason = '') {
        return this.post(`/dialog/${sessionId}/cancel`, { reason });
    }

    async getDialogHistory(sessionId) {
        return this.get(`/dialog/${sessionId}/history`);
    }

    // Architecture API
    async designArchitecture(sessionId) {
        return this.post('/architecture/design', null, {
            params: { session_id: sessionId }
        });
    }

    async getArchitecture(sessionId) {
        // Using query param
        const response = await fetch(`${this.baseUrl}/architecture/${sessionId}`);
        return response.json();
    }

    async getTechInfo() {
        return this.get('/architecture/tech-info');
    }

    // Codegen API
    async startCodegen(sessionId) {
        const response = await fetch(`${this.baseUrl}/codegen/generate?session_id=${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return response.json();
    }

    async getCodegenJob(jobId) {
        return this.get(`/codegen/jobs/${jobId}`);
    }

    async listCodegenJobs(sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.get(`/codegen/jobs${params}`);
    }

    async cancelCodegenJob(jobId) {
        return this.post(`/codegen/jobs/${jobId}/cancel`);
    }

    // Deployment API
    async generateDeployConfig(sessionId, method = 'docker') {
        const response = await fetch(`${this.baseUrl}/deployment/generate?session_id=${sessionId}&method=${method}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return response.json();
    }

    async buildDocker(sessionId, tag = null) {
        return this.post('/deployment/build', { session_id: sessionId, tag });
    }

    async deploy(sessionId, method = 'docker') {
        const response = await fetch(`${this.baseUrl}/deployment/deploy?session_id=${sessionId}&method=${method}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return response.json();
    }

    async getDeploymentStatus(deploymentId) {
        return this.get(`/deployment/status/${deploymentId}`);
    }

    // Delivery API
    async getDeliveryChecklist(sessionId) {
        const response = await fetch(`${this.baseUrl}/delivery/checklist?session_id=${sessionId}`);
        return response.json();
    }

    async generateDocs(sessionId, types = null) {
        return this.post('/delivery/docs', { session_id: sessionId, types });
    }

    async prepareRelease(sessionId, version = null, changelog = null) {
        return this.post('/delivery/release', { session_id: sessionId, version, changelog });
    }

    async listDeliveredProjects() {
        return this.get('/delivery/projects');
    }

    // Tasks API
    async listTasks(sessionId = null, status = null, limit = 100) {
        const params = new URLSearchParams();
        if (sessionId) params.append('session_id', sessionId);
        if (status) params.append('status', status);
        params.append('limit', limit);
        return this.get(`/tasks?${params}`);
    }

    async getRunningTasks() {
        return this.get('/tasks/running');
    }

    async getTaskStats() {
        return this.get('/tasks/stats');
    }

    async getTask(taskId) {
        return this.get(`/tasks/${taskId}`);
    }

    async updateTask(taskId, status = null, progress = null) {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (progress !== null) params.append('progress', progress);
        const response = await fetch(`${this.baseUrl}/tasks/${taskId}?${params}`, {
            method: 'PATCH'
        });
        return response.json();
    }

    // Stats
    async getStats() {
        return this.get('/stats');
    }

    async healthCheck() {
        return this.get('/health');
    }
}

// Global API client
const api = new ApiClient();
