/**
 * 🌐 LivePrecisionCalculator - WebSocket Manager
 * ===========================================
 * 
 * Manages WebSocket connections with automatic reconnection,
 * connection pooling, and real-time message handling.
 */

class WebSocketManager {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.pingInterval = null;
        this.reconnectTimeout = null;
        
        // Event handlers
        this.onMessage = null;
        this.onConnectionChange = null;
        this.onError = null;
        
        // Message queue for when disconnected
        this.messageQueue = [];
        this.maxQueueSize = 100;
        
        // Statistics
        this.stats = {
            messagesReceived: 0,
            messagesSent: 0,
            reconnections: 0,
            totalUptime: 0,
            connectTime: null
        };
        
        this.getWebSocketUrl = this.getWebSocketUrl.bind(this);
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws`;
    }
    
    async connect() {
        if (this.websocket && (this.websocket.readyState === WebSocket.CONNECTING || this.websocket.readyState === WebSocket.OPEN)) {
            console.log('WebSocket already connecting or connected');
            return;
        }
        
        try {
            console.log('🌐 Connecting to WebSocket...');
            
            this.websocket = new WebSocket(this.getWebSocketUrl());
            
            this.websocket.onopen = (event) => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.stats.connectTime = Date.now();
                this.stats.reconnections++;
                
                // Process queued messages
                this.processMessageQueue();
                
                // Start ping interval
                this.startPingInterval();
                
                if (this.onConnectionChange) {
                    this.onConnectionChange(true);
                }
            };
            
            this.websocket.onmessage = (event) => {
                this.stats.messagesReceived++;
                
                try {
                    const data = JSON.parse(event.data);
                    
                    // Handle ping/pong
                    if (data.type === 'ping') {
                        this.send({ type: 'pong' });
                        return;
                    }
                    
                    if (data.type === 'pong') {
                        // Pong received, connection is alive
                        return;
                    }
                    
                    if (this.onMessage) {
                        this.onMessage(data);
                    }
                    
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.log('🔌 WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                
                // Update uptime
                if (this.stats.connectTime) {
                    this.stats.totalUptime += Date.now() - this.stats.connectTime;
                    this.stats.connectTime = null;
                }
                
                this.stopPingInterval();
                
                if (this.onConnectionChange) {
                    this.onConnectionChange(false);
                }
                
                // Attempt reconnection if not a normal closure
                if (event.code !== 1000 && event.code !== 1001) {
                    this.scheduleReconnect();
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('🚨 WebSocket error:', error);
                
                if (this.onError) {
                    this.onError(error);
                }
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    disconnect() {
        console.log('🔌 Disconnecting WebSocket...');
        
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        
        this.stopPingInterval();
        
        if (this.websocket) {
            this.websocket.close(1000, 'User disconnection');
            this.websocket = null;
        }
        
        this.isConnected = false;
        
        if (this.onConnectionChange) {
            this.onConnectionChange(false);
        }
    }
    
    send(data) {
        if (!this.isConnected || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            // Queue message for later
            if (this.messageQueue.length < this.maxQueueSize) {
                this.messageQueue.push(data);
                console.log('Message queued (WebSocket not connected)');
            } else {
                console.warn('Message queue full, dropping message');
            }
            return false;
        }
        
        try {
            this.websocket.send(JSON.stringify(data));
            this.stats.messagesSent++;
            return true;
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
            return false;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
        
        console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
        
        this.reconnectTimeout = setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    processMessageQueue() {
        console.log(`📤 Processing ${this.messageQueue.length} queued messages`);
        
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }
    
    startPingInterval() {
        this.stopPingInterval();
        
        this.pingInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping', timestamp: Date.now() });
            }
        }, 30000); // Ping every 30 seconds
    }
    
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    ensureConnection() {
        if (!this.isConnected) {
            console.log('🔄 Ensuring WebSocket connection...');
            this.connect();
        }
    }
    
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            stats: {
                ...this.stats,
                currentUptime: this.stats.connectTime ? Date.now() - this.stats.connectTime : 0
            }
        };
    }
    
    // Health check method
    async healthCheck() {
        return new Promise((resolve, reject) => {
            if (!this.isConnected) {
                reject(new Error('WebSocket not connected'));
                return;
            }
            
            const healthCheckId = Date.now();
            const timeout = setTimeout(() => {
                reject(new Error('Health check timeout'));
            }, 5000);
            
            const originalOnMessage = this.onMessage;
            this.onMessage = (data) => {
                if (data.type === 'pong' && data.healthCheckId === healthCheckId) {
                    clearTimeout(timeout);
                    this.onMessage = originalOnMessage;
                    resolve(true);
                } else if (originalOnMessage) {
                    originalOnMessage(data);
                }
            };
            
            this.send({
                type: 'ping',
                healthCheckId: healthCheckId,
                timestamp: Date.now()
            });
        });
    }
    
    // Message broadcasting with acknowledgment
    async sendWithAck(data, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const messageId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            const messageData = {
                ...data,
                messageId: messageId,
                requiresAck: true
            };
            
            const timeoutHandle = setTimeout(() => {
                reject(new Error('Message acknowledgment timeout'));
            }, timeout);
            
            const originalOnMessage = this.onMessage;
            this.onMessage = (receivedData) => {
                if (receivedData.type === 'ack' && receivedData.messageId === messageId) {
                    clearTimeout(timeoutHandle);
                    this.onMessage = originalOnMessage;
                    resolve(receivedData);
                } else if (originalOnMessage) {
                    originalOnMessage(receivedData);
                }
            };
            
            if (!this.send(messageData)) {
                clearTimeout(timeoutHandle);
                this.onMessage = originalOnMessage;
                reject(new Error('Failed to send message'));
            }
        });
    }
    
    // Connection pooling simulation (for future enhancement)
    createConnectionPool(size = 3) {
        console.log(`🏊 Creating WebSocket connection pool with ${size} connections`);
        // This would be implemented for high-frequency trading scenarios
        // where multiple connections might be beneficial
    }
    
    // Bandwidth monitoring
    monitorBandwidth() {
        const startTime = Date.now();
        const startRx = this.stats.messagesReceived;
        const startTx = this.stats.messagesSent;
        
        setInterval(() => {
            const currentTime = Date.now();
            const currentRx = this.stats.messagesReceived;
            const currentTx = this.stats.messagesSent;
            
            const timeElapsed = (currentTime - startTime) / 1000; // seconds
            const rxRate = (currentRx - startRx) / timeElapsed;
            const txRate = (currentTx - startTx) / timeElapsed;
            
            console.log(`📊 WebSocket bandwidth - RX: ${rxRate.toFixed(2)} msg/s, TX: ${txRate.toFixed(2)} msg/s`);
        }, 10000); // Every 10 seconds
    }
    
    // Quality of Service metrics
    measureLatency() {
        if (!this.isConnected) return null;
        
        const startTime = performance.now();
        
        return new Promise((resolve, reject) => {
            const latencyId = Date.now();
            const timeout = setTimeout(() => {
                reject(new Error('Latency measurement timeout'));
            }, 3000);
            
            const originalOnMessage = this.onMessage;
            this.onMessage = (data) => {
                if (data.type === 'pong' && data.latencyId === latencyId) {
                    const latency = performance.now() - startTime;
                    clearTimeout(timeout);
                    this.onMessage = originalOnMessage;
                    resolve(latency);
                } else if (originalOnMessage) {
                    originalOnMessage(data);
                }
            };
            
            this.send({
                type: 'ping',
                latencyId: latencyId,
                timestamp: Date.now()
            });
        });
    }
    
    // Error recovery strategies
    handleConnectionError(error) {
        console.error('🚨 WebSocket connection error:', error);
        
        // Implement different recovery strategies based on error type
        if (error.code === 1006) { // Abnormal closure
            console.log('🔧 Implementing recovery strategy for abnormal closure');
            this.scheduleReconnect();
        } else if (error.code === 1011) { // Server error
            console.log('🔧 Server error detected, implementing backoff strategy');
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
            this.scheduleReconnect();
        }
    }
    
    // Performance optimization
    optimizePerformance() {
        // Batch message sending for better performance
        this.messageBatch = [];
        this.batchTimeout = null;
        
        this.originalSend = this.send;
        this.send = (data) => {
            if (data.priority === 'high') {
                return this.originalSend(data);
            }
            
            this.messageBatch.push(data);
            
            if (!this.batchTimeout) {
                this.batchTimeout = setTimeout(() => {
                    if (this.messageBatch.length > 0) {
                        this.originalSend({
                            type: 'batch',
                            messages: this.messageBatch
                        });
                        this.messageBatch = [];
                    }
                    this.batchTimeout = null;
                }, 100); // Batch every 100ms
            }
            
            return true;
        };
    }
}

// Auto-initialize WebSocket manager when loaded
window.WebSocketManager = WebSocketManager;