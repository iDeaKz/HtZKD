# 3D Paint Studio 🎨

A comprehensive 3D paint style application with advanced graphics capabilities, real-time rendering, and complete error management at every level.

## Features

### 🚀 Core Capabilities
- **Real-time 3D rendering** with hardware acceleration
- **Advanced brush systems** with physics simulation
- **Multi-threaded rendering** pipeline
- **GPU memory management** and optimization
- **Layer management** with alpha blending
- **Dynamic lighting** with shadows
- **Particle effects** for paint splatters

### 🎨 Brush Types
- **Standard Brush**: Classic painting with pressure sensitivity
- **Texture Brush**: Pattern-based painting with custom textures
- **Particle Brush**: Dynamic particle-based effects
- **Volumetric Brush**: 3D paint in volumetric space
- **Physics Brush**: Paint with gravity and fluid simulation

### 🔧 Technical Features
- **WebGL 2.0/1.0** compatibility with fallback support
- **Three.js** integration for 3D graphics
- **Custom GLSL shaders** for advanced effects
- **Memory pooling** and resource optimization
- **Error recovery** mechanisms at every level
- **Performance monitoring** and adaptive quality
- **Touch/stylus support** for drawing tablets

### 📁 File Format Support
- **Native .p3d format** with full layer support
- **Standard image formats**: PNG, JPG, BMP, TIFF, WebP
- **Adobe formats**: PSD (read-only)
- **3D formats**: OBJ, PLY, STL
- **Vector formats**: SVG
- **Archive formats**: ZIP

## Installation

### Prerequisites
- Python 3.8+
- Modern web browser with WebGL support
- 4GB+ RAM (8GB+ recommended)
- Graphics card with OpenGL 3.3+ support

### Quick Start
```bash
# Clone the repository
git clone https://github.com/iDeaKz/HtZKD.git
cd HtZKD

# Install dependencies
pip install -r requirements_updated.txt

# Start the backend server
python backend/main.py

# Open your browser to http://localhost:8000
```

### Development Setup
```bash
# Install development dependencies
npm install

# Start development server with auto-reload
npm run dev

# Run tests
npm test
```

## Architecture

### Frontend Structure
```
frontend/
├── index.html                 # Main application page
├── css/
│   ├── main.css              # Core application styles
│   ├── canvas.css            # Canvas-specific styles
│   └── ui-components.css     # UI component styles
├── js/
│   ├── main.js               # Application lifecycle manager
│   ├── error-handler.js      # Multi-level error management
│   ├── webgl-utils.js        # WebGL utilities and optimization
│   ├── canvas3d.js           # 3D canvas engine with Three.js
│   ├── brush-engine.js       # Advanced brush systems
│   └── ui-manager.js         # UI interaction management
├── shaders/
│   ├── vertex.glsl           # Vertex shaders for 3D effects
│   └── fragment.glsl         # Fragment shaders with PBR lighting
└── assets/
    ├── textures/             # Brush textures and patterns
    ├── brushes/              # Brush definitions
    └── icons/                # UI icons
```

### Backend Structure
```
backend/
├── main.py                   # FastAPI application server
├── api/
│   ├── canvas_api.py         # Canvas operations API
│   └── file_api.py           # File operations API
├── services/
│   ├── gpu_manager.py        # GPU memory management
│   ├── image_processor.py    # Advanced image processing
│   └── file_manager.py       # Multi-format file handling
└── utils/
    ├── error_handler.py      # Backend error management
    ├── logger.py             # Logging configuration
    └── performance.py        # Performance monitoring
```

## API Documentation

### Canvas API
- `POST /api/canvas/create` - Create new canvas
- `GET /api/canvas/status` - Get canvas status
- `POST /api/canvas/strokes` - Add brush stroke
- `POST /api/canvas/layers` - Create layer
- `POST /api/canvas/export` - Export canvas

### File API
- `POST /api/files/upload` - Upload file
- `GET /api/files/list` - List files
- `POST /api/files/convert/{filename}` - Convert file format
- `GET /api/files/download/{filename}` - Download file

### System API
- `GET /health` - Health check
- `GET /api/status` - System status and performance

## Performance Optimization

### Memory Management
- **GPU buffer pooling** for efficient memory allocation
- **Automatic cleanup** of unused resources
- **Memory pressure detection** and adaptive responses
- **Cache optimization** for frequently used assets

### Rendering Optimization
- **Level-of-detail** rendering for complex scenes
- **Frustum culling** for off-screen objects
- **Adaptive quality** based on performance
- **Multi-threaded** rendering pipeline

### Network Optimization
- **Asset streaming** for large textures
- **Compression** for file transfers
- **WebSocket** support for real-time collaboration
- **Progressive loading** of application resources

## Usage Examples

### Basic Painting
```javascript
// Initialize the application
const app = new Paint3DApp();
await app.initialize();

// Select brush and start painting
app.components.uiManager.selectBrush('standard');
app.components.brushEngine.updateSettings({
    size: 20,
    opacity: 0.8,
    color: { r: 1, g: 0, b: 0 }
});

// The application handles mouse/touch events automatically
```

### Custom Brush Creation
```javascript
// Create custom brush
class CustomBrush extends BaseBrush {
    paint(point, stroke) {
        return {
            shape: 'custom',
            size: this.settings.size,
            opacity: this.settings.opacity,
            color: this.settings.color,
            pattern: 'spiral'
        };
    }
}

// Register custom brush
window.BrushEngine.registerBrush('custom', new CustomBrush());
```

### File Operations
```javascript
// Export canvas
await fetch('/api/canvas/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        format: 'png',
        quality: 95,
        include_layers: true
    })
});

// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
await fetch('/api/files/upload', {
    method: 'POST',
    body: formData
});
```

## Configuration

### Environment Variables
```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# GPU settings
MAX_GPU_MEMORY_MB=2048
ENABLE_GPU_MONITORING=true

# File settings
MAX_FILE_SIZE_MB=1024
UPLOAD_DIR=uploads
EXPORT_DIR=exports

# Performance settings
MAX_WORKERS=4
CACHE_SIZE_MB=512
```

### Performance Tuning
```javascript
// Adjust quality settings
window.Canvas3D.setQuality('high');  // high, medium, low

// Configure memory limits
window.BrushEngine.setMemoryLimit(512);  // MB

// Enable/disable features
window.Canvas3D.shadowsEnabled = true;
window.Canvas3D.particlesEnabled = true;
window.Canvas3D.physicsEnabled = true;
```

## Browser Compatibility

### Minimum Requirements
- **Chrome 90+** (recommended)
- **Firefox 88+**
- **Safari 14+**
- **Edge 90+**

### WebGL Support
- **WebGL 2.0** for optimal performance
- **WebGL 1.0** fallback support
- **Software rendering** as last resort

### Mobile Support
- **iOS Safari 14+**
- **Chrome Mobile 90+**
- **Touch and stylus** support
- **Responsive design** for tablets

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open pull request

### Code Standards
- **ES6+ JavaScript** with modern syntax
- **Type annotations** in JSDoc format
- **Comprehensive error handling** at every level
- **Performance-first** approach
- **Accessibility** considerations

### Testing
```bash
# Run all tests
npm test

# Run specific test suites
npm run test:frontend
npm run test:backend
npm run test:integration

# Performance tests
npm run test:performance
```

## Troubleshooting

### Common Issues

#### WebGL Context Lost
- **Cause**: GPU driver issues or memory pressure
- **Solution**: Automatic context restoration implemented
- **Manual fix**: Refresh the page

#### Slow Performance
- **Check**: GPU utilization in browser dev tools
- **Solution**: Lower quality settings or close other GPU applications
- **Automatic**: Adaptive quality adjustment enabled

#### File Upload Errors
- **Check**: File size and format support
- **Solution**: Use supported formats (PNG, JPG, P3D)
- **Limit**: 1GB maximum file size

### Debug Mode
```javascript
// Enable debug mode
localStorage.setItem('debug', 'true');
location.reload();

// Check performance stats
console.log(window.Canvas3D.getPerformanceStats());
console.log(window.BrushEngine.getPerformanceStats());
```

## Performance Metrics

### Target Performance
- **< 16ms frame time** for 60fps rendering
- **< 100MB RAM** for basic operations
- **Zero crashes** during normal usage
- **Instant response** to user input

### Monitoring
- Real-time FPS counter
- Memory usage display
- GPU utilization tracking
- Error rate monitoring

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Three.js** - 3D graphics library
- **WebGL** - Hardware-accelerated graphics
- **FastAPI** - Modern web framework
- **OpenCV** - Computer vision library
- **Contributors** - All the amazing developers

---

**Built with ❤️ for digital artists and creative professionals**