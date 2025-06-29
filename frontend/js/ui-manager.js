/**
 * UI Manager for 3D Paint Application
 * Handles all user interface interactions and state management
 */

class UIManager {
    constructor() {
        this.elements = {};
        this.state = {
            currentTool: 'standard',
            currentColor: { r: 1, g: 0, b: 0 },
            brushSize: 10,
            brushOpacity: 100,
            pressureSensitive: true,
            layerCount: 1,
            activeLayer: 0,
            isFullscreen: false,
            showGrid: false,
            showRulers: false
        };
        
        this.eventListeners = new Map();
        this.initialized = false;
    }

    /**
     * Initialize the UI manager
     */
    initialize() {
        try {
            this.cacheElements();
            this.setupEventListeners();
            this.initializeState();
            this.setupKeyboardShortcuts();
            this.setupTooltips();
            
            this.initialized = true;
            console.log('UI Manager initialized successfully');
            
            return true;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.USER_INPUT,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `UI Manager initialization failed: ${error.message}`,
                error: error
            });
            return false;
        }
    }

    /**
     * Cache DOM elements for performance
     */
    cacheElements() {
        const elementIds = [
            'brush-standard', 'brush-texture', 'brush-particle', 'brush-volumetric',
            'brush-size', 'brush-size-value', 'brush-opacity', 'brush-opacity-value',
            'brush-pressure', 'color-picker', 'undo-btn', 'redo-btn', 'clear-canvas',
            'zoom-in', 'zoom-out', 'zoom-level', 'reset-view', 'add-layer',
            'layers-list', 'ambient-light', 'directional-light', 'enable-shadows',
            'enable-particles', 'enable-physics', 'new-canvas', 'open-file',
            'save-file', 'file-input', 'fps-counter', 'memory-usage'
        ];

        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                this.elements[id] = element;
            }
        });

        // Cache color swatches
        this.elements.colorSwatches = document.querySelectorAll('.color-swatch');
        
        // Cache export buttons
        this.elements.exportButtons = document.querySelectorAll('[data-format]');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Brush tool selection
        this.addEventListeners([
            ['brush-standard', 'click', () => this.selectBrush('standard')],
            ['brush-texture', 'click', () => this.selectBrush('texture')],
            ['brush-particle', 'click', () => this.selectBrush('particle')],
            ['brush-volumetric', 'click', () => this.selectBrush('volumetric')]
        ]);

        // Brush settings
        this.addEventListeners([
            ['brush-size', 'input', this.onBrushSizeChange.bind(this)],
            ['brush-opacity', 'input', this.onBrushOpacityChange.bind(this)],
            ['brush-pressure', 'change', this.onPressureSensitivityChange.bind(this)],
            ['color-picker', 'change', this.onColorChange.bind(this)]
        ]);

        // Canvas controls
        this.addEventListeners([
            ['undo-btn', 'click', this.undo.bind(this)],
            ['redo-btn', 'click', this.redo.bind(this)],
            ['clear-canvas', 'click', this.clearCanvas.bind(this)],
            ['zoom-in', 'click', () => this.zoom(0.1)],
            ['zoom-out', 'click', () => this.zoom(-0.1)],
            ['reset-view', 'click', this.resetView.bind(this)]
        ]);

        // Layer management
        this.addEventListeners([
            ['add-layer', 'click', this.addLayer.bind(this)]
        ]);

        // Lighting controls
        this.addEventListeners([
            ['ambient-light', 'input', this.onAmbientLightChange.bind(this)],
            ['directional-light', 'input', this.onDirectionalLightChange.bind(this)],
            ['enable-shadows', 'change', this.onShadowsToggle.bind(this)],
            ['enable-particles', 'change', this.onParticlesToggle.bind(this)],
            ['enable-physics', 'change', this.onPhysicsToggle.bind(this)]
        ]);

        // File operations
        this.addEventListeners([
            ['new-canvas', 'click', this.newCanvas.bind(this)],
            ['open-file', 'click', this.openFile.bind(this)],
            ['save-file', 'click', this.saveFile.bind(this)],
            ['file-input', 'change', this.onFileSelected.bind(this)]
        ]);

        // Color swatches
        this.elements.colorSwatches?.forEach((swatch, index) => {
            swatch.addEventListener('click', () => this.selectColorSwatch(swatch));
        });

        // Export buttons
        this.elements.exportButtons?.forEach(button => {
            button.addEventListener('click', (e) => {
                const format = e.target.getAttribute('data-format');
                this.exportCanvas(format);
            });
        });

        // Window events
        window.addEventListener('beforeunload', this.onBeforeUnload.bind(this));
        window.addEventListener('keydown', this.onKeyDown.bind(this));
        window.addEventListener('keyup', this.onKeyUp.bind(this));
    }

    /**
     * Helper method to add multiple event listeners
     * @param {Array} listeners - Array of [elementId, event, handler] tuples
     */
    addEventListeners(listeners) {
        listeners.forEach(([elementId, event, handler]) => {
            const element = this.elements[elementId];
            if (element) {
                element.addEventListener(event, handler);
                
                // Store for cleanup
                if (!this.eventListeners.has(elementId)) {
                    this.eventListeners.set(elementId, []);
                }
                this.eventListeners.get(elementId).push({ event, handler });
            }
        });
    }

    /**
     * Initialize UI state
     */
    initializeState() {
        // Set default brush
        this.selectBrush(this.state.currentTool);
        
        // Set default color
        this.updateColorPicker();
        
        // Initialize sliders
        this.updateBrushSizeUI();
        this.updateBrushOpacityUI();
        
        // Initialize checkboxes
        if (this.elements['brush-pressure']) {
            this.elements['brush-pressure'].checked = this.state.pressureSensitive;
        }

        // Initialize lighting
        this.updateLightingUI();
    }

    /**
     * Set up keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        this.shortcuts = {
            'KeyB': () => this.selectBrush('standard'),
            'KeyT': () => this.selectBrush('texture'),
            'KeyP': () => this.selectBrush('particle'),
            'KeyV': () => this.selectBrush('volumetric'),
            'KeyZ': (e) => e.ctrlKey || e.metaKey ? this.undo() : null,
            'KeyY': (e) => e.ctrlKey || e.metaKey ? this.redo() : null,
            'KeyS': (e) => e.ctrlKey || e.metaKey ? (e.preventDefault(), this.saveFile()) : null,
            'KeyO': (e) => e.ctrlKey || e.metaKey ? (e.preventDefault(), this.openFile()) : null,
            'KeyN': (e) => e.ctrlKey || e.metaKey ? (e.preventDefault(), this.newCanvas()) : null,
            'Space': (e) => (e.preventDefault(), this.togglePanMode()),
            'Equal': () => this.zoom(0.1),
            'Minus': () => this.zoom(-0.1),
            'Digit0': () => this.resetView(),
            'KeyF': () => this.toggleFullscreen(),
            'KeyG': () => this.toggleGrid(),
            'KeyR': () => this.toggleRulers()
        };
    }

    /**
     * Set up tooltips
     */
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        tooltipElements.forEach(element => {
            // Simple tooltip implementation
            element.addEventListener('mouseenter', this.showTooltip.bind(this));
            element.addEventListener('mouseleave', this.hideTooltip.bind(this));
        });
    }

    /**
     * Brush selection methods
     */
    selectBrush(brushName) {
        try {
            // Update UI
            document.querySelectorAll('.btn-outline-primary').forEach(btn => {
                btn.classList.remove('active');
            });
            
            const brushButton = this.elements[`brush-${brushName}`];
            if (brushButton) {
                brushButton.classList.add('active');
            }

            // Update brush engine
            if (window.BrushEngine) {
                window.BrushEngine.setCurrentBrush(brushName);
            }

            this.state.currentTool = brushName;
            console.log(`Selected brush: ${brushName}`);

        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.USER_INPUT,
                level: window.ErrorHandler.errorLevels.WARNING,
                message: `Failed to select brush: ${error.message}`,
                error: error
            });
        }
    }

    /**
     * Brush settings event handlers
     */
    onBrushSizeChange(event) {
        this.state.brushSize = parseInt(event.target.value);
        this.updateBrushSizeUI();
        this.updateBrushEngine();
    }

    onBrushOpacityChange(event) {
        this.state.brushOpacity = parseInt(event.target.value);
        this.updateBrushOpacityUI();
        this.updateBrushEngine();
    }

    onPressureSensitivityChange(event) {
        this.state.pressureSensitive = event.target.checked;
        this.updateBrushEngine();
    }

    onColorChange(event) {
        const color = this.hexToRgb(event.target.value);
        if (color) {
            this.state.currentColor = {
                r: color.r / 255,
                g: color.g / 255,
                b: color.b / 255
            };
            this.updateBrushEngine();
            this.updateColorSwatches();
        }
    }

    /**
     * Update brush engine with current settings
     */
    updateBrushEngine() {
        if (window.BrushEngine) {
            window.BrushEngine.updateSettings({
                size: this.state.brushSize,
                opacity: this.state.brushOpacity / 100,
                pressureSensitive: this.state.pressureSensitive,
                color: this.state.currentColor
            });
        }
    }

    /**
     * UI update methods
     */
    updateBrushSizeUI() {
        if (this.elements['brush-size-value']) {
            this.elements['brush-size-value'].textContent = `${this.state.brushSize}px`;
        }
    }

    updateBrushOpacityUI() {
        if (this.elements['brush-opacity-value']) {
            this.elements['brush-opacity-value'].textContent = `${this.state.brushOpacity}%`;
        }
    }

    updateColorPicker() {
        const hex = this.rgbToHex(
            Math.round(this.state.currentColor.r * 255),
            Math.round(this.state.currentColor.g * 255),
            Math.round(this.state.currentColor.b * 255)
        );
        
        if (this.elements['color-picker']) {
            this.elements['color-picker'].value = hex;
        }
    }

    updateColorSwatches() {
        this.elements.colorSwatches?.forEach(swatch => {
            swatch.classList.remove('active');
        });
    }

    /**
     * Color swatch selection
     */
    selectColorSwatch(swatch) {
        const color = swatch.getAttribute('data-color');
        if (color) {
            const rgb = this.hexToRgb(color);
            if (rgb) {
                this.state.currentColor = {
                    r: rgb.r / 255,
                    g: rgb.g / 255,
                    b: rgb.b / 255
                };
                
                this.updateColorPicker();
                this.updateBrushEngine();
                
                // Update swatch selection
                this.elements.colorSwatches?.forEach(s => s.classList.remove('active'));
                swatch.classList.add('active');
            }
        }
    }

    /**
     * Canvas control methods
     */
    undo() {
        if (window.BrushEngine) {
            const success = window.BrushEngine.undo();
            this.showMessage(success ? 'Undid last action' : 'Nothing to undo', 'info');
        }
    }

    redo() {
        // Redo functionality would need to be implemented in BrushEngine
        this.showMessage('Redo not implemented yet', 'warning');
    }

    clearCanvas() {
        const confirmed = confirm('Are you sure you want to clear the canvas?');
        if (confirmed && window.BrushEngine) {
            window.BrushEngine.clearAll();
            this.showMessage('Canvas cleared', 'success');
        }
    }

    zoom(delta) {
        if (window.Canvas3D && window.Canvas3D.camera) {
            window.Canvas3D.zoom(delta);
            this.updateZoomUI();
        }
    }

    resetView() {
        if (window.Canvas3D && window.Canvas3D.camera) {
            window.Canvas3D.camera.position.set(0, 0, 5);
            window.Canvas3D.camera.lookAt(0, 0, 0);
            this.updateZoomUI();
        }
    }

    updateZoomUI() {
        if (this.elements['zoom-level'] && window.Canvas3D && window.Canvas3D.camera) {
            const zoom = Math.round((5 / window.Canvas3D.camera.position.z) * 100);
            this.elements['zoom-level'].textContent = `${zoom}%`;
        }
    }

    /**
     * Layer management
     */
    addLayer() {
        this.state.layerCount++;
        this.createLayerElement(this.state.layerCount - 1);
        this.showMessage(`Layer ${this.state.layerCount} added`, 'success');
    }

    createLayerElement(index) {
        const layersList = this.elements['layers-list'];
        if (!layersList) return;

        const layerElement = document.createElement('div');
        layerElement.className = 'layer-item';
        layerElement.setAttribute('data-layer', index);
        
        layerElement.innerHTML = `
            <div class="layer-preview"></div>
            <div class="layer-info">
                <span class="layer-name">Layer ${index + 1}</span>
                <div class="layer-controls">
                    <input type="range" class="layer-opacity" min="0" max="100" value="100">
                    <button class="btn btn-sm btn-outline-danger layer-delete">×</button>
                </div>
            </div>
        `;

        // Add event listeners
        layerElement.addEventListener('click', () => this.selectLayer(index));
        layerElement.querySelector('.layer-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteLayer(index);
        });

        layersList.appendChild(layerElement);
    }

    selectLayer(index) {
        document.querySelectorAll('.layer-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const layerElement = document.querySelector(`[data-layer="${index}"]`);
        if (layerElement) {
            layerElement.classList.add('active');
            this.state.activeLayer = index;
        }
    }

    deleteLayer(index) {
        const layerElement = document.querySelector(`[data-layer="${index}"]`);
        if (layerElement && this.state.layerCount > 1) {
            layerElement.remove();
            this.state.layerCount--;
            this.showMessage(`Layer ${index + 1} deleted`, 'info');
        }
    }

    /**
     * Lighting controls
     */
    onAmbientLightChange(event) {
        const intensity = parseInt(event.target.value) / 100;
        if (window.Canvas3D && window.Canvas3D.lights[0]) {
            window.Canvas3D.lights[0].intensity = intensity;
        }
    }

    onDirectionalLightChange(event) {
        const intensity = parseInt(event.target.value) / 100;
        if (window.Canvas3D && window.Canvas3D.lights[1]) {
            window.Canvas3D.lights[1].intensity = intensity;
        }
    }

    onShadowsToggle(event) {
        const enabled = event.target.checked;
        if (window.Canvas3D && window.Canvas3D.renderer) {
            window.Canvas3D.renderer.shadowMap.enabled = enabled;
            window.Canvas3D.shadowsEnabled = enabled;
        }
    }

    onParticlesToggle(event) {
        const enabled = event.target.checked;
        if (window.Canvas3D) {
            window.Canvas3D.particlesEnabled = enabled;
        }
        if (window.BrushEngine) {
            window.BrushEngine.updateSettings({ particlesEnabled: enabled });
        }
    }

    onPhysicsToggle(event) {
        const enabled = event.target.checked;
        if (window.Canvas3D) {
            window.Canvas3D.physicsEnabled = enabled;
        }
        if (window.BrushEngine) {
            window.BrushEngine.physicsEnabled = enabled;
        }
    }

    updateLightingUI() {
        // Set default lighting values
        if (this.elements['ambient-light']) {
            this.elements['ambient-light'].value = 30;
        }
        if (this.elements['directional-light']) {
            this.elements['directional-light'].value = 70;
        }
    }

    /**
     * File operations
     */
    newCanvas() {
        const confirmed = confirm('Create a new canvas? Unsaved changes will be lost.');
        if (confirmed) {
            this.clearCanvas();
            this.showMessage('New canvas created', 'success');
        }
    }

    openFile() {
        if (this.elements['file-input']) {
            this.elements['file-input'].click();
        }
    }

    onFileSelected(event) {
        const file = event.target.files[0];
        if (file) {
            this.loadFile(file);
        }
    }

    async loadFile(file) {
        try {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Load file content
                console.log('File loaded:', file.name);
                this.showMessage(`File loaded: ${file.name}`, 'success');
            };
            reader.readAsDataURL(file);
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.FILE_SYSTEM,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Failed to load file: ${error.message}`,
                error: error
            });
        }
    }

    saveFile() {
        try {
            // Export canvas as image
            this.exportCanvas('png');
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.FILE_SYSTEM,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Failed to save file: ${error.message}`,
                error: error
            });
        }
    }

    /**
     * Export functionality
     */
    exportCanvas(format) {
        try {
            if (!window.Canvas3D || !window.Canvas3D.renderer) {
                throw new Error('Canvas not initialized');
            }

            const canvas = window.Canvas3D.renderer.domElement;
            
            switch (format) {
                case 'png':
                    this.downloadCanvas(canvas, 'canvas.png', 'image/png');
                    break;
                case 'jpg':
                    this.downloadCanvas(canvas, 'canvas.jpg', 'image/jpeg');
                    break;
                case 'obj':
                    this.exportOBJ();
                    break;
                case 'psd':
                    this.showMessage('PSD export not implemented yet', 'warning');
                    break;
                default:
                    throw new Error(`Unsupported format: ${format}`);
            }
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.FILE_SYSTEM,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Export failed: ${error.message}`,
                error: error
            });
        }
    }

    downloadCanvas(canvas, filename, mimeType) {
        canvas.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showMessage(`Exported as ${filename}`, 'success');
        }, mimeType);
    }

    exportOBJ() {
        // OBJ export would need to be implemented
        this.showMessage('OBJ export not implemented yet', 'warning');
    }

    /**
     * Special features
     */
    togglePanMode() {
        // Toggle between paint and pan modes
        const container = document.querySelector('.canvas-container');
        if (container) {
            container.classList.toggle('panning');
        }
    }

    toggleFullscreen() {
        const container = document.querySelector('.canvas-container');
        if (container) {
            if (!this.state.isFullscreen) {
                container.requestFullscreen();
                this.state.isFullscreen = true;
            } else {
                document.exitFullscreen();
                this.state.isFullscreen = false;
            }
        }
    }

    toggleGrid() {
        const container = document.querySelector('.canvas-container');
        if (container) {
            container.classList.toggle('show-grid');
            this.state.showGrid = !this.state.showGrid;
        }
    }

    toggleRulers() {
        this.state.showRulers = !this.state.showRulers;
        // Ruler implementation would go here
    }

    /**
     * Event handlers
     */
    onKeyDown(event) {
        const handler = this.shortcuts[event.code];
        if (handler) {
            handler(event);
        }
    }

    onKeyUp(event) {
        // Handle key releases if needed
    }

    onBeforeUnload(event) {
        // Warn user about unsaved changes
        event.preventDefault();
        event.returnValue = '';
    }

    /**
     * Tooltip methods
     */
    showTooltip(event) {
        const title = event.target.getAttribute('title');
        if (title) {
            // Simple tooltip implementation
            console.log('Tooltip:', title);
        }
    }

    hideTooltip(event) {
        // Hide tooltip
    }

    /**
     * Utility methods
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    rgbToHex(r, g, b) {
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }

    showMessage(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // You could implement a toast notification system here
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }

    /**
     * Performance monitoring
     */
    updatePerformanceUI() {
        // Update FPS counter
        if (this.elements['fps-counter'] && window.Canvas3D) {
            this.elements['fps-counter'].textContent = `FPS: ${window.Canvas3D.currentFPS}`;
        }
        
        // Update memory usage
        if (this.elements['memory-usage']) {
            const memoryInfo = performance.memory || { usedJSHeapSize: 0 };
            const memMB = Math.round(memoryInfo.usedJSHeapSize / 1024 / 1024);
            this.elements['memory-usage'].textContent = `RAM: ${memMB}MB`;
        }
    }

    /**
     * Cleanup
     */
    dispose() {
        // Remove event listeners
        this.eventListeners.forEach((listeners, elementId) => {
            const element = this.elements[elementId];
            if (element) {
                listeners.forEach(({ event, handler }) => {
                    element.removeEventListener(event, handler);
                });
            }
        });
        
        this.eventListeners.clear();
        this.elements = {};
        this.initialized = false;
    }
}

// Create global UI manager instance
window.UIManager = new UIManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
}