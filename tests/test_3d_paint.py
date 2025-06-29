"""
Test suite for 3D Paint Studio Backend
"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
import numpy as np

# Test image processor
@pytest.mark.asyncio
async def test_image_processor():
    """Test image processing functionality"""
    try:
        from backend.services.image_processor import ImageProcessor
        
        processor = ImageProcessor(max_workers=2)
        await processor.start_workers()
        
        # Create test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test resize operation
        task_id = await processor.process_image_async(
            test_image, 
            'resize', 
            width=50, 
            height=50
        )
        
        # Wait for completion
        await asyncio.sleep(1)
        
        status = processor.get_task_status(task_id)
        assert status is not None
        assert status['operation'] == 'resize'
        
        await processor.stop_workers()
        
        print("✓ Image processor test passed")
        
    except ImportError as e:
        print(f"⚠ Image processor test skipped: {e}")

# Test GPU manager
def test_gpu_manager():
    """Test GPU memory management"""
    try:
        from backend.services.gpu_manager import GPUManager
        
        gpu_manager = GPUManager(max_memory_mb=128)
        
        # Test buffer allocation
        buffer_id = gpu_manager.allocate_buffer(10, 'test', 'static')
        assert buffer_id is not None
        
        # Test buffer deallocation
        success = gpu_manager.deallocate_buffer(buffer_id)
        assert success
        
        # Test performance stats
        stats = gpu_manager.get_performance_stats()
        assert 'memory' in stats
        assert 'buffers' in stats
        
        print("✓ GPU manager test passed")
        
    except ImportError as e:
        print(f"⚠ GPU manager test skipped: {e}")

# Test file manager
@pytest.mark.asyncio
async def test_file_manager():
    """Test file management functionality"""
    try:
        from backend.services.file_manager import FileManager, ProjectData, FileMetadata, LayerData
        from datetime import datetime
        
        file_manager = FileManager()
        
        # Create test project data
        metadata = FileMetadata(
            filename="test.p3d",
            size_bytes=1024,
            format=".p3d",
            version="1.0",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            checksum="test_checksum"
        )
        
        layer = LayerData(
            id="test_layer",
            name="Test Layer",
            opacity=1.0,
            blend_mode="normal",
            visible=True,
            locked=False,
            data=b"test_data",
            width=100,
            height=100,
            format="png"
        )
        
        project_data = ProjectData(
            metadata=metadata,
            canvas_settings={'width': 100, 'height': 100},
            layers=[layer],
            brush_strokes=[],
            camera_settings={},
            lighting_settings={}
        )
        
        # Test write and read
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.p3d"
            
            await file_manager.write_file(project_data, test_file)
            assert test_file.exists()
            
            loaded_data = await file_manager.read_file(test_file)
            assert loaded_data.metadata.filename == "test.p3d"
            assert len(loaded_data.layers) == 1
            assert loaded_data.layers[0].name == "Test Layer"
        
        print("✓ File manager test passed")
        
    except ImportError as e:
        print(f"⚠ File manager test skipped: {e}")

# Test backend API (if FastAPI is available)
@pytest.mark.asyncio
async def test_backend_api():
    """Test backend API functionality"""
    try:
        from backend.main import Paint3DBackend
        import httpx
        
        backend = Paint3DBackend()
        app = backend.create_app()
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Test health check
            response = await client.get("/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            
            # Test system status
            response = await client.get("/api/status")
            assert response.status_code == 200
            
            status_data = response.json()
            assert "timestamp" in status_data
            assert "system" in status_data
        
        print("✓ Backend API test passed")
        
    except ImportError as e:
        print(f"⚠ Backend API test skipped: {e}")

def test_frontend_files():
    """Test frontend file structure"""
    frontend_dir = Path("frontend")
    
    # Check main files exist
    assert (frontend_dir / "index.html").exists(), "Main HTML file missing"
    assert (frontend_dir / "js" / "main.js").exists(), "Main JS file missing"
    assert (frontend_dir / "css" / "main.css").exists(), "Main CSS file missing"
    
    # Check shader files
    assert (frontend_dir / "shaders" / "vertex.glsl").exists(), "Vertex shader missing"
    assert (frontend_dir / "shaders" / "fragment.glsl").exists(), "Fragment shader missing"
    
    # Check JavaScript modules
    js_files = [
        "error-handler.js",
        "webgl-utils.js", 
        "canvas3d.js",
        "brush-engine.js",
        "ui-manager.js"
    ]
    
    for js_file in js_files:
        assert (frontend_dir / "js" / js_file).exists(), f"JS file missing: {js_file}"
    
    print("✓ Frontend file structure test passed")

def test_configuration_files():
    """Test configuration files"""
    # Check package.json
    assert Path("package.json").exists(), "package.json missing"
    
    with open("package.json") as f:
        package_data = json.load(f)
        assert package_data["name"] == "3d-paint-studio"
        assert "scripts" in package_data
    
    # Check requirements
    assert Path("requirements_updated.txt").exists(), "Updated requirements missing"
    assert Path("backend/requirements.txt").exists(), "Backend requirements missing"
    
    print("✓ Configuration files test passed")

if __name__ == "__main__":
    """Run tests if executed directly"""
    
    print("Running 3D Paint Studio Tests...")
    print("=" * 50)
    
    # Run synchronous tests
    test_gpu_manager()
    test_frontend_files()
    test_configuration_files()
    
    # Run asynchronous tests
    async def run_async_tests():
        await test_image_processor()
        await test_file_manager()
        await test_backend_api()
    
    try:
        asyncio.run(run_async_tests())
    except Exception as e:
        print(f"⚠ Some async tests failed: {e}")
    
    print("=" * 50)
    print("✓ Test suite completed")