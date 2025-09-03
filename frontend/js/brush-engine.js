/**
 * Advanced Brush Engine for 3D Paint Application
 * Provides comprehensive brush systems with physics simulation
 */

class BrushEngine {
    constructor() {
        this.brushes = new Map();
        this.currentBrush = null;
        this.brushSettings = {
            size: 10,
            opacity: 1.0,
            flow: 1.0,
            hardness: 0.8,
            spacing: 0.1,
            pressureSensitive: true,
            tiltSensitive: false,
            rotationSensitive: false,
            color: { r: 1, g: 0, b: 0 },
            blendMode: 'normal'
        };
        
        // Physics simulation
        this.physicsEnabled = true;
        this.gravity = -9.81;
        this.viscosity = 0.1;
        this.surfaceTension = 0.5;
        
        // Performance optimization
        this.strokeCache = new Map();
        this.maxCacheSize = 100;
        
        // Stroke state
        this.currentStroke = null;
        this.strokeHistory = [];
        this.maxHistorySize = 50;
        
        // Particle system
        this.particles = [];
        this.maxParticles = 1000;
        
        this.initializeBrushes();
    }

    /**
     * Initialize default brush types
     */
    initializeBrushes() {
        // Standard brush
        this.registerBrush('standard', new StandardBrush());
        
        // Texture brush
        this.registerBrush('texture', new TextureBrush());
        
        // Particle brush
        this.registerBrush('particle', new ParticleBrush());
        
        // Volumetric brush
        this.registerBrush('volumetric', new VolumetricBrush());
        
        // Physics brush
        this.registerBrush('physics', new PhysicsBrush());
        
        // Set default brush
        this.setCurrentBrush('standard');
    }

    /**
     * Register a new brush type
     * @param {string} name - Brush name
     * @param {Object} brushInstance - Brush implementation
     */
    registerBrush(name, brushInstance) {
        this.brushes.set(name, brushInstance);
        console.log(`Brush registered: ${name}`);
    }

    /**
     * Set the current brush
     * @param {string} brushName - Name of the brush to use
     */
    setCurrentBrush(brushName) {
        if (this.brushes.has(brushName)) {
            this.currentBrush = this.brushes.get(brushName);
            this.currentBrush.setSettings(this.brushSettings);
            console.log(`Current brush set to: ${brushName}`);
            
            // Update UI cursor
            this.updateCursor(brushName);
        } else {
            console.error(`Brush not found: ${brushName}`);
        }
    }

    /**
     * Update brush settings
     * @param {Object} newSettings - New brush settings
     */
    updateSettings(newSettings) {
        this.brushSettings = { ...this.brushSettings, ...newSettings };
        
        if (this.currentBrush) {
            this.currentBrush.setSettings(this.brushSettings);
        }
        
        // Update UI
        this.updateSettingsUI();
    }

    /**
     * Start a new brush stroke
     * @param {Object} startPoint - Starting point with coordinates and pressure
     */
    startStroke(startPoint) {
        try {
            if (!this.currentBrush) {
                throw new Error('No brush selected');
            }

            // Create new stroke
            this.currentStroke = new BrushStroke({
                brush: this.currentBrush,
                settings: { ...this.brushSettings },
                startPoint: startPoint,
                timestamp: performance.now()
            });

            // Initialize stroke
            this.currentStroke.initialize();

            // Add to history
            this.addToHistory(this.currentStroke);

            console.log('Brush stroke started at:', startPoint);
            
            return this.currentStroke;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.BRUSH,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Failed to start brush stroke: ${error.message}`,
                error: error
            });
            return null;
        }
    }

    /**
     * Continue the current brush stroke
     * @param {Object} point - Point data with coordinates, pressure, tilt, etc.
     */
    continueStroke(point) {
        try {
            if (!this.currentStroke) {
                console.warn('No active stroke to continue');
                return;
            }

            // Add point to stroke
            this.currentStroke.addPoint(point);

            // Update rendering
            this.updateStrokeRendering();

            // Handle particle effects
            if (this.brushSettings.particlesEnabled) {
                this.generateParticles(point);
            }

            // Handle physics simulation
            if (this.physicsEnabled && this.currentStroke.hasPhysics()) {
                this.updatePhysics(point);
            }

        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.BRUSH,
                level: window.ErrorHandler.errorLevels.WARNING,
                message: `Error continuing brush stroke: ${error.message}`,
                error: error
            });
        }
    }

    /**
     * End the current brush stroke
     * @param {Object} endPoint - Final point data
     */
    endStroke(endPoint) {
        try {
            if (!this.currentStroke) {
                console.warn('No active stroke to end');
                return;
            }

            // Add final point
            if (endPoint) {
                this.currentStroke.addPoint(endPoint);
            }

            // Finalize stroke
            this.currentStroke.finalize();

            // Cache the stroke for optimization
            this.cacheStroke(this.currentStroke);

            // Generate final particle burst if applicable
            if (this.brushSettings.particlesEnabled) {
                this.generateStrokeEndParticles(this.currentStroke);
            }

            console.log(`Brush stroke completed with ${this.currentStroke.points.length} points`);
            
            // Clear current stroke
            this.currentStroke = null;

        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.BRUSH,
                level: window.ErrorHandler.errorLevels.WARNING,
                message: `Error ending brush stroke: ${error.message}`,
                error: error
            });
        }
    }

    /**
     * Update stroke rendering
     */
    updateStrokeRendering() {
        if (!this.currentStroke || !window.Canvas3D.isInitialized) return;

        // Update stroke mesh
        this.currentStroke.updateMesh();

        // Update paint texture
        this.updatePaintTexture();
    }

    /**
     * Update paint texture on canvas
     */
    updatePaintTexture() {
        // This would integrate with the 3D canvas to update the paint texture
        if (window.Canvas3D && window.Canvas3D.paintRenderTarget) {
            const renderer = window.Canvas3D.renderer;
            const scene = new THREE.Scene();
            const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

            // Render stroke to texture
            renderer.setRenderTarget(window.Canvas3D.paintRenderTarget);
            renderer.render(scene, camera);
            renderer.setRenderTarget(null);
        }
    }

    /**
     * Generate particle effects
     * @param {Object} point - Current point data
     */
    generateParticles(point) {
        if (this.particles.length >= this.maxParticles) {
            // Remove oldest particles
            this.particles.splice(0, this.particles.length - this.maxParticles + 10);
        }

        // Create new particles based on brush movement
        const velocity = this.calculateVelocity(point);
        const particleCount = Math.floor(velocity * this.brushSettings.size * 0.1);

        for (let i = 0; i < particleCount; i++) {
            const particle = new PaintParticle({
                position: { ...point.position },
                velocity: {
                    x: (Math.random() - 0.5) * velocity,
                    y: (Math.random() - 0.5) * velocity,
                    z: (Math.random() - 0.5) * velocity * 0.5
                },
                color: { ...this.brushSettings.color },
                size: Math.random() * this.brushSettings.size * 0.2,
                life: 1.0,
                decay: 0.02
            });

            this.particles.push(particle);
        }
    }

    /**
     * Generate particles at stroke end
     * @param {BrushStroke} stroke - The completed stroke
     */
    generateStrokeEndParticles(stroke) {
        const lastPoint = stroke.points[stroke.points.length - 1];
        const burstCount = Math.floor(this.brushSettings.size * 0.5);

        for (let i = 0; i < burstCount; i++) {
            const angle = (i / burstCount) * Math.PI * 2;
            const speed = Math.random() * 2 + 1;

            const particle = new PaintParticle({
                position: { ...lastPoint.position },
                velocity: {
                    x: Math.cos(angle) * speed,
                    y: Math.sin(angle) * speed,
                    z: (Math.random() - 0.5) * speed * 0.5
                },
                color: { ...this.brushSettings.color },
                size: Math.random() * this.brushSettings.size * 0.3,
                life: 1.0,
                decay: 0.01
            });

            this.particles.push(particle);
        }
    }

    /**
     * Update physics simulation
     * @param {Object} point - Current point data
     */
    updatePhysics(point) {
        // Apply gravity to paint particles
        this.particles.forEach(particle => {
            if (particle.hasPhysics) {
                particle.velocity.y += this.gravity * 0.016; // Assuming 60fps
                
                // Apply viscosity
                particle.velocity.x *= (1 - this.viscosity * 0.016);
                particle.velocity.y *= (1 - this.viscosity * 0.016);
                particle.velocity.z *= (1 - this.viscosity * 0.016);
                
                // Update position
                particle.position.x += particle.velocity.x * 0.016;
                particle.position.y += particle.velocity.y * 0.016;
                particle.position.z += particle.velocity.z * 0.016;
            }
        });

        // Handle paint dripping
        if (this.currentBrush.supportsDripping && this.currentBrush.supportsDripping()) {
            this.simulatePaintDripping(point);
        }
    }

    /**
     * Simulate paint dripping effects
     * @param {Object} point - Current point data
     */
    simulatePaintDripping(point) {
        // Create drip if paint accumulation is high enough
        if (Math.random() < this.calculateDripProbability(point)) {
            const drip = new PaintDrip({
                startPosition: { ...point.position },
                color: { ...this.brushSettings.color },
                viscosity: this.viscosity,
                size: this.brushSettings.size * 0.1
            });

            this.particles.push(drip);
        }
    }

    /**
     * Calculate drip probability based on paint accumulation
     * @param {Object} point - Point data
     */
    calculateDripProbability(point) {
        const accumulation = this.currentStroke.getAccumulationAt(point.position);
        const angle = this.calculateSurfaceAngle(point.position);
        
        // Higher probability on steep angles and high accumulation
        return Math.min(0.1, accumulation * 0.01 + Math.abs(Math.sin(angle)) * 0.05);
    }

    /**
     * Calculate surface angle at position
     * @param {Object} position - Position to check
     */
    calculateSurfaceAngle(position) {
        // This would use the 3D surface normal to calculate angle
        // For now, return a simple approximation
        return 0;
    }

    /**
     * Calculate velocity from point data
     * @param {Object} point - Point data
     */
    calculateVelocity(point) {
        if (!this.currentStroke || this.currentStroke.points.length < 2) {
            return 0;
        }

        const lastPoint = this.currentStroke.points[this.currentStroke.points.length - 2];
        const dx = point.position.x - lastPoint.position.x;
        const dy = point.position.y - lastPoint.position.y;
        const dt = (point.timestamp - lastPoint.timestamp) || 16; // Default to 16ms

        return Math.sqrt(dx * dx + dy * dy) / (dt * 0.001); // Convert to units per second
    }

    /**
     * Update particles each frame
     */
    updateParticles() {
        this.particles = this.particles.filter(particle => {
            particle.update();
            return !particle.isDead();
        });
    }

    /**
     * Cache stroke for performance optimization
     * @param {BrushStroke} stroke - Stroke to cache
     */
    cacheStroke(stroke) {
        if (this.strokeCache.size >= this.maxCacheSize) {
            // Remove oldest cached stroke
            const firstKey = this.strokeCache.keys().next().value;
            this.strokeCache.delete(firstKey);
        }

        const cacheKey = `stroke_${stroke.id}`;
        this.strokeCache.set(cacheKey, stroke.serialize());
    }

    /**
     * Get cached stroke
     * @param {string} strokeId - Stroke ID
     */
    getCachedStroke(strokeId) {
        const cacheKey = `stroke_${strokeId}`;
        return this.strokeCache.get(cacheKey);
    }

    /**
     * Add stroke to history
     * @param {BrushStroke} stroke - Stroke to add
     */
    addToHistory(stroke) {
        this.strokeHistory.push(stroke);

        if (this.strokeHistory.length > this.maxHistorySize) {
            this.strokeHistory.shift();
        }
    }

    /**
     * Undo last stroke
     */
    undo() {
        if (this.strokeHistory.length > 0) {
            const lastStroke = this.strokeHistory.pop();
            lastStroke.remove();
            console.log('Undid last stroke');
            return true;
        }
        return false;
    }

    /**
     * Clear all strokes
     */
    clearAll() {
        this.strokeHistory.forEach(stroke => stroke.remove());
        this.strokeHistory = [];
        this.particles = [];
        this.strokeCache.clear();
        
        // Clear canvas
        if (window.Canvas3D && window.Canvas3D.paintRenderTarget) {
            const renderer = window.Canvas3D.renderer;
            renderer.setRenderTarget(window.Canvas3D.paintRenderTarget);
            renderer.clear();
            renderer.setRenderTarget(null);
        }
        
        console.log('Cleared all strokes');
    }

    /**
     * Update cursor based on current brush
     * @param {string} brushName - Name of the current brush
     */
    updateCursor(brushName) {
        const container = document.querySelector('.canvas-container');
        if (container) {
            // Remove existing brush classes
            container.classList.remove('brush-standard', 'brush-texture', 'brush-particle', 'brush-volumetric');
            
            // Add current brush class
            container.classList.add(`brush-${brushName}`);
        }
    }

    /**
     * Update settings UI
     */
    updateSettingsUI() {
        // Update size slider
        const sizeSlider = document.getElementById('brush-size');
        const sizeValue = document.getElementById('brush-size-value');
        if (sizeSlider && sizeValue) {
            sizeSlider.value = this.brushSettings.size;
            sizeValue.textContent = `${this.brushSettings.size}px`;
        }

        // Update opacity slider
        const opacitySlider = document.getElementById('brush-opacity');
        const opacityValue = document.getElementById('brush-opacity-value');
        if (opacitySlider && opacityValue) {
            opacitySlider.value = this.brushSettings.opacity * 100;
            opacityValue.textContent = `${Math.round(this.brushSettings.opacity * 100)}%`;
        }

        // Update color picker
        const colorPicker = document.getElementById('color-picker');
        if (colorPicker) {
            const r = Math.round(this.brushSettings.color.r * 255);
            const g = Math.round(this.brushSettings.color.g * 255);
            const b = Math.round(this.brushSettings.color.b * 255);
            colorPicker.value = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
        }
    }

    /**
     * Get brush performance statistics
     */
    getPerformanceStats() {
        return {
            activeParticles: this.particles.length,
            cachedStrokes: this.strokeCache.size,
            strokeHistory: this.strokeHistory.length,
            currentBrush: this.currentBrush ? this.currentBrush.constructor.name : 'None',
            physicsEnabled: this.physicsEnabled
        };
    }

    /**
     * Optimize performance
     */
    optimizePerformance() {
        // Reduce particle count
        if (this.particles.length > this.maxParticles * 0.5) {
            this.particles.splice(0, Math.floor(this.particles.length * 0.3));
        }

        // Clear old cache entries
        if (this.strokeCache.size > this.maxCacheSize * 0.8) {
            const keysToDelete = Array.from(this.strokeCache.keys()).slice(0, Math.floor(this.strokeCache.size * 0.3));
            keysToDelete.forEach(key => this.strokeCache.delete(key));
        }

        console.log('Brush engine performance optimized');
    }

    /**
     * Dispose of resources
     */
    dispose() {
        this.clearAll();
        this.brushes.clear();
        this.currentBrush = null;
        this.particles = [];
        this.strokeCache.clear();
        this.strokeHistory = [];
    }
}

/**
 * Base brush class
 */
class BaseBrush {
    constructor() {
        this.settings = {};
        this.name = 'base';
    }

    setSettings(settings) {
        this.settings = { ...this.settings, ...settings };
    }

    paint(point, stroke) {
        // Override in subclasses
    }

    supportsDripping() {
        return false;
    }
}

/**
 * Standard brush implementation
 */
class StandardBrush extends BaseBrush {
    constructor() {
        super();
        this.name = 'standard';
    }

    paint(point, stroke) {
        // Standard circular brush implementation
        return {
            shape: 'circle',
            size: this.settings.size * (point.pressure || 1.0),
            opacity: this.settings.opacity,
            color: this.settings.color
        };
    }
}

/**
 * Texture brush implementation
 */
class TextureBrush extends BaseBrush {
    constructor() {
        super();
        this.name = 'texture';
        this.texture = null;
    }

    paint(point, stroke) {
        return {
            shape: 'texture',
            size: this.settings.size * (point.pressure || 1.0),
            opacity: this.settings.opacity,
            color: this.settings.color,
            texture: this.texture
        };
    }
}

/**
 * Particle brush implementation
 */
class ParticleBrush extends BaseBrush {
    constructor() {
        super();
        this.name = 'particle';
    }

    paint(point, stroke) {
        return {
            shape: 'particles',
            size: this.settings.size,
            opacity: this.settings.opacity,
            color: this.settings.color,
            particleCount: Math.floor(this.settings.size * 0.5)
        };
    }
}

/**
 * Volumetric brush implementation
 */
class VolumetricBrush extends BaseBrush {
    constructor() {
        super();
        this.name = 'volumetric';
    }

    paint(point, stroke) {
        return {
            shape: 'volumetric',
            size: this.settings.size,
            opacity: this.settings.opacity,
            color: this.settings.color,
            depth: this.settings.size * 0.3
        };
    }
}

/**
 * Physics brush implementation
 */
class PhysicsBrush extends BaseBrush {
    constructor() {
        super();
        this.name = 'physics';
    }

    paint(point, stroke) {
        return {
            shape: 'physics',
            size: this.settings.size,
            opacity: this.settings.opacity,
            color: this.settings.color,
            viscosity: 0.1,
            hasPhysics: true
        };
    }

    supportsDripping() {
        return true;
    }
}

/**
 * Brush stroke class
 */
class BrushStroke {
    constructor(options) {
        this.id = this.generateId();
        this.brush = options.brush;
        this.settings = options.settings;
        this.points = [options.startPoint];
        this.timestamp = options.timestamp;
        this.mesh = null;
        this.isFinalized = false;
    }

    initialize() {
        // Create Three.js mesh for the stroke
        this.createMesh();
    }

    addPoint(point) {
        this.points.push(point);
        this.updateMesh();
    }

    finalize() {
        this.isFinalized = true;
        this.optimizeMesh();
    }

    createMesh() {
        // Create initial mesh
        const geometry = new THREE.BufferGeometry();
        const material = new THREE.MeshBasicMaterial({
            color: new THREE.Color(this.settings.color.r, this.settings.color.g, this.settings.color.b),
            transparent: true,
            opacity: this.settings.opacity
        });

        this.mesh = new THREE.Mesh(geometry, material);
        
        if (window.Canvas3D && window.Canvas3D.scene) {
            window.Canvas3D.scene.add(this.mesh);
        }
    }

    updateMesh() {
        if (!this.mesh || this.points.length < 2) return;

        // Update geometry based on points
        const positions = [];
        const colors = [];

        this.points.forEach(point => {
            positions.push(point.position.x, point.position.y, point.position.z || 0);
            colors.push(this.settings.color.r, this.settings.color.g, this.settings.color.b);
        });

        this.mesh.geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        this.mesh.geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
        this.mesh.geometry.attributes.position.needsUpdate = true;
        this.mesh.geometry.attributes.color.needsUpdate = true;
    }

    optimizeMesh() {
        // Optimize geometry after stroke is complete
        if (this.mesh && this.mesh.geometry) {
            this.mesh.geometry.computeBoundingSphere();
        }
    }

    getAccumulationAt(position) {
        // Calculate paint accumulation at a given position
        let accumulation = 0;
        const threshold = this.settings.size;

        this.points.forEach(point => {
            const distance = this.distanceTo(point.position, position);
            if (distance < threshold) {
                accumulation += 1 - (distance / threshold);
            }
        });

        return accumulation;
    }

    distanceTo(pos1, pos2) {
        const dx = pos1.x - pos2.x;
        const dy = pos1.y - pos2.y;
        const dz = (pos1.z || 0) - (pos2.z || 0);
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    }

    hasPhysics() {
        return this.brush.supportsDripping && this.brush.supportsDripping();
    }

    remove() {
        if (this.mesh && window.Canvas3D && window.Canvas3D.scene) {
            window.Canvas3D.scene.remove(this.mesh);
            this.mesh.geometry.dispose();
            this.mesh.material.dispose();
        }
    }

    serialize() {
        return {
            id: this.id,
            points: this.points,
            settings: this.settings,
            timestamp: this.timestamp
        };
    }

    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

/**
 * Paint particle class
 */
class PaintParticle {
    constructor(options) {
        this.position = options.position;
        this.velocity = options.velocity;
        this.color = options.color;
        this.size = options.size;
        this.life = options.life;
        this.decay = options.decay;
        this.hasPhysics = options.hasPhysics || false;
    }

    update() {
        // Update life
        this.life -= this.decay;

        // Update position based on velocity
        this.position.x += this.velocity.x * 0.016;
        this.position.y += this.velocity.y * 0.016;
        this.position.z += this.velocity.z * 0.016;

        // Update size based on life
        this.size *= 0.99;
    }

    isDead() {
        return this.life <= 0 || this.size <= 0.1;
    }
}

/**
 * Paint drip class
 */
class PaintDrip extends PaintParticle {
    constructor(options) {
        super(options);
        this.viscosity = options.viscosity;
        this.hasPhysics = true;
        this.velocity = { x: 0, y: -1, z: 0 }; // Start dripping downward
    }

    update() {
        super.update();

        // Apply gravity and viscosity
        this.velocity.y += -9.81 * 0.016;
        this.velocity.x *= (1 - this.viscosity);
        this.velocity.y *= (1 - this.viscosity * 0.5); // Less drag on vertical movement
        this.velocity.z *= (1 - this.viscosity);
    }
}

// Create global brush engine instance
window.BrushEngine = new BrushEngine();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrushEngine;
}