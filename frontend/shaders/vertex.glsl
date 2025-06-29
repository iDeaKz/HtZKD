/**
 * Advanced Vertex Shader for 3D Paint Application
 * Supports multiple brush types, lighting, and effects
 */

#version 300 es

// Precision qualifiers
precision highp float;
precision highp int;

// Vertex attributes
in vec3 position;
in vec3 normal;
in vec2 uv;
in vec3 color;
in float opacity;

// Instance attributes (for particle systems)
in vec3 instancePosition;
in vec3 instanceScale;
in vec4 instanceRotation;
in vec4 instanceColor;

// Uniforms - Matrices
uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
uniform mat4 modelViewMatrix;
uniform mat3 normalMatrix;

// Uniforms - Camera
uniform vec3 cameraPosition;

// Uniforms - Time and animation
uniform float time;
uniform float deltaTime;

// Uniforms - Brush settings
uniform int brushType; // 0=standard, 1=texture, 2=particle, 3=volumetric
uniform float brushSize;
uniform float brushOpacity;
uniform float brushHardness;
uniform vec3 brushPosition;
uniform vec3 brushVelocity;

// Uniforms - Lighting
uniform vec3 ambientLightColor;
uniform float ambientLightIntensity;
uniform vec3 directionalLightColor;
uniform vec3 directionalLightDirection;
uniform float directionalLightIntensity;

// Uniforms - Effects
uniform bool enableShadows;
uniform bool enableParticles;
uniform bool enablePhysics;
uniform float gravity;
uniform float windStrength;
uniform vec3 windDirection;

// Uniforms - Material properties
uniform float metalness;
uniform float roughness;
uniform float emissive;
uniform float transparency;

// Varying outputs to fragment shader
out vec3 vPosition;
out vec3 vWorldPosition;
out vec3 vNormal;
out vec3 vViewNormal;
out vec2 vUv;
out vec3 vColor;
out float vOpacity;
out vec3 vViewPosition;
out vec4 vShadowCoord;

// Varying for lighting calculations
out vec3 vLightDirection;
out float vLightIntensity;

// Varying for effects
out float vDistance;
out float vBrushInfluence;
out vec3 vVelocity;

// Varying for particles
out float vParticleLife;
out float vParticleSize;

// Shadow mapping
uniform mat4 shadowMatrix;
uniform bool receiveShadows;

// Utility functions
vec3 transformDirection(vec3 dir, mat4 matrix) {
    return normalize((matrix * vec4(dir, 0.0)).xyz);
}

vec4 quaternionToMatrix(vec4 q) {
    float x = q.x, y = q.y, z = q.z, w = q.w;
    float x2 = x + x, y2 = y + y, z2 = z + z;
    float xx = x * x2, xy = x * y2, xz = x * z2;
    float yy = y * y2, yz = y * z2, zz = z * z2;
    float wx = w * x2, wy = w * y2, wz = w * z2;
    
    return mat4(
        1.0 - (yy + zz), xy - wz, xz + wy, 0.0,
        xy + wz, 1.0 - (xx + zz), yz - wx, 0.0,
        xz - wy, yz + wx, 1.0 - (xx + yy), 0.0,
        0.0, 0.0, 0.0, 1.0
    );
}

float calculateBrushInfluence(vec3 worldPos, vec3 brushPos, float size) {
    float distance = length(worldPos - brushPos);
    float influence = 1.0 - smoothstep(0.0, size, distance);
    return pow(influence, brushHardness);
}

vec3 applyPhysics(vec3 pos, vec3 velocity, float deltaTime) {
    vec3 newPos = pos;
    
    if (enablePhysics) {
        // Apply gravity
        velocity.y += gravity * deltaTime;
        
        // Apply wind
        velocity += windDirection * windStrength * deltaTime;
        
        // Update position
        newPos += velocity * deltaTime;
    }
    
    return newPos;
}

void main() {
    // Initialize varying variables
    vUv = uv;
    vColor = color;
    vOpacity = opacity;
    
    // Calculate transformed position
    vec3 transformedPosition = position;
    vec3 transformedNormal = normal;
    
    // Handle different brush types
    if (brushType == 2) { // Particle brush
        // Apply instanced transformations for particles
        mat4 instanceMatrix = quaternionToMatrix(instanceRotation);
        instanceMatrix[3] = vec4(instancePosition, 1.0);
        
        transformedPosition = (instanceMatrix * vec4(position * instanceScale, 1.0)).xyz;
        transformedNormal = mat3(instanceMatrix) * normal;
        
        vColor = instanceColor.rgb;
        vOpacity = instanceColor.a;
        
        // Calculate particle properties
        vParticleLife = instanceColor.a; // Using alpha as life indicator
        vParticleSize = length(instanceScale);
    }
    else if (brushType == 3) { // Volumetric brush
        // Apply volumetric deformation
        float volumeInfluence = calculateBrushInfluence(position, brushPosition, brushSize);
        transformedPosition += normal * volumeInfluence * brushSize * 0.1;
    }
    
    // Apply physics if enabled
    if (enablePhysics && brushType == 2) {
        transformedPosition = applyPhysics(transformedPosition, brushVelocity, deltaTime);
        vVelocity = brushVelocity;
    }
    
    // Calculate world position
    vWorldPosition = (modelMatrix * vec4(transformedPosition, 1.0)).xyz;
    vPosition = transformedPosition;
    
    // Calculate view position
    vec4 viewPosition = viewMatrix * vec4(vWorldPosition, 1.0);
    vViewPosition = viewPosition.xyz;
    
    // Transform normal to view space
    vNormal = transformedNormal;
    vViewNormal = normalMatrix * transformedNormal;
    
    // Calculate lighting
    vLightDirection = normalize(directionalLightDirection);
    vLightIntensity = max(dot(normalize(vViewNormal), vLightDirection), 0.0) * directionalLightIntensity + ambientLightIntensity;
    
    // Calculate distance from camera
    vDistance = length(vViewPosition);
    
    // Calculate brush influence
    vBrushInfluence = calculateBrushInfluence(vWorldPosition, brushPosition, brushSize);
    
    // Calculate shadow coordinates
    if (enableShadows && receiveShadows) {
        vShadowCoord = shadowMatrix * vec4(vWorldPosition, 1.0);
    }
    
    // Calculate final position
    gl_Position = projectionMatrix * viewPosition;
    
    // Handle point size for particle rendering
    if (brushType == 2) {
        gl_PointSize = vParticleSize * (100.0 / vDistance);
        gl_PointSize = clamp(gl_PointSize, 1.0, 64.0);
    }
}