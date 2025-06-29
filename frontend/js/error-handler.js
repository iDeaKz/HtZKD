/**
 * Comprehensive Error Handler for 3D Paint Application
 * Provides multi-level error management with recovery mechanisms
 */

class ErrorHandler {
    constructor() {
        this.errorLog = [];
        this.errorCallbacks = {};
        this.recoveryAttempts = new Map();
        this.maxRecoveryAttempts = 3;
        
        // Initialize error tracking
        this.initializeErrorTracking();
        
        // Set up global error handlers
        this.setupGlobalErrorHandlers();
    }

    /**
     * Initialize error tracking system
     */
    initializeErrorTracking() {
        this.errorTypes = {
            WEBGL: 'webgl',
            CANVAS: 'canvas',
            MEMORY: 'memory',
            NETWORK: 'network',
            GPU: 'gpu',
            USER_INPUT: 'user_input',
            FILE_SYSTEM: 'file_system',
            PERFORMANCE: 'performance',
            SHADER: 'shader',
            BRUSH: 'brush',
            LAYER: 'layer',
            CRITICAL: 'critical'
        };

        this.errorLevels = {
            INFO: 'info',
            WARNING: 'warning',
            ERROR: 'error',
            CRITICAL: 'critical'
        };

        this.performanceMetrics = {
            frameTime: [],
            memoryUsage: [],
            gpuMemory: [],
            renderCalls: 0,
            lastFrameTime: performance.now()
        };
    }

    /**
     * Set up global error handlers
     */
    setupGlobalErrorHandlers() {
        // JavaScript errors
        window.onerror = (message, source, lineno, colno, error) => {
            this.handleError({
                type: this.errorTypes.CRITICAL,
                level: this.errorLevels.ERROR,
                message: message,
                source: source,
                line: lineno,
                column: colno,
                error: error,
                timestamp: Date.now()
            });
            return true;
        };

        // Promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                type: this.errorTypes.CRITICAL,
                level: this.errorLevels.ERROR,
                message: 'Unhandled Promise Rejection',
                error: event.reason,
                timestamp: Date.now()
            });
            event.preventDefault();
        });

        // Resource loading errors
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.handleError({
                    type: this.errorTypes.NETWORK,
                    level: this.errorLevels.WARNING,
                    message: `Resource loading failed: ${event.target.src || event.target.href}`,
                    element: event.target,
                    timestamp: Date.now()
                });
            }
        }, true);
    }

    /**
     * Handle errors with recovery mechanisms
     * @param {Object} errorData - Error information
     */
    handleError(errorData) {
        // Log error
        this.logError(errorData);

        // Attempt recovery
        this.attemptRecovery(errorData);

        // Notify UI
        this.notifyUI(errorData);

        // Trigger callbacks
        this.triggerCallbacks(errorData);

        // Performance monitoring
        this.updatePerformanceMetrics(errorData);
    }

    /**
     * Log error to internal storage and console
     * @param {Object} errorData - Error information
     */
    logError(errorData) {
        // Add to internal log
        this.errorLog.push({
            ...errorData,
            id: this.generateErrorId(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            timestamp: Date.now()
        });

        // Keep only last 100 errors
        if (this.errorLog.length > 100) {
            this.errorLog.shift();
        }

        // Console logging
        const logMethod = this.getConsoleMethod(errorData.level);
        console[logMethod]('3D Paint Error:', errorData);

        // Send to backend if available
        this.sendToBackend(errorData);
    }

    /**
     * Attempt automatic recovery from errors
     * @param {Object} errorData - Error information
     */
    attemptRecovery(errorData) {
        const recoveryKey = `${errorData.type}_${errorData.message}`;
        const attempts = this.recoveryAttempts.get(recoveryKey) || 0;

        if (attempts >= this.maxRecoveryAttempts) {
            console.warn('Max recovery attempts reached for:', recoveryKey);
            return false;
        }

        this.recoveryAttempts.set(recoveryKey, attempts + 1);

        switch (errorData.type) {
            case this.errorTypes.WEBGL:
                return this.recoverWebGL(errorData);
            
            case this.errorTypes.MEMORY:
                return this.recoverMemory(errorData);
            
            case this.errorTypes.GPU:
                return this.recoverGPU(errorData);
            
            case this.errorTypes.CANVAS:
                return this.recoverCanvas(errorData);
            
            case this.errorTypes.SHADER:
                return this.recoverShader(errorData);
            
            default:
                return this.genericRecovery(errorData);
        }
    }

    /**
     * WebGL error recovery
     * @param {Object} errorData - Error information
     */
    recoverWebGL(errorData) {
        console.log('Attempting WebGL recovery...');
        
        try {
            // Force WebGL context restoration
            const canvas = document.getElementById('canvas3d');
            if (canvas && canvas.getContext) {
                const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                if (gl) {
                    // Check if context is lost
                    if (gl.isContextLost()) {
                        console.log('WebGL context lost, waiting for restoration...');
                        canvas.addEventListener('webglcontextrestored', () => {
                            console.log('WebGL context restored');
                            this.notifyRecovery('WebGL context restored');
                            // Reinitialize 3D engine
                            if (window.Canvas3D) {
                                window.Canvas3D.reinitialize();
                            }
                        });
                        return true;
                    }
                }
            }
            
            // Try fallback to software rendering
            this.enableSoftwareRendering();
            return true;
        } catch (error) {
            console.error('WebGL recovery failed:', error);
            return false;
        }
    }

    /**
     * Memory error recovery
     * @param {Object} errorData - Error information
     */
    recoverMemory(errorData) {
        console.log('Attempting memory recovery...');
        
        try {
            // Force garbage collection if available
            if (window.gc) {
                window.gc();
            }
            
            // Clear caches
            this.clearMemoryCaches();
            
            // Reduce quality settings
            this.reduceQualitySettings();
            
            return true;
        } catch (error) {
            console.error('Memory recovery failed:', error);
            return false;
        }
    }

    /**
     * GPU error recovery
     * @param {Object} errorData - Error information
     */
    recoverGPU(errorData) {
        console.log('Attempting GPU recovery...');
        
        try {
            // Reduce GPU load
            this.reduceGPULoad();
            
            // Clear GPU buffers
            this.clearGPUBuffers();
            
            return true;
        } catch (error) {
            console.error('GPU recovery failed:', error);
            return false;
        }
    }

    /**
     * Canvas error recovery
     * @param {Object} errorData - Error information
     */
    recoverCanvas(errorData) {
        console.log('Attempting canvas recovery...');
        
        try {
            // Recreate canvas element
            const canvas = document.getElementById('canvas3d');
            if (canvas) {
                const parent = canvas.parentNode;
                const newCanvas = canvas.cloneNode(true);
                parent.replaceChild(newCanvas, canvas);
                
                // Reinitialize canvas
                if (window.Canvas3D) {
                    window.Canvas3D.reinitialize();
                }
                
                return true;
            }
        } catch (error) {
            console.error('Canvas recovery failed:', error);
            return false;
        }
    }

    /**
     * Shader error recovery
     * @param {Object} errorData - Error information
     */
    recoverShader(errorData) {
        console.log('Attempting shader recovery...');
        
        try {
            // Use fallback shaders
            this.loadFallbackShaders();
            return true;
        } catch (error) {
            console.error('Shader recovery failed:', error);
            return false;
        }
    }

    /**
     * Generic recovery attempt
     * @param {Object} errorData - Error information
     */
    genericRecovery(errorData) {
        console.log('Attempting generic recovery...');
        
        try {
            // Reload page as last resort
            if (errorData.level === this.errorLevels.CRITICAL) {
                const userConfirmed = confirm('A critical error occurred. Reload the page?');
                if (userConfirmed) {
                    window.location.reload();
                }
            }
            return true;
        } catch (error) {
            console.error('Generic recovery failed:', error);
            return false;
        }
    }

    /**
     * Helper methods for recovery
     */
    enableSoftwareRendering() {
        // Enable software rendering fallback
        const canvas = document.getElementById('canvas3d');
        if (canvas) {
            canvas.classList.add('software-rendering');
        }
    }

    clearMemoryCaches() {
        // Clear various caches
        if (window.Canvas3D && window.Canvas3D.clearCaches) {
            window.Canvas3D.clearCaches();
        }
    }

    reduceQualitySettings() {
        // Reduce rendering quality
        if (window.Canvas3D && window.Canvas3D.setQuality) {
            window.Canvas3D.setQuality('low');
        }
    }

    reduceGPULoad() {
        // Reduce GPU intensive operations
        if (window.Canvas3D && window.Canvas3D.reduceGPULoad) {
            window.Canvas3D.reduceGPULoad();
        }
    }

    clearGPUBuffers() {
        // Clear GPU buffers
        if (window.Canvas3D && window.Canvas3D.clearGPUBuffers) {
            window.Canvas3D.clearGPUBuffers();
        }
    }

    loadFallbackShaders() {
        // Load basic fallback shaders
        if (window.Canvas3D && window.Canvas3D.loadFallbackShaders) {
            window.Canvas3D.loadFallbackShaders();
        }
    }

    /**
     * Notify UI of errors
     * @param {Object} errorData - Error information
     */
    notifyUI(errorData) {
        const errorDisplay = document.getElementById('error-display');
        const errorMessage = document.getElementById('error-message');
        
        if (errorDisplay && errorMessage) {
            errorMessage.textContent = errorData.message;
            errorDisplay.classList.remove('d-none');
            
            // Auto-hide after 5 seconds for non-critical errors
            if (errorData.level !== this.errorLevels.CRITICAL) {
                setTimeout(() => {
                    errorDisplay.classList.add('d-none');
                }, 5000);
            }
        }
    }

    /**
     * Notify successful recovery
     * @param {string} message - Recovery message
     */
    notifyRecovery(message) {
        console.log('Recovery successful:', message);
        
        // You could show a success message here
        const errorDisplay = document.getElementById('error-display');
        if (errorDisplay) {
            errorDisplay.classList.add('d-none');
        }
    }

    /**
     * Trigger registered callbacks
     * @param {Object} errorData - Error information
     */
    triggerCallbacks(errorData) {
        const callbacks = this.errorCallbacks[errorData.type] || [];
        callbacks.forEach(callback => {
            try {
                callback(errorData);
            } catch (error) {
                console.error('Error callback failed:', error);
            }
        });
    }

    /**
     * Update performance metrics
     * @param {Object} errorData - Error information
     */
    updatePerformanceMetrics(errorData) {
        if (errorData.type === this.errorTypes.PERFORMANCE) {
            const now = performance.now();
            const frameTime = now - this.performanceMetrics.lastFrameTime;
            this.performanceMetrics.frameTime.push(frameTime);
            this.performanceMetrics.lastFrameTime = now;
            
            // Keep only last 60 frames
            if (this.performanceMetrics.frameTime.length > 60) {
                this.performanceMetrics.frameTime.shift();
            }
        }
    }

    /**
     * Send error to backend
     * @param {Object} errorData - Error information
     */
    async sendToBackend(errorData) {
        try {
            if (errorData.level === this.errorLevels.CRITICAL) {
                await fetch('/api/errors', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(errorData)
                });
            }
        } catch (error) {
            console.error('Failed to send error to backend:', error);
        }
    }

    /**
     * Register error callback
     * @param {string} errorType - Error type
     * @param {Function} callback - Callback function
     */
    onError(errorType, callback) {
        if (!this.errorCallbacks[errorType]) {
            this.errorCallbacks[errorType] = [];
        }
        this.errorCallbacks[errorType].push(callback);
    }

    /**
     * Get console method for error level
     * @param {string} level - Error level
     */
    getConsoleMethod(level) {
        switch (level) {
            case this.errorLevels.INFO:
                return 'info';
            case this.errorLevels.WARNING:
                return 'warn';
            case this.errorLevels.ERROR:
                return 'error';
            case this.errorLevels.CRITICAL:
                return 'error';
            default:
                return 'log';
        }
    }

    /**
     * Generate unique error ID
     */
    generateErrorId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * Get error statistics
     */
    getErrorStats() {
        const stats = {
            total: this.errorLog.length,
            byType: {},
            byLevel: {},
            recent: this.errorLog.slice(-10)
        };

        this.errorLog.forEach(error => {
            stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
            stats.byLevel[error.level] = (stats.byLevel[error.level] || 0) + 1;
        });

        return stats;
    }

    /**
     * Clear error log
     */
    clearErrorLog() {
        this.errorLog = [];
        this.recoveryAttempts.clear();
    }
}

// Create global error handler instance
window.ErrorHandler = new ErrorHandler();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}