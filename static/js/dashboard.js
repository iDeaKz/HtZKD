/**
 * 🚀 LivePrecisionCalculator - Main Dashboard Controller
 * ====================================================
 * 
 * Manages the quantum-precision calculator dashboard with real-time updates,
 * 3D visualizations, and comprehensive error handling.
 */

class QuantumDashboard {
    constructor() {
        this.isInitialized = false;
        this.calculationHistory = [];
        this.systemMetrics = {};
        this.exchangeRates = {};
        this.healingEvents = [];
        this.charts = {};
        
        // Audio context for reactive elements
        this.audioContext = null;
        this.audioEnabled = false;
        
        // Animation controls
        this.animationEnabled = true;
        this.animationId = null;
        
        // WebSocket manager
        this.wsManager = null;
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing Quantum Dashboard...');
        
        try {
            // Initialize WebSocket connection
            await this.initWebSocket();
            
            // Initialize form handlers
            this.initFormHandlers();
            
            // Initialize charts
            this.initCharts();
            
            // Initialize UI controls
            this.initUIControls();
            
            // Initialize audio context
            this.initAudioContext();
            
            // Load initial data
            await this.loadInitialData();
            
            // Hide loading overlay
            this.hideLoadingOverlay();
            
            this.isInitialized = true;
            console.log('✅ Quantum Dashboard initialized successfully');
            
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.showError('Failed to initialize dashboard: ' + error.message);
        }
    }
    
    async initWebSocket() {
        this.wsManager = new WebSocketManager();
        
        this.wsManager.onMessage = (data) => {
            this.handleWebSocketMessage(data);
        };
        
        this.wsManager.onConnectionChange = (connected) => {
            this.updateConnectionStatus(connected);
        };
        
        await this.wsManager.connect();
    }
    
    initFormHandlers() {
        const form = document.getElementById('calculatorForm');
        const clearFeedBtn = document.getElementById('clearFeed');
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performCalculation();
        });
        
        clearFeedBtn.addEventListener('click', () => {
            this.clearCalculationFeed();
        });
        
        // Auto-populate currency dropdown
        this.populateCurrencyDropdown();
    }
    
    initCharts() {
        // Performance Analytics Chart
        const performanceCtx = document.getElementById('performanceChart').getContext('2d');
        this.charts.performance = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Calculations/min',
                    data: [],
                    borderColor: '#4dd0e1',
                    backgroundColor: 'rgba(77, 208, 225, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Error Rate %',
                    data: [],
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: { color: '#ffffff' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
        
        // Currency Exchange Rates Chart
        const currencyCtx = document.getElementById('currencyChart').getContext('2d');
        this.charts.currency = new Chart(currencyCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Exchange Rate (vs USD)',
                    data: [],
                    backgroundColor: 'rgba(77, 208, 225, 0.6)',
                    borderColor: '#4dd0e1',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
    
    initUIControls() {
        const toggleAnimation = document.getElementById('toggleAnimation');
        const toggleAudio = document.getElementById('toggleAudio');
        
        toggleAnimation.addEventListener('click', () => {
            this.toggleAnimation();
        });
        
        toggleAudio.addEventListener('click', () => {
            this.toggleAudio();
        });
    }
    
    initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🔊 Audio context initialized');
        } catch (error) {
            console.warn('⚠️ Audio context not available:', error);
        }
    }
    
    async loadInitialData() {
        try {
            // Load supported currencies
            const currencyResponse = await fetch('/api/currencies');
            const currencyData = await currencyResponse.json();
            
            this.exchangeRates = currencyData.current_rates || {};
            this.updateCurrencyChart();
            
            // Load system metrics
            const metricsResponse = await fetch('/api/metrics');
            const metricsData = await metricsResponse.json();
            
            this.updateSystemMetrics(metricsData);
            
            // Load healing events
            const healingResponse = await fetch('/api/healing-events');
            const healingData = await healingResponse.json();
            
            this.healingEvents = healingData;
            this.updateHealingDashboard();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }
    
    async performCalculation() {
        const operand1 = document.getElementById('operand1').value;
        const operand2 = document.getElementById('operand2').value;
        const operation = document.getElementById('operation').value;
        const precision = parseInt(document.getElementById('precision').value);
        const currency = document.getElementById('currency').value;
        
        if (!operand1 || !operand2) {
            this.showError('Please enter both operands');
            return;
        }
        
        const request = {
            operand1,
            operand2,
            operation,
            precision,
            currency
        };
        
        try {
            const response = await fetch('/api/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Calculation failed');
            }
            
            const result = await response.json();
            this.displayCalculationResult(result);
            this.addToCalculationFeed(request, result);
            
            // Play success sound if audio enabled
            if (this.audioEnabled) {
                this.playCalculationSound();
            }
            
        } catch (error) {
            console.error('Calculation error:', error);
            this.showError('Calculation failed: ' + error.message);
        }
    }
    
    displayCalculationResult(result) {
        const resultDisplay = document.getElementById('resultDisplay');
        
        resultDisplay.innerHTML = `
            <div class="result-content fade-in">
                <div class="result-value">${result.result}</div>
                <div class="result-meta">
                    <div><strong>Precision:</strong> ${result.precision_used} decimals</div>
                    <div><strong>Currency:</strong> ${result.currency}</div>
                    <div><strong>ID:</strong> ${result.calculation_id.substring(0, 8)}...</div>
                    <div><strong>Time:</strong> ${new Date(result.timestamp).toLocaleTimeString()}</div>
                </div>
            </div>
        `;
        
        resultDisplay.className = 'result-display has-result';
        
        // Add success animation
        resultDisplay.classList.add('success-flash');
        setTimeout(() => {
            resultDisplay.classList.remove('success-flash');
        }, 600);
    }
    
    addToCalculationFeed(request, result) {
        const feed = document.getElementById('calculationFeed');
        
        // Remove placeholder if present
        const placeholder = feed.querySelector('.feed-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        const feedItem = document.createElement('div');
        feedItem.className = 'feed-item';
        feedItem.innerHTML = `
            <div class="feed-item-header">
                <div class="feed-item-operation">
                    ${request.operand1} ${this.getOperationSymbol(request.operation)} ${request.operand2}
                </div>
                <div class="feed-item-timestamp">
                    ${new Date(result.timestamp).toLocaleTimeString()}
                </div>
            </div>
            <div class="feed-item-result">
                = ${result.result}
            </div>
        `;
        
        // Insert at the beginning
        feed.insertBefore(feedItem, feed.firstChild);
        
        // Keep only last 20 items
        const items = feed.querySelectorAll('.feed-item');
        if (items.length > 20) {
            items[items.length - 1].remove();
        }
        
        // Add to history
        this.calculationHistory.push({ request, result });
    }
    
    getOperationSymbol(operation) {
        const symbols = {
            'add': '+',
            'subtract': '−',
            'multiply': '×',
            'divide': '÷',
            'power': '^'
        };
        return symbols[operation] || operation;
    }
    
    clearCalculationFeed() {
        const feed = document.getElementById('calculationFeed');
        feed.innerHTML = `
            <div class="feed-placeholder">
                <i class="fas fa-satellite-dish fa-2x"></i>
                <p>Waiting for live calculations...</p>
            </div>
        `;
        this.calculationHistory = [];
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'calculation_result':
                // Handle real-time calculation from other clients
                if (data.data.calculation_id) {
                    this.addToCalculationFeed(
                        {
                            operand1: 'Remote',
                            operand2: 'Client',
                            operation: 'calculate'
                        },
                        data.data
                    );
                }
                break;
                
            case 'system_metrics':
                this.updateSystemMetrics(data.data);
                break;
                
            case 'exchange_rates':
                this.exchangeRates = data.data;
                this.updateCurrencyChart();
                break;
                
            case 'healing_event':
                this.addHealingEvent(data.data);
                break;
                
            case 'welcome':
                console.log('🎉 WebSocket connected:', data.data);
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    updateSystemMetrics(metrics) {
        this.systemMetrics = metrics;
        
        // Update metric displays
        document.getElementById('activeConnections').textContent = metrics.active_connections;
        document.getElementById('calculationsPerMinute').textContent = metrics.calculations_per_minute;
        document.getElementById('cacheHitRatio').textContent = (metrics.cache_hit_ratio * 100).toFixed(1) + '%';
        document.getElementById('errorRate').textContent = (metrics.error_rate * 100).toFixed(1) + '%';
        document.getElementById('uptime').textContent = this.formatUptime(metrics.uptime_seconds);
        
        // Update performance chart
        this.updatePerformanceChart(metrics);
    }
    
    updatePerformanceChart(metrics) {
        const chart = this.charts.performance;
        const now = new Date().toLocaleTimeString();
        
        // Add new data point
        chart.data.labels.push(now);
        chart.data.datasets[0].data.push(metrics.calculations_per_minute);
        chart.data.datasets[1].data.push(metrics.error_rate * 100);
        
        // Keep only last 20 data points
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
            chart.data.datasets[1].data.shift();
        }
        
        chart.update('none');
    }
    
    updateCurrencyChart() {
        const chart = this.charts.currency;
        const currencies = Object.keys(this.exchangeRates).slice(0, 10); // Top 10
        const rates = currencies.map(curr => parseFloat(this.exchangeRates[curr]));
        
        chart.data.labels = currencies;
        chart.data.datasets[0].data = rates;
        chart.update();
    }
    
    addHealingEvent(event) {
        this.healingEvents.unshift(event);
        
        // Keep only last 50 events
        if (this.healingEvents.length > 50) {
            this.healingEvents = this.healingEvents.slice(0, 50);
        }
        
        this.updateHealingDashboard();
    }
    
    updateHealingDashboard() {
        const eventsContainer = document.getElementById('healingEvents');
        
        if (this.healingEvents.length === 0) {
            eventsContainer.innerHTML = `
                <div class="healing-placeholder">
                    <i class="fas fa-stethoscope fa-2x"></i>
                    <p>No healing events yet - system running smoothly!</p>
                </div>
            `;
            return;
        }
        
        eventsContainer.innerHTML = this.healingEvents.slice(0, 10).map(event => `
            <div class="healing-event ${event.success ? 'success' : 'error'}">
                <strong>${event.error_type}:</strong> ${event.healing_action}
                <small class="d-block mt-1">${new Date(event.timestamp).toLocaleString()}</small>
            </div>
        `).join('');
        
        // Update healing stats
        const totalHealed = this.healingEvents.filter(e => e.success).length;
        const successRate = this.healingEvents.length > 0 
            ? (totalHealed / this.healingEvents.length * 100).toFixed(1)
            : 100;
            
        document.getElementById('totalHealed').textContent = totalHealed;
        document.getElementById('healingSuccessRate').textContent = successRate + '%';
    }
    
    toggleAnimation() {
        this.animationEnabled = !this.animationEnabled;
        const btn = document.getElementById('toggleAnimation');
        
        if (this.animationEnabled) {
            btn.innerHTML = '<i class="fas fa-pause"></i> Animation';
            if (window.threeVisualization) {
                window.threeVisualization.startAnimation();
            }
        } else {
            btn.innerHTML = '<i class="fas fa-play"></i> Animation';
            if (window.threeVisualization) {
                window.threeVisualization.stopAnimation();
            }
        }
    }
    
    toggleAudio() {
        this.audioEnabled = !this.audioEnabled;
        const btn = document.getElementById('toggleAudio');
        
        if (this.audioEnabled) {
            btn.innerHTML = '<i class="fas fa-volume-up"></i> Audio';
            if (this.audioContext && this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
        } else {
            btn.innerHTML = '<i class="fas fa-volume-mute"></i> Audio';
        }
    }
    
    playCalculationSound() {
        if (!this.audioContext || !this.audioEnabled) return;
        
        try {
            // Create a simple success sound
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, this.audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.3);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + 0.3);
            
        } catch (error) {
            console.warn('Failed to play sound:', error);
        }
    }
    
    populateCurrencyDropdown() {
        const currencySelect = document.getElementById('currency');
        const currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD',
            'MXN', 'SGD', 'HKD', 'NOK', 'INR', 'KRW', 'TRY', 'RUB', 'BRL', 'ZAR'
        ];
        
        currencySelect.innerHTML = currencies.map(curr => 
            `<option value="${curr}">${curr}</option>`
        ).join('');
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const statusText = document.getElementById('statusText');
        
        if (connected) {
            statusElement.className = 'connection-status connected';
            statusText.textContent = 'Connected';
        } else {
            statusElement.className = 'connection-status disconnected';
            statusText.textContent = 'Disconnected';
        }
    }
    
    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 500);
    }
    
    showError(message) {
        console.error('Dashboard Error:', message);
        
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast quantum-card position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quantumDashboard = new QuantumDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (window.quantumDashboard && window.quantumDashboard.wsManager) {
        if (document.hidden) {
            console.log('Page hidden, maintaining WebSocket connection');
        } else {
            console.log('Page visible, ensuring WebSocket connection');
            window.quantumDashboard.wsManager.ensureConnection();
        }
    }
});