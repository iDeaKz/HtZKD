/**
 * Main Application Entry Point for 3D Paint Studio
 * Initializes all components and manages application lifecycle
 */

class Paint3DApp {
    constructor() {
        this.version = '1.0.0';
        this.initialized = false;
        this.components = {};
        this.startTime = performance.now();
        
        // Application state
        this.state = {
            isLoading: true,
            hasError: false,
            errorMessage: null,
            performanceMode: 'auto', // auto, high, medium, low
            debugMode: false
        };
        
        // Performance monitoring
        this.performanceMetrics = {
            initTime: 0,
            avgFrameTime: 0,
            memoryUsage: 0,
            errorCount: 0
        };
        
        console.log(`3D Paint Studio v${this.version} starting...`);
    }

    /**
     * Initialize the application
     */
    async initialize() {
        try {
            console.log('Initializing 3D Paint Studio...');
            
            // Show loading indicator
            this.showLoadingIndicator();
            
            // Check browser compatibility
            await this.checkCompatibility();
            
            // Initialize error handler first
            await this.initializeErrorHandler();
            
            // Initialize core components
            await this.initializeComponents();
            
            // Set up performance monitoring
            this.setupPerformanceMonitoring();
            
            // Initialize auto-save
            this.setupAutoSave();
            
            // Set up global event handlers
            this.setupGlobalEventHandlers();
            
            // Mark as initialized
            this.initialized = true;
            this.state.isLoading = false;
            
            // Calculate initialization time
            this.performanceMetrics.initTime = performance.now() - this.startTime;
            
            console.log(`3D Paint Studio initialized in ${this.performanceMetrics.initTime.toFixed(2)}ms`);
            
            // Hide loading indicator
            this.hideLoadingIndicator();
            
            // Show welcome message
            this.showWelcomeMessage();
            
            return true;
            
        } catch (error) {
            this.handleInitializationError(error);
            return false;
        }
    }

    /**
     * Check browser compatibility
     */
    async checkCompatibility() {
        const compatibility = {
            webgl: false,
            webgl2: false,
            canvas: false,
            workers: false,
            indexeddb: false,
            fileapi: false,
            pointerevents: false
        };

        // Check WebGL support
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        const gl2 = canvas.getContext('webgl2');
        
        compatibility.webgl = !!gl;
        compatibility.webgl2 = !!gl2;
        compatibility.canvas = !!canvas.getContext('2d');
        
        // Check other APIs
        compatibility.workers = typeof Worker !== 'undefined';
        compatibility.indexeddb = 'indexedDB' in window;
        compatibility.fileapi = 'File' in window && 'FileReader' in window;
        compatibility.pointerevents = 'PointerEvent' in window;
        
        console.log('Browser compatibility:', compatibility);
        
        // Check minimum requirements
        if (!compatibility.webgl || !compatibility.canvas) {
            throw new Error('Your browser does not support required features for 3D Paint Studio');
        }
        
        // Warn about missing features
        if (!compatibility.webgl2) {
            console.warn('WebGL 2.0 not supported, falling back to WebGL 1.0');
        }
        
        if (!compatibility.pointerevents) {
            console.warn('Pointer Events not supported, touch functionality may be limited');
        }
    }

    /**
     * Initialize error handler
     */
    async initializeErrorHandler() {
        if (window.ErrorHandler) {
            // Error handler is already initialized globally
            this.components.errorHandler = window.ErrorHandler;
            
            // Set up error callback
            this.components.errorHandler.onError('critical', (error) => {
                this.handleCriticalError(error);
            });
            
            console.log('Error handler initialized');
        } else {
            throw new Error('Error handler not available');
        }
    }

    /**
     * Initialize core components
     */
    async initializeComponents() {
        const initSteps = [
            { name: 'UI Manager', init: () => this.initializeUIManager() },
            { name: 'WebGL Utils', init: () => this.initializeWebGL() },
            { name: '3D Canvas', init: () => this.initialize3DCanvas() },
            { name: 'Brush Engine', init: () => this.initializeBrushEngine() },
            { name: 'Performance Monitor', init: () => this.initializePerformanceMonitor() }
        ];

        for (const step of initSteps) {
            try {
                console.log(`Initializing ${step.name}...`);
                await step.init();
                console.log(`${step.name} initialized successfully`);
            } catch (error) {
                console.error(`Failed to initialize ${step.name}:`, error);
                throw new Error(`Component initialization failed: ${step.name}`);
            }
        }
    }

    /**
     * Initialize UI Manager
     */
    async initializeUIManager() {
        if (window.UIManager) {
            const success = window.UIManager.initialize();
            if (success) {
                this.components.uiManager = window.UIManager;
            } else {
                throw new Error('UI Manager initialization failed');
            }
        } else {
            throw new Error('UI Manager not available');
        }
    }

    /**
     * Initialize WebGL
     */
    async initializeWebGL() {
        // WebGL initialization is handled by Canvas3D
        // This is a placeholder for any WebGL-specific setup
        console.log('WebGL utilities ready');
    }

    /**
     * Initialize 3D Canvas
     */
    async initialize3DCanvas() {
        if (window.Canvas3D) {
            const success = await window.Canvas3D.initialize('canvas3d');
            if (success) {
                this.components.canvas3d = window.Canvas3D;
            } else {
                throw new Error('3D Canvas initialization failed');
            }
        } else {
            throw new Error('3D Canvas not available');
        }
    }

    /**
     * Initialize Brush Engine
     */
    async initializeBrushEngine() {
        if (window.BrushEngine) {
            this.components.brushEngine = window.BrushEngine;
            console.log('Brush Engine ready');
        } else {
            throw new Error('Brush Engine not available');
        }
    }

    /**
     * Initialize Performance Monitor
     */
    async initializePerformanceMonitor() {
        // Set up performance monitoring interval
        this.performanceInterval = setInterval(() => {
            this.updatePerformanceMetrics();
        }, 1000);
        
        console.log('Performance monitor started');
    }

    /**
     * Set up performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor frame rate
        this.frameTimeHistory = [];
        this.lastFrameTime = performance.now();
        
        // Monitor memory usage
        if (performance.memory) {
            this.memoryHistory = [];
        }
        
        // Set up adaptive quality
        this.setupAdaptiveQuality();
    }

    /**
     * Set up adaptive quality based on performance
     */
    setupAdaptiveQuality() {
        this.qualityCheckInterval = setInterval(() => {
            if (this.components.canvas3d && this.performanceMetrics.avgFrameTime > 20) {
                // Frame time over 20ms (under 50fps), reduce quality
                const currentQuality = this.components.canvas3d.qualityLevel;
                
                if (currentQuality === 'high') {
                    this.components.canvas3d.setQuality('medium');
                    console.log('Automatically reduced quality to medium');
                } else if (currentQuality === 'medium') {
                    this.components.canvas3d.setQuality('low');
                    console.log('Automatically reduced quality to low');
                }
            } else if (this.components.canvas3d && this.performanceMetrics.avgFrameTime < 10) {
                // Frame time under 10ms (over 100fps), can increase quality
                const currentQuality = this.components.canvas3d.qualityLevel;
                
                if (currentQuality === 'low') {
                    this.components.canvas3d.setQuality('medium');
                    console.log('Automatically increased quality to medium');
                } else if (currentQuality === 'medium') {
                    this.components.canvas3d.setQuality('high');
                    console.log('Automatically increased quality to high');
                }
            }
        }, 5000); // Check every 5 seconds
    }

    /**
     * Update performance metrics
     */
    updatePerformanceMetrics() {
        // Update frame time
        const now = performance.now();
        const frameTime = now - this.lastFrameTime;
        this.lastFrameTime = now;
        
        this.frameTimeHistory.push(frameTime);
        if (this.frameTimeHistory.length > 60) {
            this.frameTimeHistory.shift();
        }
        
        this.performanceMetrics.avgFrameTime = 
            this.frameTimeHistory.reduce((a, b) => a + b, 0) / this.frameTimeHistory.length;
        
        // Update memory usage
        if (performance.memory) {
            this.performanceMetrics.memoryUsage = performance.memory.usedJSHeapSize;
            
            this.memoryHistory.push(this.performanceMetrics.memoryUsage);
            if (this.memoryHistory.length > 60) {
                this.memoryHistory.shift();
            }
        }
        
        // Update UI
        if (this.components.uiManager) {
            this.components.uiManager.updatePerformanceUI();
        }
        
        // Check for memory leaks
        this.checkMemoryLeaks();
    }

    /**
     * Check for memory leaks
     */
    checkMemoryLeaks() {
        if (this.memoryHistory && this.memoryHistory.length >= 60) {
            const recent = this.memoryHistory.slice(-20);
            const older = this.memoryHistory.slice(-60, -40);
            
            const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
            const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
            
            const increase = recentAvg - olderAvg;
            const threshold = 10 * 1024 * 1024; // 10MB increase
            
            if (increase > threshold) {
                console.warn('Potential memory leak detected:', {
                    increase: `${(increase / 1024 / 1024).toFixed(2)}MB`,
                    current: `${(recentAvg / 1024 / 1024).toFixed(2)}MB`
                });
                
                // Trigger cleanup
                this.performMemoryCleanup();
            }
        }
    }

    /**
     * Perform memory cleanup
     */
    performMemoryCleanup() {
        console.log('Performing memory cleanup...');
        
        // Clear caches
        if (this.components.canvas3d) {
            this.components.canvas3d.clearCaches();
        }
        
        if (this.components.brushEngine) {
            this.components.brushEngine.optimizePerformance();
        }
        
        // Force garbage collection if available
        if (window.gc) {
            window.gc();
        }
    }

    /**
     * Set up auto-save functionality
     */
    setupAutoSave() {
        this.autoSaveInterval = setInterval(() => {
            this.performAutoSave();
        }, 30000); // Auto-save every 30 seconds
    }

    /**
     * Perform auto-save
     */
    performAutoSave() {
        try {
            const saveData = this.createSaveData();
            localStorage.setItem('paint3d_autosave', JSON.stringify(saveData));
            console.log('Auto-save completed');
        } catch (error) {
            console.warn('Auto-save failed:', error);
        }
    }

    /**
     * Create save data
     */
    createSaveData() {
        return {
            version: this.version,
            timestamp: Date.now(),
            brushSettings: this.components.brushEngine ? this.components.brushEngine.brushSettings : {},
            cameraPosition: this.components.canvas3d ? this.components.canvas3d.camera.position : {},
            layers: [] // Layer data would go here
        };
    }

    /**
     * Load auto-save data
     */
    loadAutoSave() {
        try {
            const saveData = localStorage.getItem('paint3d_autosave');
            if (saveData) {
                const data = JSON.parse(saveData);
                console.log('Auto-save data found:', data);
                
                // Restore settings
                if (data.brushSettings && this.components.brushEngine) {
                    this.components.brushEngine.updateSettings(data.brushSettings);
                }
                
                return true;
            }
        } catch (error) {
            console.warn('Failed to load auto-save data:', error);
        }
        
        return false;
    }

    /**
     * Set up global event handlers
     */
    setupGlobalEventHandlers() {
        // Visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onPageHidden();
            } else {
                this.onPageVisible();
            }
        });
        
        // Online/offline
        window.addEventListener('online', () => {
            console.log('Connection restored');
        });
        
        window.addEventListener('offline', () => {
            console.log('Connection lost');
        });
        
        // Memory pressure (if supported)
        if ('memory' in navigator) {
            navigator.memory.addEventListener('memoryPressure', () => {
                this.performMemoryCleanup();
            });
        }
    }

    /**
     * Handle page hidden
     */
    onPageHidden() {
        // Pause rendering to save resources
        if (this.components.canvas3d) {
            this.components.canvas3d.stopRenderLoop();
        }
        
        // Perform save
        this.performAutoSave();
    }

    /**
     * Handle page visible
     */
    onPageVisible() {
        // Resume rendering
        if (this.components.canvas3d) {
            this.components.canvas3d.startRenderLoop();
        }
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        console.log('Welcome to 3D Paint Studio!');
        
        // Check for auto-save data
        if (this.loadAutoSave()) {
            if (this.components.uiManager) {
                this.components.uiManager.showMessage('Previous session restored', 'info');
            }
        }
    }

    /**
     * Handle initialization error
     */
    handleInitializationError(error) {
        console.error('3D Paint Studio initialization failed:', error);
        
        this.state.hasError = true;
        this.state.errorMessage = error.message;
        
        // Show error message
        const errorDisplay = document.getElementById('error-display');
        const errorMessage = document.getElementById('error-message');
        
        if (errorDisplay && errorMessage) {
            errorMessage.textContent = `Failed to initialize: ${error.message}`;
            errorDisplay.classList.remove('d-none');
        }
        
        // Hide loading indicator
        this.hideLoadingIndicator();
    }

    /**
     * Handle critical error
     */
    handleCriticalError(error) {
        console.error('Critical error occurred:', error);
        
        // Show critical error dialog
        const message = `A critical error occurred: ${error.message}\n\nThe application may not function correctly. Please refresh the page.`;
        alert(message);
        
        // Attempt recovery
        this.attemptRecovery();
    }

    /**
     * Attempt recovery from critical error
     */
    attemptRecovery() {
        console.log('Attempting recovery...');
        
        try {
            // Stop all intervals
            if (this.performanceInterval) {
                clearInterval(this.performanceInterval);
            }
            
            if (this.qualityCheckInterval) {
                clearInterval(this.qualityCheckInterval);
            }
            
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
            }
            
            // Reinitialize components
            setTimeout(() => {
                this.initialize();
            }, 1000);
            
        } catch (error) {
            console.error('Recovery failed:', error);
        }
    }

    /**
     * Get application status
     */
    getStatus() {
        return {
            version: this.version,
            initialized: this.initialized,
            state: this.state,
            performance: this.performanceMetrics,
            components: Object.keys(this.components)
        };
    }

    /**
     * Dispose of the application
     */
    dispose() {
        console.log('Disposing 3D Paint Studio...');
        
        // Clear intervals
        if (this.performanceInterval) {
            clearInterval(this.performanceInterval);
        }
        
        if (this.qualityCheckInterval) {
            clearInterval(this.qualityCheckInterval);
        }
        
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        // Dispose components
        Object.values(this.components).forEach(component => {
            if (component && typeof component.dispose === 'function') {
                component.dispose();
            }
        });
        
        this.components = {};
        this.initialized = false;
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Create global application instance
        window.Paint3DApp = new Paint3DApp();
        
        // Initialize the application
        const success = await window.Paint3DApp.initialize();
        
        if (success) {
            console.log('3D Paint Studio is ready!');
        } else {
            console.error('3D Paint Studio failed to initialize');
        }
        
    } catch (error) {
        console.error('Failed to start 3D Paint Studio:', error);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Paint3DApp;
}