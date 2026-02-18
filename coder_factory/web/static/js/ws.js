/**
 * WebSocket Client for Coder-Factory
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.listeners = new Map();

        // Will be set by Alpine app
        this.onStateChange = null;
    }

    connect(sessionId = null) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        this.sessionId = sessionId;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = sessionId
            ? `${protocol}//${window.location.host}/ws/${sessionId}`
            : `${protocol}//${window.location.host}/ws/global`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connected = true;
                this.reconnectAttempts = 0;
                this._notifyStateChange();

                // Start heartbeat
                this._startHeartbeat();
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected', event.code, event.reason);
                this.connected = false;
                this._notifyStateChange();

                // Attempt reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
                    setTimeout(() => this.connect(this.sessionId), this.reconnectDelay);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this._handleMessage(message);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        this._notifyStateChange();
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    subscribe(events) {
        this.send({ type: 'subscribe', events });
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    _handleMessage(message) {
        const { type } = message;

        // Notify listeners
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => callback(message));
        }

        // Also notify all listeners
        if (this.listeners.has('*')) {
            this.listeners.get('*').forEach(callback => callback(message));
        }
    }

    _startHeartbeat() {
        this._heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 30000);
    }

    _stopHeartbeat() {
        if (this._heartbeatInterval) {
            clearInterval(this._heartbeatInterval);
        }
    }

    _notifyStateChange() {
        if (this.onStateChange) {
            this.onStateChange(this.connected);
        }
    }
}

// Global WebSocket client
const wsClient = new WebSocketClient();
