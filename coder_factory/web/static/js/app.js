/**
 * Main Application for Coder-Factory Web Interface
 * Uses Alpine.js-style reactive state management
 */

document.addEventListener('DOMContentLoaded', () => {
    // Create reactive app state
    window.app = {
        // Navigation
        currentPage: 'dashboard',

        // Connection state
        wsConnected: false,

        // Dashboard stats
        stats: {
            activeSessions: 0,
            runningTasks: 0,
            completedTasks: 0,
            deliveredProjects: 0,
        },

        // Requirement state
        requirementText: '',
        submitting: false,
        parsedResult: null,
        currentSessionId: null,

        // Dialog state
        dialogState: 'idle',
        dialogProgress: 0,
        dialogHistory: [],
        currentQuestion: null,
        textInput: '',

        // Architecture state
        architecture: null,

        // Tasks state
        tasks: [],
        taskStats: { by_status: {}, by_priority: {}, by_type: {} },
        taskFilter: '',
        runningTasks: [],

        // Delivery state
        deliveryChecklist: [],
        deliveredProjects: [],

        // Notifications
        notification: {
            show: false,
            message: '',
            type: 'info',
        },

        // Initialize
        async init() {
            // Setup WebSocket
            wsClient.onStateChange = (connected) => {
                this.wsConnected = connected;
            };
            wsClient.connect();

            // Setup WebSocket listeners
            wsClient.on('*', (message) => this.handleWsMessage(message));

            // Load initial data
            await this.loadStats();
            await this.loadTasks();
            await this.loadDeliveredProjects();

            // Auto-refresh stats
            setInterval(() => this.loadStats(), 30000);
        },

        // WebSocket message handler
        handleWsMessage(message) {
            switch (message.type) {
                case 'dialog_update':
                    this.dialogState = message.state;
                    this.loadCurrentQuestion();
                    break;

                case 'task_update':
                    this.loadTasks();
                    break;

                case 'codegen_progress':
                    this.loadTasks();
                    break;

                case 'deployment_status':
                    this.showNotification(`部署状态: ${message.status}`, 'info');
                    break;

                case 'system':
                    this.showNotification(message.message, message.level);
                    break;
            }
        },

        // Notification
        showNotification(message, type = 'info') {
            this.notification = { show: true, message, type };
            setTimeout(() => {
                this.notification.show = false;
            }, 3000);
        },

        // Stats
        async loadStats() {
            try {
                const data = await api.getStats();
                this.stats = {
                    activeSessions: data.active_sessions || 0,
                    runningTasks: data.running_tasks || 0,
                    completedTasks: data.completed_tasks || 0,
                    deliveredProjects: data.delivered_projects || 0,
                };
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        },

        // Requirements
        async submitRequirement() {
            if (!this.requirementText.trim()) return;

            this.submitting = true;
            try {
                const result = await api.submitRequirement(this.requirementText);
                if (result.success) {
                    this.parsedResult = result;
                    this.currentSessionId = result.session_id;
                    this.showNotification('需求解析成功', 'success');

                    // Connect WebSocket to session
                    wsClient.connect(this.currentSessionId);
                } else {
                    this.showNotification(result.error || '解析失败', 'error');
                }
            } catch (error) {
                this.showNotification(error.message, 'error');
            } finally {
                this.submitting = false;
            }
        },

        // Dialog
        async startDialog() {
            if (!this.currentSessionId) return;

            this.currentPage = 'dialog';
            await this.loadDialogStatus();
            await this.loadCurrentQuestion();
        },

        async loadDialogStatus() {
            if (!this.currentSessionId) return;

            try {
                const data = await api.getDialogStatus(this.currentSessionId);
                this.dialogState = data.state;

                // Calculate progress
                const summary = data.dialog_summary || {};
                const total = summary.total_questions || 0;
                const answered = summary.answered_questions || 0;
                this.dialogProgress = total > 0 ? Math.round((answered / total) * 100) : 0;

                // Load history
                const history = await api.getDialogHistory(this.currentSessionId);
                this.dialogHistory = history.history || [];
            } catch (error) {
                console.error('Failed to load dialog status:', error);
            }
        },

        async loadCurrentQuestion() {
            if (!this.currentSessionId) return;

            try {
                const data = await api.getCurrentQuestion(this.currentSessionId);
                if (data.has_question) {
                    this.currentQuestion = data.question;
                } else {
                    this.currentQuestion = null;

                    // Check if approved
                    const status = await api.getDialogStatus(this.currentSessionId);
                    if (status.state === 'approved') {
                        this.dialogState = 'approved';
                        this.dialogProgress = 100;
                    }
                }
            } catch (error) {
                console.error('Failed to load question:', error);
            }
        },

        async answerQuestion(answer) {
            if (!this.currentSessionId || !this.currentQuestion) return;

            try {
                const result = await api.answerQuestion(this.currentSessionId, answer);

                if (result.success) {
                    this.textInput = '';
                    await this.loadDialogStatus();

                    if (result.state === 'refining' || result.state === 'approved') {
                        this.currentQuestion = null;
                    } else {
                        await this.loadCurrentQuestion();
                    }
                } else {
                    this.showNotification(result.error || '提交失败', 'error');
                }
            } catch (error) {
                this.showNotification(error.message, 'error');
            }
        },

        // Architecture
        async loadArchitecture() {
            if (!this.currentSessionId) return;

            try {
                const data = await api.getArchitecture(this.currentSessionId);
                this.architecture = data;
            } catch (error) {
                console.error('Failed to load architecture:', error);
            }
        },

        formatDirectoryStructure(struct, indent = 0) {
            if (!struct) return '';

            let result = '  '.repeat(indent) + struct.name + '/\n';

            if (struct.children) {
                for (const child of struct.children) {
                    if (child.type === 'directory') {
                        result += this.formatDirectoryStructure(child, indent + 1);
                    } else {
                        result += '  '.repeat(indent + 1) + child.name + '\n';
                    }
                }
            }

            return result;
        },

        // Code generation
        async startCodegen() {
            if (!this.currentSessionId) return;

            try {
                const result = await api.startCodegen(this.currentSessionId);
                if (result.job_id) {
                    this.showNotification('代码生成已开始', 'success');
                    this.currentPage = 'tasks';

                    // Poll job status
                    this.pollCodegenJob(result.job_id);
                }
            } catch (error) {
                this.showNotification(error.message, 'error');
            }
        },

        async pollCodegenJob(jobId) {
            const poll = async () => {
                try {
                    const job = await api.getCodegenJob(jobId);

                    if (job.status === 'completed') {
                        this.showNotification('代码生成完成!', 'success');
                        await this.loadTasks();
                    } else if (job.status === 'failed') {
                        this.showNotification('代码生成失败: ' + job.error, 'error');
                    } else if (job.status === 'running' || job.status === 'pending') {
                        setTimeout(poll, 2000);
                    }
                } catch (error) {
                    console.error('Failed to poll job:', error);
                }
            };

            poll();
        },

        // Tasks
        async loadTasks() {
            try {
                const [tasksData, statsData, runningData] = await Promise.all([
                    api.listTasks(null, this.taskFilter || null),
                    api.getTaskStats(),
                    api.getRunningTasks()
                ]);

                this.tasks = tasksData.tasks || [];
                this.taskStats = statsData;
                this.runningTasks = runningData.running_tasks || [];
            } catch (error) {
                console.error('Failed to load tasks:', error);
            }
        },

        get filteredTasks() {
            if (!this.taskFilter) return this.tasks;
            return this.tasks.filter(t => t.status === this.taskFilter);
        },

        // Delivery
        async loadDeliveryChecklist() {
            if (!this.currentSessionId) return;

            try {
                const data = await api.getDeliveryChecklist(this.currentSessionId);
                this.deliveryChecklist = data.checklist || [];
            } catch (error) {
                console.error('Failed to load checklist:', error);
            }
        },

        async loadDeliveredProjects() {
            try {
                const data = await api.listDeliveredProjects();
                this.deliveredProjects = data.projects || [];
            } catch (error) {
                console.error('Failed to load projects:', error);
            }
        },

        async generateDocs() {
            if (!this.currentSessionId) return;

            try {
                const result = await api.generateDocs(this.currentSessionId);
                this.showNotification(`已生成文档: ${result.generated.join(', ')}`, 'success');
            } catch (error) {
                this.showNotification(error.message, 'error');
            }
        },

        async prepareRelease() {
            if (!this.currentSessionId) return;

            try {
                const result = await api.prepareRelease(this.currentSessionId);
                this.showNotification(`项目已准备好发布，版本: ${result.version}`, 'success');
                await this.loadDeliveredProjects();
            } catch (error) {
                this.showNotification(error.message, 'error');
            }
        }
    };

    // Initialize app
    app.init();

    // Watch for page changes
    let lastPage = app.currentPage;
    setInterval(() => {
        if (app.currentPage !== lastPage) {
            lastPage = app.currentPage;

            // Load page-specific data
            switch (app.currentPage) {
                case 'dialog':
                    app.loadDialogStatus();
                    app.loadCurrentQuestion();
                    break;
                case 'architecture':
                    app.loadArchitecture();
                    break;
                case 'tasks':
                    app.loadTasks();
                    break;
                case 'delivery':
                    app.loadDeliveryChecklist();
                    app.loadDeliveredProjects();
                    break;
            }
        }
    }, 100);
});
