/**
 * 🎮 LivePrecisionCalculator - 3D Visualization Engine
 * ==================================================
 * 
 * Creates stunning 3D visualizations for calculation streams using Three.js
 * with audio-reactive elements and particle systems for error healing.
 */

class ThreeVisualization {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.container = null;
        
        // 3D Objects
        this.calculationSphere = null;
        this.particleSystem = null;
        this.currencyNodes = [];
        this.healingParticles = [];
        
        // Animation
        this.animationRunning = true;
        this.animationFrame = null;
        this.time = 0;
        
        // Audio reactive
        this.audioAnalyser = null;
        this.audioData = null;
        
        // Controls
        this.controls = null;
        
        // Calculation visualization
        this.calculationHistory = [];
        this.maxCalculationHistory = 100;
        
        this.init();
    }
    
    init() {
        console.log('🎮 Initializing 3D Visualization...');
        
        this.container = document.getElementById('threejs-container');
        if (!this.container) {
            console.error('3D container not found!');
            return;
        }
        
        this.initScene();
        this.initCamera();
        this.initRenderer();
        this.initLights();
        this.initObjects();
        this.initControls();
        this.initAudioAnalyser();
        
        this.handleResize();
        window.addEventListener('resize', () => this.handleResize());
        
        this.startAnimation();
        
        console.log('✅ 3D Visualization initialized');
    }
    
    initScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000510);
        
        // Add fog for depth
        this.scene.fog = new THREE.Fog(0x000510, 50, 200);
    }
    
    initCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(0, 10, 30);
        this.camera.lookAt(0, 0, 0);
    }
    
    initRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        
        this.container.appendChild(this.renderer.domElement);
    }
    
    initLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x4dd0e1, 0.3);
        this.scene.add(ambientLight);
        
        // Main directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(20, 20, 20);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 100;
        this.scene.add(directionalLight);
        
        // Point lights for quantum effect
        const pointLight1 = new THREE.PointLight(0x4dd0e1, 1, 50);
        pointLight1.position.set(-15, 10, 15);
        this.scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xff6b6b, 0.8, 50);
        pointLight2.position.set(15, -10, -15);
        this.scene.add(pointLight2);
        
        // Hemisphere light for realistic lighting
        const hemisphereLight = new THREE.HemisphereLight(0x4dd0e1, 0x000510, 0.4);
        this.scene.add(hemisphereLight);
    }
    
    initObjects() {
        this.createCalculationSphere();
        this.createParticleSystem();
        this.createCurrencyNodes();
        this.createQuantumGrid();
    }
    
    createCalculationSphere() {
        // Central calculation visualization sphere
        const geometry = new THREE.IcosahedronGeometry(3, 2);
        
        // Custom shader material for quantum effect
        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                resolution: { value: new THREE.Vector2(800, 600) },
                calculationIntensity: { value: 0.0 },
                errorIntensity: { value: 0.0 }
            },
            vertexShader: `
                uniform float time;
                uniform float calculationIntensity;
                varying vec3 vPosition;
                varying vec3 vNormal;
                varying vec2 vUv;
                
                void main() {
                    vPosition = position;
                    vNormal = normal;
                    vUv = uv;
                    
                    vec3 pos = position;
                    
                    // Add calculation-based displacement
                    float displacement = sin(pos.x * 0.5 + time) * 
                                       cos(pos.y * 0.5 + time) * 
                                       calculationIntensity * 0.3;
                    
                    pos += normal * displacement;
                    
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
                }
            `,
            fragmentShader: `
                uniform float time;
                uniform float calculationIntensity;
                uniform float errorIntensity;
                varying vec3 vPosition;
                varying vec3 vNormal;
                
                void main() {
                    vec3 quantumColor = vec3(0.3, 0.82, 0.88); // Quantum blue
                    vec3 errorColor = vec3(1.0, 0.42, 0.42);   // Error red
                    vec3 successColor = vec3(0.15, 0.82, 0.81); // Success cyan
                    
                    // Calculate fresnel effect
                    float fresnel = pow(1.0 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
                    
                    // Quantum energy effect
                    float energy = sin(time * 2.0 + vPosition.x * 0.1) * 
                                  cos(time * 1.5 + vPosition.y * 0.1) * 0.5 + 0.5;
                    
                    // Mix colors based on calculation state
                    vec3 finalColor = mix(quantumColor, successColor, calculationIntensity);
                    finalColor = mix(finalColor, errorColor, errorIntensity);
                    
                    // Add energy and fresnel
                    finalColor *= (0.7 + energy * 0.3);
                    finalColor += vec3(fresnel * 0.3);
                    
                    gl_FragColor = vec4(finalColor, 0.8 + fresnel * 0.2);
                }
            `,
            transparent: true,
            side: THREE.DoubleSide
        });
        
        this.calculationSphere = new THREE.Mesh(geometry, material);
        this.calculationSphere.position.set(0, 0, 0);
        this.calculationSphere.castShadow = true;
        this.calculationSphere.receiveShadow = true;
        this.scene.add(this.calculationSphere);
    }
    
    createParticleSystem() {
        const particleCount = 1000;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);
        const velocities = new Float32Array(particleCount * 3);
        
        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;
            
            // Random positions in sphere
            const radius = 20 + Math.random() * 30;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            
            positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i3 + 2] = radius * Math.cos(phi);
            
            // Quantum colors
            colors[i3] = 0.3 + Math.random() * 0.4;     // R
            colors[i3 + 1] = 0.8 + Math.random() * 0.2; // G
            colors[i3 + 2] = 0.8 + Math.random() * 0.2; // B
            
            sizes[i] = Math.random() * 2 + 0.5;
            
            // Random velocities
            velocities[i3] = (Math.random() - 0.5) * 0.02;
            velocities[i3 + 1] = (Math.random() - 0.5) * 0.02;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.02;
        }
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        
        // Store velocities for animation
        geometry.userData.velocities = velocities;
        
        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                audioIntensity: { value: 0 }
            },
            vertexShader: `
                attribute float size;
                attribute vec3 color;
                uniform float time;
                uniform float audioIntensity;
                varying vec3 vColor;
                varying float vAlpha;
                
                void main() {
                    vColor = color;
                    
                    vec3 pos = position;
                    
                    // Audio-reactive movement
                    pos += sin(time + position.x * 0.01) * audioIntensity * 2.0 * vec3(1.0, 0.5, 1.0);
                    
                    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                    
                    gl_PointSize = size * (300.0 / -mvPosition.z) * (1.0 + audioIntensity);
                    gl_Position = projectionMatrix * mvPosition;
                    
                    vAlpha = 0.6 + audioIntensity * 0.4;
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                varying float vAlpha;
                
                void main() {
                    vec2 center = gl_PointCoord - 0.5;
                    float dist = length(center);
                    
                    if (dist > 0.5) discard;
                    
                    float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
                    
                    gl_FragColor = vec4(vColor, alpha * vAlpha);
                }
            `,
            transparent: true,
            vertexColors: true,
            blending: THREE.AdditiveBlending
        });
        
        this.particleSystem = new THREE.Points(geometry, material);
        this.scene.add(this.particleSystem);
    }
    
    createCurrencyNodes() {
        const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY'];
        const radius = 15;
        
        currencies.forEach((currency, index) => {
            const angle = (index / currencies.length) * Math.PI * 2;
            const x = Math.cos(angle) * radius;
            const z = Math.sin(angle) * radius;
            
            // Node geometry
            const geometry = new THREE.OctahedronGeometry(0.5, 1);
            const material = new THREE.MeshPhongMaterial({
                color: 0x4dd0e1,
                emissive: 0x002244,
                transparent: true,
                opacity: 0.8
            });
            
            const node = new THREE.Mesh(geometry, material);
            node.position.set(x, Math.sin(index) * 2, z);
            node.userData.currency = currency;
            node.userData.baseY = node.position.y;
            
            this.scene.add(node);
            this.currencyNodes.push(node);
            
            // Add currency label
            this.createCurrencyLabel(currency, x, node.position.y + 1, z);
        });
    }
    
    createCurrencyLabel(text, x, y, z) {
        // Create text sprite for currency label
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 128;
        canvas.height = 64;
        
        context.fillStyle = 'rgba(77, 208, 225, 0.8)';
        context.fillRect(0, 0, canvas.width, canvas.height);
        
        context.font = 'Bold 20px Arial';
        context.fillStyle = '#ffffff';
        context.textAlign = 'center';
        context.fillText(text, canvas.width / 2, canvas.height / 2 + 7);
        
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
        const sprite = new THREE.Sprite(material);
        
        sprite.position.set(x, y, z);
        sprite.scale.set(2, 1, 1);
        
        this.scene.add(sprite);
    }
    
    createQuantumGrid() {
        // Create a quantum energy grid floor
        const gridSize = 50;
        const divisions = 20;
        
        const gridHelper = new THREE.GridHelper(gridSize, divisions, 0x4dd0e1, 0x002244);
        gridHelper.position.y = -10;
        gridHelper.material.opacity = 0.3;
        gridHelper.material.transparent = true;
        this.scene.add(gridHelper);
    }
    
    initControls() {
        // Mouse controls for camera (optional - can be disabled for auto-rotation)
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.enableZoom = true;
            this.controls.enablePan = false;
            this.controls.maxDistance = 100;
            this.controls.minDistance = 10;
        }
    }
    
    initAudioAnalyser() {
        if (window.quantumDashboard && window.quantumDashboard.audioContext) {
            try {
                this.audioAnalyser = window.quantumDashboard.audioContext.createAnalyser();
                this.audioAnalyser.fftSize = 256;
                this.audioData = new Uint8Array(this.audioAnalyser.frequencyBinCount);
            } catch (error) {
                console.warn('Audio analyser initialization failed:', error);
            }
        }
    }
    
    startAnimation() {
        if (this.animationRunning) {
            this.animate();
        }
    }
    
    stopAnimation() {
        this.animationRunning = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
    
    animate() {
        if (!this.animationRunning) return;
        
        this.animationFrame = requestAnimationFrame(() => this.animate());
        
        this.time += 0.01;
        
        // Update calculation sphere
        if (this.calculationSphere) {
            this.calculationSphere.rotation.x += 0.005;
            this.calculationSphere.rotation.y += 0.01;
            
            // Update shader uniforms
            if (this.calculationSphere.material.uniforms) {
                this.calculationSphere.material.uniforms.time.value = this.time;
                
                // Pulse effect during calculations
                const intensity = Math.sin(this.time * 3) * 0.5 + 0.5;
                this.calculationSphere.material.uniforms.calculationIntensity.value = intensity * 0.3;
            }
        }
        
        // Update particle system
        if (this.particleSystem) {
            this.particleSystem.rotation.y += 0.002;
            
            // Audio-reactive particles
            let audioIntensity = 0;
            if (this.audioAnalyser && this.audioData) {
                this.audioAnalyser.getByteFrequencyData(this.audioData);
                audioIntensity = Array.from(this.audioData).reduce((a, b) => a + b) / this.audioData.length / 255;
            }
            
            if (this.particleSystem.material.uniforms) {
                this.particleSystem.material.uniforms.time.value = this.time;
                this.particleSystem.material.uniforms.audioIntensity.value = audioIntensity;
            }
            
            // Animate particle positions
            const positions = this.particleSystem.geometry.attributes.position.array;
            const velocities = this.particleSystem.geometry.userData.velocities;
            
            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];
                
                // Boundary check - reset if too far
                const distance = Math.sqrt(positions[i]**2 + positions[i+1]**2 + positions[i+2]**2);
                if (distance > 60) {
                    const radius = 20;
                    const theta = Math.random() * Math.PI * 2;
                    const phi = Math.acos(2 * Math.random() - 1);
                    
                    positions[i] = radius * Math.sin(phi) * Math.cos(theta);
                    positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
                    positions[i + 2] = radius * Math.cos(phi);
                }
            }
            
            this.particleSystem.geometry.attributes.position.needsUpdate = true;
        }
        
        // Update currency nodes
        this.currencyNodes.forEach((node, index) => {
            node.rotation.x += 0.01;
            node.rotation.y += 0.02;
            
            // Floating motion
            node.position.y = node.userData.baseY + Math.sin(this.time + index) * 0.5;
            
            // Pulsing glow
            const glow = Math.sin(this.time * 2 + index) * 0.3 + 0.7;
            node.material.emissive.setRGB(0.0, 0.1 * glow, 0.2 * glow);
        });
        
        // Update camera auto-rotation
        if (!this.controls || !this.controls.enabled) {
            this.camera.position.x = Math.cos(this.time * 0.1) * 30;
            this.camera.position.z = Math.sin(this.time * 0.1) * 30;
            this.camera.lookAt(0, 0, 0);
        }
        
        if (this.controls) {
            this.controls.update();
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    handleResize() {
        if (!this.container || !this.camera || !this.renderer) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    // Public methods for dashboard integration
    triggerCalculationEffect(result) {
        if (!this.calculationSphere) return;
        
        // Pulse the calculation sphere
        const material = this.calculationSphere.material;
        if (material.uniforms) {
            material.uniforms.calculationIntensity.value = 1.0;
            
            // Fade out over time
            const fadeOut = () => {
                if (material.uniforms.calculationIntensity.value > 0) {
                    material.uniforms.calculationIntensity.value *= 0.95;
                    setTimeout(fadeOut, 50);
                }
            };
            fadeOut();
        }
        
        // Add calculation visualization trail
        this.addCalculationTrail(result);
    }
    
    addCalculationTrail(result) {
        // Create a visual trail for the calculation
        const geometry = new THREE.SphereGeometry(0.2, 8, 6);
        const material = new THREE.MeshBasicMaterial({
            color: 0x26d0ce,
            transparent: true,
            opacity: 1.0
        });
        
        const trail = new THREE.Mesh(geometry, material);
        trail.position.set(
            (Math.random() - 0.5) * 10,
            (Math.random() - 0.5) * 10,
            (Math.random() - 0.5) * 10
        );
        
        this.scene.add(trail);
        
        // Animate trail towards center
        const animate = () => {
            trail.position.lerp(new THREE.Vector3(0, 0, 0), 0.02);
            trail.material.opacity *= 0.98;
            trail.scale.multiplyScalar(1.01);
            
            if (trail.material.opacity > 0.01) {
                requestAnimationFrame(animate);
            } else {
                this.scene.remove(trail);
            }
        };
        animate();
    }
    
    triggerHealingEffect() {
        // Create healing particle burst
        const particleCount = 50;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const velocities = [];
        
        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;
            positions[i3] = 0;
            positions[i3 + 1] = 0;
            positions[i3 + 2] = 0;
            
            velocities.push(
                (Math.random() - 0.5) * 0.5,
                Math.random() * 0.3,
                (Math.random() - 0.5) * 0.5
            );
        }
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const material = new THREE.PointsMaterial({
            color: 0x26d0ce,
            size: 0.5,
            transparent: true,
            opacity: 1.0,
            blending: THREE.AdditiveBlending
        });
        
        const healingBurst = new THREE.Points(geometry, material);
        this.scene.add(healingBurst);
        
        // Animate healing burst
        let life = 1.0;
        const animateHealing = () => {
            const positions = healingBurst.geometry.attributes.position.array;
            
            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += velocities[i];
                positions[i + 1] += velocities[i + 1];
                positions[i + 2] += velocities[i + 2];
                
                velocities[i + 1] -= 0.01; // Gravity
            }
            
            healingBurst.geometry.attributes.position.needsUpdate = true;
            
            life *= 0.98;
            healingBurst.material.opacity = life;
            
            if (life > 0.01) {
                requestAnimationFrame(animateHealing);
            } else {
                this.scene.remove(healingBurst);
            }
        };
        animateHealing();
    }
    
    updateCurrencyRates(rates) {
        // Animate currency nodes based on exchange rates
        this.currencyNodes.forEach(node => {
            const currency = node.userData.currency;
            if (rates[currency]) {
                const rate = parseFloat(rates[currency]);
                const scale = 0.5 + rate * 0.5; // Scale based on rate
                node.scale.setScalar(Math.min(scale, 2.0));
                
                // Color intensity based on rate
                const intensity = Math.min(rate, 2.0) / 2.0;
                node.material.color.setRGB(0.3 + intensity * 0.4, 0.8, 0.8 + intensity * 0.2);
            }
        });
    }
}

// Initialize 3D visualization when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure container is ready
    setTimeout(() => {
        window.threeVisualization = new ThreeVisualization();
    }, 100);
});