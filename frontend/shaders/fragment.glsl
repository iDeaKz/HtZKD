/**
 * Advanced Fragment Shader for 3D Paint Application
 * Supports multiple brush types, lighting, shadows, and effects
 */

#version 300 es

// Precision qualifiers
precision highp float;
precision highp int;

// Varying inputs from vertex shader
in vec3 vPosition;
in vec3 vWorldPosition;
in vec3 vNormal;
in vec3 vViewNormal;
in vec2 vUv;
in vec3 vColor;
in float vOpacity;
in vec3 vViewPosition;
in vec4 vShadowCoord;

// Lighting inputs
in vec3 vLightDirection;
in float vLightIntensity;

// Effects inputs
in float vDistance;
in float vBrushInfluence;
in vec3 vVelocity;

// Particle inputs
in float vParticleLife;
in float vParticleSize;

// Output color
out vec4 fragColor;

// Uniforms - Brush settings
uniform int brushType; // 0=standard, 1=texture, 2=particle, 3=volumetric
uniform float brushSize;
uniform float brushOpacity;
uniform float brushHardness;
uniform vec3 brushColor;
uniform float brushFlow;

// Uniforms - Material properties
uniform float metalness;
uniform float roughness;
uniform float emissive;
uniform float transparency;
uniform vec3 baseColor;

// Uniforms - Lighting
uniform vec3 ambientLightColor;
uniform float ambientLightIntensity;
uniform vec3 directionalLightColor;
uniform float directionalLightIntensity;
uniform vec3 cameraPosition;

// Uniforms - Textures
uniform sampler2D paintTexture;
uniform sampler2D brushTexture;
uniform sampler2D normalMap;
uniform sampler2D roughnessMap;
uniform sampler2D metallicMap;
uniform sampler2D shadowMap;

// Uniforms - Effects
uniform bool enableShadows;
uniform bool enableParticles;
uniform bool enablePhysics;
uniform float time;
uniform float deltaTime;

// Uniforms - Environment
uniform vec3 fogColor;
uniform float fogNear;
uniform float fogFar;
uniform bool enableFog;

// Uniforms - Post-processing
uniform float exposure;
uniform float gamma;
uniform float contrast;
uniform float saturation;

// Noise function for procedural effects
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float noise(vec2 st) {
    vec2 i = floor(st);
    vec2 f = fract(st);
    
    float a = random(i);
    float b = random(i + vec2(1.0, 0.0));
    float c = random(i + vec2(0.0, 1.0));
    float d = random(i + vec2(1.0, 1.0));
    
    vec2 u = f * f * (3.0 - 2.0 * f);
    
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

// Fractional Brownian Motion for complex noise
float fbm(vec2 st) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 0.0;
    
    for (int i = 0; i < 5; i++) {
        value += amplitude * noise(st);
        st *= 2.0;
        amplitude *= 0.5;
    }
    
    return value;
}

// Shadow calculation
float calculateShadow(vec4 shadowCoord) {
    if (!enableShadows) return 1.0;
    
    vec3 projCoords = shadowCoord.xyz / shadowCoord.w;
    projCoords = projCoords * 0.5 + 0.5;
    
    if (projCoords.z > 1.0) return 1.0;
    
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    float currentDepth = projCoords.z;
    
    float bias = 0.005;
    float shadow = currentDepth - bias > closestDepth ? 0.0 : 1.0;
    
    // PCF (Percentage-Closer Filtering) for softer shadows
    float shadowSum = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
            shadowSum += currentDepth - bias > pcfDepth ? 0.0 : 1.0;
        }
    }
    
    return shadowSum / 9.0;
}

// PBR lighting calculation
vec3 calculatePBR(vec3 albedo, vec3 normal, vec3 viewDir, vec3 lightDir, vec3 lightColor, float metallic, float rough) {
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float NdotV = max(dot(normal, viewDir), 0.0);
    float NdotL = max(dot(normal, lightDir), 0.0);
    float NdotH = max(dot(normal, halfwayDir), 0.0);
    float VdotH = max(dot(viewDir, halfwayDir), 0.0);
    
    // Fresnel
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 F = F0 + (1.0 - F0) * pow(1.0 - VdotH, 5.0);
    
    // Distribution
    float alpha = rough * rough;
    float alpha2 = alpha * alpha;
    float denom = NdotH * NdotH * (alpha2 - 1.0) + 1.0;
    float D = alpha2 / (3.14159265 * denom * denom);
    
    // Geometry
    float k = (rough + 1.0) * (rough + 1.0) / 8.0;
    float G1L = NdotL / (NdotL * (1.0 - k) + k);
    float G1V = NdotV / (NdotV * (1.0 - k) + k);
    float G = G1L * G1V;
    
    // BRDF
    vec3 numerator = D * G * F;
    float denominator = 4.0 * NdotV * NdotL + 0.001;
    vec3 specular = numerator / denominator;
    
    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - metallic;
    
    return (kD * albedo / 3.14159265 + specular) * lightColor * NdotL;
}

// Standard brush rendering
vec4 renderStandardBrush() {
    vec3 normal = normalize(vViewNormal);
    vec3 viewDir = normalize(cameraPosition - vWorldPosition);
    vec3 lightDir = normalize(vLightDirection);
    
    // Base color
    vec3 albedo = mix(baseColor, brushColor, vBrushInfluence);
    
    // Sample textures
    vec3 textureColor = texture(paintTexture, vUv).rgb;
    float roughnessValue = texture(roughnessMap, vUv).r * roughness;
    float metallicValue = texture(metallicMap, vUv).r * metalness;
    
    // Calculate lighting
    vec3 color = calculatePBR(albedo * textureColor, normal, viewDir, lightDir, directionalLightColor, metallicValue, roughnessValue);
    
    // Add ambient lighting
    color += albedo * ambientLightColor * ambientLightIntensity;
    
    // Apply shadow
    float shadow = calculateShadow(vShadowCoord);
    color *= shadow;
    
    // Apply brush influence
    float alpha = vOpacity * brushOpacity * vBrushInfluence;
    
    return vec4(color, alpha);
}

// Texture brush rendering
vec4 renderTextureBrush() {
    vec3 normal = normalize(vViewNormal);
    
    // Sample brush texture
    vec4 brushSample = texture(brushTexture, vUv);
    
    // Combine with brush color
    vec3 color = brushColor * brushSample.rgb * vLightIntensity;
    
    // Apply brush influence with texture
    float alpha = vOpacity * brushOpacity * vBrushInfluence * brushSample.a;
    
    return vec4(color, alpha);
}

// Particle brush rendering
vec4 renderParticleBrush() {
    // Calculate particle properties
    float life = vParticleLife;
    float size = vParticleSize;
    
    // Calculate distance from particle center
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    // Create soft circular particles
    float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
    alpha *= life; // Fade based on particle life
    
    // Add some noise for organic look
    float noiseValue = noise(gl_PointCoord * 8.0 + time);
    alpha *= 0.8 + 0.2 * noiseValue;
    
    // Color based on velocity for motion blur effect
    vec3 color = brushColor;
    if (enablePhysics) {
        float speed = length(vVelocity);
        color = mix(color, color * 1.5, speed * 0.1);
    }
    
    alpha *= vOpacity * brushOpacity;
    
    return vec4(color, alpha);
}

// Volumetric brush rendering
vec4 renderVolumetricBrush() {
    vec3 normal = normalize(vViewNormal);
    vec3 viewDir = normalize(cameraPosition - vWorldPosition);
    
    // Create volumetric effect using noise
    vec2 noiseCoord = vUv * 4.0 + time * 0.1;
    float noiseValue = fbm(noiseCoord);
    
    // Calculate depth-based opacity
    float depthFade = 1.0 - smoothstep(0.0, brushSize, vDistance);
    
    // Combine brush influence with noise
    float influence = vBrushInfluence * (0.5 + 0.5 * noiseValue) * depthFade;
    
    // Create rim lighting effect
    float rimLight = 1.0 - abs(dot(normal, viewDir));
    rimLight = pow(rimLight, 2.0);
    
    vec3 color = brushColor * (1.0 + rimLight * 0.5) * vLightIntensity;
    float alpha = vOpacity * brushOpacity * influence;
    
    return vec4(color, alpha);
}

// Fog calculation
vec3 applyFog(vec3 color, float distance) {
    if (!enableFog) return color;
    
    float fogFactor = smoothstep(fogNear, fogFar, distance);
    return mix(color, fogColor, fogFactor);
}

// Tone mapping
vec3 toneMap(vec3 color) {
    // ACES tone mapping
    color *= exposure;
    color = (color * (2.51 * color + 0.03)) / (color * (2.43 * color + 0.59) + 0.14);
    
    // Gamma correction
    color = pow(color, vec3(1.0 / gamma));
    
    // Contrast adjustment
    color = (color - 0.5) * contrast + 0.5;
    
    // Saturation adjustment
    float luminance = dot(color, vec3(0.299, 0.587, 0.114));
    color = mix(vec3(luminance), color, saturation);
    
    return color;
}

void main() {
    vec4 finalColor;
    
    // Render based on brush type
    switch (brushType) {
        case 0: // Standard brush
            finalColor = renderStandardBrush();
            break;
        case 1: // Texture brush
            finalColor = renderTextureBrush();
            break;
        case 2: // Particle brush
            finalColor = renderParticleBrush();
            break;
        case 3: // Volumetric brush
            finalColor = renderVolumetricBrush();
            break;
        default:
            finalColor = vec4(brushColor * vLightIntensity, vOpacity * brushOpacity);
    }
    
    // Apply fog
    finalColor.rgb = applyFog(finalColor.rgb, vDistance);
    
    // Apply tone mapping
    finalColor.rgb = toneMap(finalColor.rgb);
    
    // Clamp values
    finalColor = clamp(finalColor, 0.0, 1.0);
    
    // Early discard for performance
    if (finalColor.a < 0.01) {
        discard;
    }
    
    fragColor = finalColor;
}