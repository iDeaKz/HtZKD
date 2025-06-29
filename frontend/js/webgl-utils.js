/**
 * WebGL Utilities for 3D Paint Application
 * Provides comprehensive WebGL management and optimization
 */

class WebGLUtils {
    constructor() {
        this.gl = null;
        this.canvas = null;
        this.extensions = {};
        this.capabilities = {};
        this.programs = new Map();
        this.buffers = new Map();
        this.textures = new Map();
        this.framebuffers = new Map();
        this.vertexArrays = new Map();
        
        this.isInitialized = false;
        this.contextLost = false;
        
        // Performance tracking
        this.drawCalls = 0;
        this.triangles = 0;
        this.lastFrameTime = performance.now();
    }

    /**
     * Initialize WebGL context with comprehensive error handling
     * @param {HTMLCanvasElement} canvas - Canvas element
     * @param {Object} options - WebGL context options
     */
    initialize(canvas, options = {}) {
        this.canvas = canvas;
        
        // Default WebGL context options optimized for 3D painting
        const defaultOptions = {
            alpha: false,
            depth: true,
            stencil: true,
            antialias: true,
            premultipliedAlpha: false,
            preserveDrawingBuffer: false,
            powerPreference: 'high-performance',
            failIfMajorPerformanceeCaveat: false
        };

        const contextOptions = { ...defaultOptions, ...options };

        try {
            // Try WebGL2 first, fallback to WebGL1
            this.gl = canvas.getContext('webgl2', contextOptions) ||
                     canvas.getContext('webgl', contextOptions) ||
                     canvas.getContext('experimental-webgl', contextOptions);

            if (!this.gl) {
                throw new Error('WebGL not supported or context creation failed');
            }

            // Set up context lost/restored handlers
            this.setupContextHandlers();
            
            // Detect capabilities and extensions
            this.detectCapabilities();
            
            // Initialize state
            this.initializeState();
            
            this.isInitialized = true;
            console.log('WebGL initialized successfully');
            
            return true;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.WEBGL,
                level: window.ErrorHandler.errorLevels.CRITICAL,
                message: `WebGL initialization failed: ${error.message}`,
                error: error
            });
            return false;
        }
    }

    /**
     * Set up WebGL context lost/restored event handlers
     */
    setupContextHandlers() {
        this.canvas.addEventListener('webglcontextlost', (event) => {
            event.preventDefault();
            this.contextLost = true;
            console.warn('WebGL context lost');
            
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.WEBGL,
                level: window.ErrorHandler.errorLevels.WARNING,
                message: 'WebGL context lost',
                event: event
            });
        });

        this.canvas.addEventListener('webglcontextrestored', () => {
            this.contextLost = false;
            console.log('WebGL context restored');
            
            // Reinitialize resources
            this.reinitialize();
        });
    }

    /**
     * Detect WebGL capabilities and extensions
     */
    detectCapabilities() {
        const gl = this.gl;
        
        // Get WebGL version
        this.capabilities.version = gl.getParameter(gl.VERSION);
        this.capabilities.isWebGL2 = this.capabilities.version.includes('WebGL 2.0');
        
        // Get renderer info
        this.capabilities.vendor = gl.getParameter(gl.VENDOR);
        this.capabilities.renderer = gl.getParameter(gl.RENDERER);
        this.capabilities.shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
        
        // Get limits
        this.capabilities.maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
        this.capabilities.maxCubeMapTextureSize = gl.getParameter(gl.MAX_CUBE_MAP_TEXTURE_SIZE);
        this.capabilities.maxTextureImageUnits = gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS);
        this.capabilities.maxVertexTextureImageUnits = gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS);
        this.capabilities.maxCombinedTextureImageUnits = gl.getParameter(gl.MAX_COMBINED_TEXTURE_IMAGE_UNITS);
        this.capabilities.maxVertexAttribs = gl.getParameter(gl.MAX_VERTEX_ATTRIBS);
        this.capabilities.maxVertexUniformVectors = gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS);
        this.capabilities.maxFragmentUniformVectors = gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS);
        this.capabilities.maxVaryingVectors = gl.getParameter(gl.MAX_VARYING_VECTORS);
        this.capabilities.maxViewportDims = gl.getParameter(gl.MAX_VIEWPORT_DIMS);
        
        // Load extensions
        this.loadExtensions();
        
        console.log('WebGL Capabilities:', this.capabilities);
    }

    /**
     * Load important WebGL extensions
     */
    loadExtensions() {
        const gl = this.gl;
        
        const extensionList = [
            'OES_vertex_array_object',
            'OES_element_index_uint',
            'OES_texture_float',
            'OES_texture_half_float',
            'OES_texture_float_linear',
            'OES_texture_half_float_linear',
            'EXT_texture_filter_anisotropic',
            'WEBGL_lose_context',
            'WEBGL_compressed_texture_s3tc',
            'WEBGL_compressed_texture_pvrtc',
            'WEBGL_compressed_texture_etc1',
            'WEBGL_depth_texture',
            'OES_standard_derivatives',
            'EXT_shader_texture_lod',
            'EXT_frag_depth',
            'WEBGL_draw_buffers',
            'ANGLE_instanced_arrays'
        ];

        extensionList.forEach(extensionName => {
            const extension = gl.getExtension(extensionName);
            if (extension) {
                this.extensions[extensionName] = extension;
                console.log(`Extension loaded: ${extensionName}`);
            }
        });

        // Special handling for vertex array objects
        if (this.extensions['OES_vertex_array_object']) {
            this.capabilities.hasVertexArrayObjects = true;
        } else if (this.capabilities.isWebGL2) {
            this.capabilities.hasVertexArrayObjects = true;
        }
    }

    /**
     * Initialize WebGL state
     */
    initializeState() {
        const gl = this.gl;
        
        // Set clear color
        gl.clearColor(0.0, 0.0, 0.0, 0.0);
        
        // Enable depth testing
        gl.enable(gl.DEPTH_TEST);
        gl.depthFunc(gl.LEQUAL);
        
        // Enable blending for transparency
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        
        // Set viewport
        this.updateViewport();
        
        // Enable culling
        gl.enable(gl.CULL_FACE);
        gl.cullFace(gl.BACK);
        gl.frontFace(gl.CCW);
    }

    /**
     * Update viewport to match canvas size
     */
    updateViewport() {
        const gl = this.gl;
        const canvas = this.canvas;
        
        // Handle high DPI displays
        const pixelRatio = window.devicePixelRatio || 1;
        const displayWidth = Math.floor(canvas.clientWidth * pixelRatio);
        const displayHeight = Math.floor(canvas.clientHeight * pixelRatio);
        
        if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
            canvas.width = displayWidth;
            canvas.height = displayHeight;
        }
        
        gl.viewport(0, 0, canvas.width, canvas.height);
    }

    /**
     * Create and compile shader
     * @param {number} type - Shader type (gl.VERTEX_SHADER or gl.FRAGMENT_SHADER)
     * @param {string} source - Shader source code
     */
    createShader(type, source) {
        const gl = this.gl;
        
        try {
            const shader = gl.createShader(type);
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                const error = gl.getShaderInfoLog(shader);
                gl.deleteShader(shader);
                throw new Error(`Shader compilation failed: ${error}`);
            }
            
            return shader;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.SHADER,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Shader creation failed: ${error.message}`,
                error: error,
                shaderType: type === gl.VERTEX_SHADER ? 'vertex' : 'fragment',
                source: source
            });
            throw error;
        }
    }

    /**
     * Create shader program
     * @param {string} vertexSource - Vertex shader source
     * @param {string} fragmentSource - Fragment shader source
     */
    createProgram(vertexSource, fragmentSource) {
        const gl = this.gl;
        
        try {
            const vertexShader = this.createShader(gl.VERTEX_SHADER, vertexSource);
            const fragmentShader = this.createShader(gl.FRAGMENT_SHADER, fragmentSource);
            
            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);
            
            if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
                const error = gl.getProgramInfoLog(program);
                gl.deleteProgram(program);
                throw new Error(`Program linking failed: ${error}`);
            }
            
            // Clean up shaders
            gl.deleteShader(vertexShader);
            gl.deleteShader(fragmentShader);
            
            return program;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.SHADER,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Program creation failed: ${error.message}`,
                error: error
            });
            throw error;
        }
    }

    /**
     * Create buffer
     * @param {number} target - Buffer target (gl.ARRAY_BUFFER, gl.ELEMENT_ARRAY_BUFFER)
     * @param {ArrayBuffer|ArrayBufferView} data - Buffer data
     * @param {number} usage - Buffer usage (gl.STATIC_DRAW, gl.DYNAMIC_DRAW, gl.STREAM_DRAW)
     */
    createBuffer(target, data, usage = this.gl.STATIC_DRAW) {
        const gl = this.gl;
        
        try {
            const buffer = gl.createBuffer();
            gl.bindBuffer(target, buffer);
            gl.bufferData(target, data, usage);
            
            return buffer;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.GPU,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Buffer creation failed: ${error.message}`,
                error: error
            });
            throw error;
        }
    }

    /**
     * Create texture
     * @param {Object} options - Texture options
     */
    createTexture(options = {}) {
        const gl = this.gl;
        
        const defaults = {
            target: gl.TEXTURE_2D,
            width: 1,
            height: 1,
            internalFormat: gl.RGBA,
            format: gl.RGBA,
            type: gl.UNSIGNED_BYTE,
            data: null,
            wrapS: gl.CLAMP_TO_EDGE,
            wrapT: gl.CLAMP_TO_EDGE,
            minFilter: gl.LINEAR,
            magFilter: gl.LINEAR,
            generateMipmap: false
        };

        const config = { ...defaults, ...options };

        try {
            const texture = gl.createTexture();
            gl.bindTexture(config.target, texture);
            
            // Set texture data
            if (config.data) {
                if (config.data instanceof HTMLImageElement ||
                    config.data instanceof HTMLCanvasElement ||
                    config.data instanceof HTMLVideoElement) {
                    gl.texImage2D(config.target, 0, config.internalFormat,
                                config.format, config.type, config.data);
                } else {
                    gl.texImage2D(config.target, 0, config.internalFormat,
                                config.width, config.height, 0,
                                config.format, config.type, config.data);
                }
            } else {
                gl.texImage2D(config.target, 0, config.internalFormat,
                            config.width, config.height, 0,
                            config.format, config.type, null);
            }
            
            // Set texture parameters
            gl.texParameteri(config.target, gl.TEXTURE_WRAP_S, config.wrapS);
            gl.texParameteri(config.target, gl.TEXTURE_WRAP_T, config.wrapT);
            gl.texParameteri(config.target, gl.TEXTURE_MIN_FILTER, config.minFilter);
            gl.texParameteri(config.target, gl.TEXTURE_MAG_FILTER, config.magFilter);
            
            // Generate mipmap if requested
            if (config.generateMipmap) {
                gl.generateMipmap(config.target);
            }
            
            return texture;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.GPU,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Texture creation failed: ${error.message}`,
                error: error
            });
            throw error;
        }
    }

    /**
     * Create framebuffer
     * @param {Object} options - Framebuffer options
     */
    createFramebuffer(options = {}) {
        const gl = this.gl;
        
        try {
            const framebuffer = gl.createFramebuffer();
            gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
            
            // Create color texture if requested
            if (options.colorTexture !== false) {
                const colorTexture = this.createTexture({
                    width: options.width || this.canvas.width,
                    height: options.height || this.canvas.height,
                    internalFormat: options.colorFormat || gl.RGBA,
                    format: options.colorFormat || gl.RGBA,
                    type: options.colorType || gl.UNSIGNED_BYTE
                });
                
                gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0,
                                      gl.TEXTURE_2D, colorTexture, 0);
                
                framebuffer.colorTexture = colorTexture;
            }
            
            // Create depth buffer if requested
            if (options.depth !== false) {
                const depthBuffer = gl.createRenderbuffer();
                gl.bindRenderbuffer(gl.RENDERBUFFER, depthBuffer);
                gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT16,
                                     options.width || this.canvas.width,
                                     options.height || this.canvas.height);
                gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT,
                                         gl.RENDERBUFFER, depthBuffer);
                
                framebuffer.depthBuffer = depthBuffer;
            }
            
            // Check framebuffer completeness
            if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
                throw new Error('Framebuffer is not complete');
            }
            
            // Unbind
            gl.bindFramebuffer(gl.FRAMEBUFFER, null);
            
            return framebuffer;
        } catch (error) {
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.GPU,
                level: window.ErrorHandler.errorLevels.ERROR,
                message: `Framebuffer creation failed: ${error.message}`,
                error: error
            });
            throw error;
        }
    }

    /**
     * Check for WebGL errors
     */
    checkError(operation = 'Unknown operation') {
        const gl = this.gl;
        const error = gl.getError();
        
        if (error !== gl.NO_ERROR) {
            let errorString = 'Unknown error';
            
            switch (error) {
                case gl.INVALID_ENUM:
                    errorString = 'INVALID_ENUM';
                    break;
                case gl.INVALID_VALUE:
                    errorString = 'INVALID_VALUE';
                    break;
                case gl.INVALID_OPERATION:
                    errorString = 'INVALID_OPERATION';
                    break;
                case gl.INVALID_FRAMEBUFFER_OPERATION:
                    errorString = 'INVALID_FRAMEBUFFER_OPERATION';
                    break;
                case gl.OUT_OF_MEMORY:
                    errorString = 'OUT_OF_MEMORY';
                    break;
                case gl.CONTEXT_LOST_WEBGL:
                    errorString = 'CONTEXT_LOST_WEBGL';
                    break;
            }
            
            window.ErrorHandler.handleError({
                type: window.ErrorHandler.errorTypes.WEBGL,
                level: error === gl.OUT_OF_MEMORY ? 
                      window.ErrorHandler.errorLevels.CRITICAL : 
                      window.ErrorHandler.errorLevels.ERROR,
                message: `WebGL Error in ${operation}: ${errorString} (${error})`,
                errorCode: error,
                operation: operation
            });
            
            return error;
        }
        
        return gl.NO_ERROR;
    }

    /**
     * Get memory info (if available)
     */
    getMemoryInfo() {
        const gl = this.gl;
        const memoryInfo = {
            totalAvailable: 'Unknown',
            totalUsed: 'Unknown'
        };
        
        // Try to get memory info from WebGL debug extension
        if (this.extensions['WEBGL_debug_renderer_info']) {
            const debugInfo = this.extensions['WEBGL_debug_renderer_info'];
            memoryInfo.renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            memoryInfo.vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        }
        
        return memoryInfo;
    }

    /**
     * Reinitialize after context restoration
     */
    reinitialize() {
        this.isInitialized = false;
        this.programs.clear();
        this.buffers.clear();
        this.textures.clear();
        this.framebuffers.clear();
        this.vertexArrays.clear();
        
        this.initializeState();
        this.isInitialized = true;
        
        console.log('WebGL reinitialized after context restoration');
    }

    /**
     * Clean up resources
     */
    dispose() {
        const gl = this.gl;
        
        // Delete programs
        this.programs.forEach(program => gl.deleteProgram(program));
        this.programs.clear();
        
        // Delete buffers
        this.buffers.forEach(buffer => gl.deleteBuffer(buffer));
        this.buffers.clear();
        
        // Delete textures
        this.textures.forEach(texture => gl.deleteTexture(texture));
        this.textures.clear();
        
        // Delete framebuffers
        this.framebuffers.forEach(framebuffer => {
            if (framebuffer.colorTexture) gl.deleteTexture(framebuffer.colorTexture);
            if (framebuffer.depthBuffer) gl.deleteRenderbuffer(framebuffer.depthBuffer);
            gl.deleteFramebuffer(framebuffer);
        });
        this.framebuffers.clear();
        
        // Delete vertex arrays
        if (this.capabilities.hasVertexArrayObjects) {
            this.vertexArrays.forEach(vao => {
                if (this.capabilities.isWebGL2) {
                    gl.deleteVertexArray(vao);
                } else if (this.extensions['OES_vertex_array_object']) {
                    this.extensions['OES_vertex_array_object'].deleteVertexArrayOES(vao);
                }
            });
        }
        this.vertexArrays.clear();
        
        this.isInitialized = false;
    }
}

// Export for global use
window.WebGLUtils = WebGLUtils;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebGLUtils;
}