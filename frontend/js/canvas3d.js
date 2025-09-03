/**
 * 3D Canvas Engine for Paint Application
 * Provides comprehensive 3D rendering with hardware acceleration
 */

class Canvas3D {
    constructor() {
        this.canvas = null;
        this.webglUtils = null;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        
        // Rendering state
        this.isInitialized = false;
        this.isRendering = false;
        this.animationFrameId = null;
        
        // Performance tracking
        this.frameCount = 0;
        this.lastFPSUpdate = performance.now();
        this.currentFPS = 60;
        this.targetFPS = 60;
        
        // Memory management
        this.memoryUsage = {
            textures: 0,
            buffers: 0,
            programs: 0
        };
        
        // Scene objects
        this.layers = [];
        this.brushStrokes = [];
        this.particles = [];
        this.lights = [];
        
        // Interaction state
        this.mouseState = {
            isDown: false,
            lastX: 0,
            lastY: 0,
            button: -1
        };
        
        // Quality settings
        this.qualityLevel = 'high'; // high, medium, low
        this.shadowsEnabled = true;
        this.particlesEnabled = true;
        this.physicsEnabled = true;
        
        // Bind methods
        this.render = this.render.bind(this);
        this.onMouseDown = this.onMouseDown.bind(this);
        this.onMouseMove = this.onMouseMove.bind(this);
        this.onMouseUp = this.onMouseUp.bind(this);
        this.onResize = this.onResize.bind(this);
    }

    /**
     * Initialize the 3D canvas engine
     * @param {string} canvasId - Canvas element ID
     */
    async initialize(canvasId = 'canvas3d') {
        try {
            // Get canvas element
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) {
                throw new Error(`Canvas element '${canvasId}' not found`);
            }

            // Initialize WebGL
            this.webglUtils = new WebGLUtils();
            const success = this.webglUtils.initialize(this.canvas, {
                alpha: false,
                depth: true,
                stencil: true,
                antialias: true,
                powerPreference: 'high-performance'
            });

            if (!success) {
                throw new Error('WebGL initialization failed');
            }

            // Set up Three.js scene
            await this.initializeThreeJS();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize default scene
            this.createDefaultScene();
            
            // Start render loop
            this.startRenderLoop();
            
            this.isInitialized = true;
            console.log('3D Canvas Engine initialized successfully');
            
            // Hide loading indicator
            this.hideLoadingIndicator();
            
            return true;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.CANVAS,
                level: window.ErrorHandler.errorLevels.CRITICAL,
                message: `3D Canvas initialization failed: ${error.message}`,
                error: error
            });
            
            this.showErrorState();
            return false;
        }
    }

    /**
     * Initialize Three.js scene, camera, and renderer
     */
    async initializeThreeJS() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xffffff);
        
        // Create camera
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(0, 0, 5);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            context: this.webglUtils.gl,
            antialias: true,
            alpha: false,
            powerPreference: 'high-performance'
        });
        
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        
        // Enable shadows
        this.renderer.shadowMap.enabled = this.shadowsEnabled;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // Enable tone mapping for realistic lighting
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
        
        // Load shaders
        await this.loadShaders();
    }

    /**
     * Load custom shaders for advanced effects
     */
    async loadShaders() {
        // Basic paint shader
        const paintVertexShader = `
            varying vec2 vUv;
            varying vec3 vNormal;
            varying vec3 vPosition;
            
            void main() {
                vUv = uv;
                vNormal = normalize(normalMatrix * normal);
                vPosition = position;
                
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `;
        
        const paintFragmentShader = `
            uniform vec3 color;
            uniform float opacity;
            uniform float metalness;
            uniform float roughness;
            uniform vec3 lightDirection;
            uniform float ambientIntensity;
            
            varying vec2 vUv;
            varying vec3 vNormal;
            varying vec3 vPosition;
            
            void main() {
                vec3 normal = normalize(vNormal);
                float lightIntensity = max(dot(normal, normalize(lightDirection)), 0.0) + ambientIntensity;
                
                vec3 finalColor = color * lightIntensity;
                gl_FragColor = vec4(finalColor, opacity);
            }
        `;
        
        // Create paint material
        this.paintMaterial = new THREE.ShaderMaterial({
            vertexShader: paintVertexShader,
            fragmentShader: paintFragmentShader,
            uniforms: {
                color: { value: new THREE.Color(1, 0, 0) },
                opacity: { value: 1.0 },
                metalness: { value: 0.0 },
                roughness: { value: 0.5 },
                lightDirection: { value: new THREE.Vector3(1, 1, 1) },
                ambientIntensity: { value: 0.3 }
            },
            transparent: true
        });
    }

    /**
     * Create default scene with lights and environment
     */
    createDefaultScene() {
        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);
        
        // Add directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.7);
        directionalLight.position.set(10, 10, 10);
        directionalLight.castShadow = this.shadowsEnabled;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        this.lights.push(directionalLight);
        
        // Create default canvas plane
        this.createCanvasPlane();
        
        // Create coordinate system helper (for debugging)
        if (window.location.search.includes('debug=true')) {
            const axesHelper = new THREE.AxesHelper(5);
            this.scene.add(axesHelper);
        }
    }

    /**
     * Create the main canvas plane for 2D painting
     */
    createCanvasPlane() {
        const geometry = new THREE.PlaneGeometry(10, 8);
        const material = new THREE.MeshLambertMaterial({
            color: 0xffffff,
            transparent: true
        });
        
        this.canvasPlane = new THREE.Mesh(geometry, material);
        this.canvasPlane.receiveShadow = true;
        this.scene.add(this.canvasPlane);
        
        // Create render target for painting
        this.paintRenderTarget = new THREE.WebGLRenderTarget(1024, 1024, {
            minFilter: THREE.LinearFilter,
            magFilter: THREE.LinearFilter,
            stencilBuffer: true
        });
        
        // Apply render target as texture
        material.map = this.paintRenderTarget.texture;
    }

    /**
     * Set up event listeners for interaction
     */
    setupEventListeners() {
        // Mouse events
        this.canvas.addEventListener('mousedown', this.onMouseDown);
        this.canvas.addEventListener('mousemove', this.onMouseMove);
        this.canvas.addEventListener('mouseup', this.onMouseUp);
        this.canvas.addEventListener('wheel', this.onWheel.bind(this));
        
        // Touch events for mobile/tablet support
        this.canvas.addEventListener('touchstart', this.onTouchStart.bind(this));
        this.canvas.addEventListener('touchmove', this.onTouchMove.bind(this));
        this.canvas.addEventListener('touchend', this.onTouchEnd.bind(this));
        
        // Resize event
        window.addEventListener('resize', this.onResize);
        
        // Context menu (disable)
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    }

    /**
     * Start the render loop
     */
    startRenderLoop() {
        if (this.isRendering) return;
        
        this.isRendering = true;
        this.render();
    }

    /**
     * Stop the render loop
     */
    stopRenderLoop() {
        this.isRendering = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    /**
     * Main render loop
     */
    render() {
        if (!this.isRendering || !this.isInitialized) return;
        
        try {
            const startTime = performance.now();
            
            // Update performance metrics
            this.updatePerformanceMetrics();
            
            // Update particles if enabled
            if (this.particlesEnabled) {
                this.updateParticles();
            }
            
            // Update physics if enabled
            if (this.physicsEnabled) {
                this.updatePhysics();
            }
            
            // Render scene
            this.renderer.render(this.scene, this.camera);
            
            // Check for WebGL errors
            this.webglUtils.checkError('Render loop');
            
            // Calculate frame time
            const frameTime = performance.now() - startTime;
            this.updateFrameTime(frameTime);
            
            // Schedule next frame
            this.animationFrameId = requestAnimationFrame(this.render);
            
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.CANVAS,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Render loop error: ${error.message}`,
                error: error
            });
            
            // Try to recover
            setTimeout(() => {
                if (this.isRendering) {
                    this.render();
                }
            }, 100);
        }
    }

    /**
     * Update performance metrics
     */
    updatePerformanceMetrics() {
        this.frameCount++;
        const now = performance.now();
        
        if (now - this.lastFPSUpdate >= 1000) {
            this.currentFPS = Math.round((this.frameCount * 1000) / (now - this.lastFPSUpdate));
            this.frameCount = 0;
            this.lastFPSUpdate = now;
            
            // Update UI
            this.updatePerformanceUI();
            
            // Check for performance issues
            if (this.currentFPS < this.targetFPS * 0.8) {
                this.handlePerformanceIssue();
            }
        }
    }

    /**
     * Update particles system
     */
    updateParticles() {
        this.particles.forEach((particle, index) => {
            particle.update();
            if (particle.isDead()) {
                this.particles.splice(index, 1);
                this.scene.remove(particle.mesh);
            }
        });
    }

    /**
     * Update physics simulation
     */
    updatePhysics() {
        // Simple physics for paint drops and splashes
        // This would be expanded with a proper physics engine
        this.brushStrokes.forEach(stroke => {
            if (stroke.physics) {
                stroke.updatePhysics();
            }
        });
    }

    /**
     * Update frame time tracking
     * @param {number} frameTime - Time taken for this frame
     */
    updateFrameTime(frameTime) {
        // Monitor frame time for performance issues
        if (frameTime > 16.67) { // Over 16.67ms indicates < 60fps
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.PERFORMANCE,
                level: window.ErrorHandler.errorLevels.WARNING,
                message: `Frame time exceeded target: ${frameTime.toFixed(2)}ms`,
                frameTime: frameTime
            });
        }
    }

    /**
     * Handle performance issues
     */
    handlePerformanceIssue() {
        console.warn(`Performance issue detected: ${this.currentFPS} FPS`);
        
        // Automatically reduce quality if performance is poor
        if (this.qualityLevel === 'high' && this.currentFPS < 30) {
            this.setQuality('medium');
        } else if (this.qualityLevel === 'medium' && this.currentFPS < 20) {
            this.setQuality('low');
        }
    }

    /**
     * Set rendering quality level
     * @param {string} quality - Quality level ('high', 'medium', 'low')
     */
    setQuality(quality) {
        this.qualityLevel = quality;
        
        switch (quality) {
            case 'low':
                this.renderer.setPixelRatio(1);
                this.shadowsEnabled = false;
                this.particlesEnabled = false;
                this.renderer.shadowMap.enabled = false;
                break;
                
            case 'medium':
                this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
                this.shadowsEnabled = true;
                this.particlesEnabled = false;
                this.renderer.shadowMap.enabled = true;
                break;
                
            case 'high':
                this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                this.shadowsEnabled = true;
                this.particlesEnabled = true;
                this.renderer.shadowMap.enabled = true;
                break;
        }
        
        console.log(`Quality set to: ${quality}`);
    }

    /**
     * Mouse event handlers
     */
    onMouseDown(event) {
        this.mouseState.isDown = true;
        this.mouseState.button = event.button;
        this.mouseState.lastX = event.clientX;
        this.mouseState.lastY = event.clientY;
        
        // Start painting
        if (event.button === 0) { // Left mouse button
            this.startPainting(event);
        } else if (event.button === 1) { // Middle mouse button
            this.startPanning(event);
        }
    }

    onMouseMove(event) {
        if (!this.mouseState.isDown) return;
        
        const deltaX = event.clientX - this.mouseState.lastX;
        const deltaY = event.clientY - this.mouseState.lastY;
        
        if (this.mouseState.button === 0) {
            this.continuePainting(event, deltaX, deltaY);
        } else if (this.mouseState.button === 1) {
            this.continuePanning(deltaX, deltaY);
        }
        
        this.mouseState.lastX = event.clientX;
        this.mouseState.lastY = event.clientY;
    }

    onMouseUp(event) {
        if (this.mouseState.button === 0) {
            this.endPainting(event);
        } else if (this.mouseState.button === 1) {
            this.endPanning(event);
        }
        
        this.mouseState.isDown = false;
        this.mouseState.button = -1;
    }

    onWheel(event) {
        event.preventDefault();
        const delta = event.deltaY;
        this.zoom(delta > 0 ? -0.1 : 0.1);
    }

    /**
     * Touch event handlers
     */
    onTouchStart(event) {
        event.preventDefault();
        if (event.touches.length === 1) {
            const touch = event.touches[0];
            this.onMouseDown({
                button: 0,
                clientX: touch.clientX,
                clientY: touch.clientY
            });
        }
    }

    onTouchMove(event) {
        event.preventDefault();
        if (event.touches.length === 1) {
            const touch = event.touches[0];
            this.onMouseMove({
                clientX: touch.clientX,
                clientY: touch.clientY
            });
        }
    }

    onTouchEnd(event) {
        event.preventDefault();
        this.onMouseUp({ button: 0 });
    }

    /**
     * Painting methods
     */
    startPainting(event) {
        // Get world coordinates from screen coordinates
        const worldPos = this.screenToWorld(event.clientX, event.clientY);
        
        // Create new brush stroke
        const brushStroke = this.createBrushStroke(worldPos);
        this.brushStrokes.push(brushStroke);
        
        console.log('Started painting at:', worldPos);
    }

    continuePainting(event, deltaX, deltaY) {
        const worldPos = this.screenToWorld(event.clientX, event.clientY);
        
        // Add point to current brush stroke
        if (this.brushStrokes.length > 0) {
            const currentStroke = this.brushStrokes[this.brushStrokes.length - 1];
            currentStroke.addPoint(worldPos);
        }
    }

    endPainting(event) {
        console.log('Ended painting');
        
        // Finalize current brush stroke
        if (this.brushStrokes.length > 0) {
            const currentStroke = this.brushStrokes[this.brushStrokes.length - 1];
            currentStroke.finalize();
        }
    }

    /**
     * Camera controls
     */
    startPanning(event) {
        this.canvas.style.cursor = 'grabbing';
    }

    continuePanning(deltaX, deltaY) {
        // Pan the camera
        this.camera.position.x -= deltaX * 0.01;
        this.camera.position.y += deltaY * 0.01;
    }

    endPanning(event) {
        this.canvas.style.cursor = 'crosshair';
    }

    zoom(delta) {
        this.camera.position.z += delta;
        this.camera.position.z = Math.max(0.1, Math.min(100, this.camera.position.z));
    }

    /**
     * Utility methods
     */
    screenToWorld(screenX, screenY) {
        const rect = this.canvas.getBoundingClientRect();
        const x = ((screenX - rect.left) / rect.width) * 2 - 1;
        const y = -((screenY - rect.top) / rect.height) * 2 + 1;
        
        const vector = new THREE.Vector3(x, y, 0.5);
        vector.unproject(this.camera);
        
        const dir = vector.sub(this.camera.position).normalize();
        const distance = -this.camera.position.z / dir.z;
        const pos = this.camera.position.clone().add(dir.multiplyScalar(distance));
        
        return pos;
    }

    createBrushStroke(startPos) {
        // This would be expanded with actual brush stroke implementation
        return {
            points: [startPos],
            addPoint: function(pos) {
                this.points.push(pos);
            },
            finalize: function() {
                console.log('Brush stroke finalized with', this.points.length, 'points');
            }
        };
    }

    /**
     * Resize handler
     */
    onResize() {
        if (!this.camera || !this.renderer) return;
        
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
        
        // Update WebGL viewport
        this.webglUtils.updateViewport();
    }

    /**
     * UI update methods
     */
    updatePerformanceUI() {
        const fpsCounter = document.getElementById('fps-counter');
        if (fpsCounter) {
            fpsCounter.textContent = `FPS: ${this.currentFPS}`;
        }
        
        // Update memory usage
        const memoryUsage = document.getElementById('memory-usage');
        if (memoryUsage) {
            const info = this.renderer.info;
            const memMB = Math.round((info.memory.geometries + info.memory.textures) / 1024);
            memoryUsage.textContent = `RAM: ${memMB}MB`;
        }
    }

    hideLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    showErrorState() {
        const container = document.querySelector('.canvas-container');
        if (container) {
            container.classList.add('error');
        }
    }

    /**
     * Memory management
     */
    clearCaches() {
        // Clear Three.js caches
        THREE.Cache.clear();
        
        // Clear renderer info
        if (this.renderer) {
            this.renderer.info.reset();
        }
    }

    clearGPUBuffers() {
        if (this.renderer) {
            this.renderer.clear();
        }
    }

    /**
     * Cleanup and disposal
     */
    dispose() {
        this.stopRenderLoop();
        
        // Remove event listeners
        if (this.canvas) {
            this.canvas.removeEventListener('mousedown', this.onMouseDown);
            this.canvas.removeEventListener('mousemove', this.onMouseMove);
            this.canvas.removeEventListener('mouseup', this.onMouseUp);
            this.canvas.removeEventListener('wheel', this.onWheel);
        }
        
        window.removeEventListener('resize', this.onResize);
        
        // Dispose Three.js objects
        if (this.scene) {
            this.scene.traverse((object) => {
                if (object.geometry) object.geometry.dispose();
                if (object.material) {
                    if (Array.isArray(object.material)) {
                        object.material.forEach(material => material.dispose());
                    } else {
                        object.material.dispose();
                    }
                }
            });
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.webglUtils) {
            this.webglUtils.dispose();
        }
        
        this.isInitialized = false;
    }

    /**
     * Reinitialize after context loss
     */
    reinitialize() {
        this.dispose();
        return this.initialize(this.canvas.id);
    }
}

// Create global instance
window.Canvas3D = new Canvas3D();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Canvas3D;
}