"""
Canvas API for 3D Paint Application
Provides REST endpoints for canvas operations
"""

import logging
import asyncio
import base64
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available, API endpoints will be disabled")

from ..services.image_processor import get_image_processor
from ..services.gpu_manager import get_gpu_manager
from ..services.file_manager import get_file_manager

# Setup logger
logger = logging.getLogger(__name__)

# Pydantic models for request/response
if FASTAPI_AVAILABLE:
    class CanvasSettings(BaseModel):
        width: int = Field(..., gt=0, le=8192)
        height: int = Field(..., gt=0, le=8192)
        background_color: List[int] = Field(default=[255, 255, 255, 255])
        dpi: int = Field(default=72, gt=0, le=600)

    class BrushSettings(BaseModel):
        type: str = Field(..., regex="^(standard|texture|particle|volumetric)$")
        size: float = Field(..., gt=0, le=1000)
        opacity: float = Field(..., ge=0, le=1)
        hardness: float = Field(default=0.8, ge=0, le=1)
        flow: float = Field(default=1.0, ge=0, le=1)
        color: List[float] = Field(..., min_items=3, max_items=4)
        pressure_sensitive: bool = Field(default=True)

    class StrokePoint(BaseModel):
        x: float
        y: float
        z: float = Field(default=0.0)
        pressure: float = Field(default=1.0, ge=0, le=1)
        tilt: float = Field(default=0.0, ge=-90, le=90)
        rotation: float = Field(default=0.0, ge=0, le=360)
        timestamp: float

    class BrushStroke(BaseModel):
        id: str
        layer_id: str
        brush_settings: BrushSettings
        points: List[StrokePoint]
        start_time: float
        end_time: Optional[float] = None

    class LayerInfo(BaseModel):
        id: str
        name: str
        opacity: float = Field(..., ge=0, le=1)
        blend_mode: str = Field(default="normal")
        visible: bool = Field(default=True)
        locked: bool = Field(default=False)
        position: List[int] = Field(default=[0, 0])
        rotation: float = Field(default=0.0)
        scale: List[float] = Field(default=[1.0, 1.0])

    class ProcessingRequest(BaseModel):
        operation: str
        parameters: Dict[str, Any] = Field(default_factory=dict)
        layer_id: Optional[str] = None

    class ExportRequest(BaseModel):
        format: str = Field(..., regex="^(png|jpg|jpeg|bmp|tiff|webp|obj|p3d)$")
        quality: int = Field(default=95, ge=1, le=100)
        include_layers: bool = Field(default=False)
        layer_ids: Optional[List[str]] = None

    class PerformanceStats(BaseModel):
        fps: float
        memory_usage_mb: float
        gpu_utilization: float
        active_strokes: int
        layer_count: int

    class ErrorResponse(BaseModel):
        error: str
        message: str
        timestamp: datetime
        request_id: Optional[str] = None

# Create router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/canvas", tags=["canvas"])
else:
    router = None

# Canvas state management
class CanvasState:
    def __init__(self):
        self.settings = None
        self.layers = {}
        self.active_strokes = {}
        self.performance_stats = {}
        self.session_id = None

# Global canvas state
canvas_state = CanvasState()

# API endpoints
if FASTAPI_AVAILABLE:
    
    @router.post("/create")
    async def create_canvas(settings: CanvasSettings, background_tasks: BackgroundTasks):
        """Create a new canvas with specified settings"""
        try:
            logger.info(f"Creating canvas: {settings.width}x{settings.height}")
            
            # Validate settings
            if settings.width * settings.height > 32 * 1024 * 1024:  # 32MP limit
                raise HTTPException(status_code=400, detail="Canvas size too large")
            
            # Initialize GPU resources
            gpu_manager = get_gpu_manager()
            estimated_memory_mb = (settings.width * settings.height * 4) // (1024 * 1024)  # RGBA
            
            buffer_id = gpu_manager.allocate_buffer(estimated_memory_mb, 'canvas', 'dynamic')
            if not buffer_id:
                raise HTTPException(status_code=507, detail="Insufficient GPU memory")
            
            # Update canvas state
            canvas_state.settings = settings
            canvas_state.layers = {}
            canvas_state.active_strokes = {}
            canvas_state.session_id = f"session_{int(datetime.now().timestamp())}"
            
            # Create default background layer
            background_layer = LayerInfo(
                id="background",
                name="Background",
                opacity=1.0,
                blend_mode="normal",
                visible=True,
                locked=True
            )
            canvas_state.layers["background"] = background_layer
            
            # Schedule cleanup task
            background_tasks.add_task(cleanup_old_resources)
            
            return {
                "status": "success",
                "session_id": canvas_state.session_id,
                "canvas_settings": settings.dict(),
                "buffer_id": buffer_id,
                "estimated_memory_mb": estimated_memory_mb
            }
            
        except Exception as e:
            logger.error(f"Failed to create canvas: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/status")
    async def get_canvas_status():
        """Get current canvas status and performance metrics"""
        try:
            gpu_manager = get_gpu_manager()
            gpu_stats = gpu_manager.get_performance_stats()
            
            image_processor = await get_image_processor()
            processing_stats = image_processor.get_performance_stats()
            
            file_manager = get_file_manager()
            file_stats = file_manager.get_performance_stats()
            
            return {
                "session_id": canvas_state.session_id,
                "canvas_settings": canvas_state.settings.dict() if canvas_state.settings else None,
                "layer_count": len(canvas_state.layers),
                "active_strokes": len(canvas_state.active_strokes),
                "performance": {
                    "gpu": gpu_stats,
                    "image_processing": processing_stats,
                    "file_operations": file_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get canvas status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/layers")
    async def create_layer(layer_info: LayerInfo):
        """Create a new layer"""
        try:
            if layer_info.id in canvas_state.layers:
                raise HTTPException(status_code=409, detail="Layer ID already exists")
            
            if not canvas_state.settings:
                raise HTTPException(status_code=400, detail="No canvas created")
            
            # Allocate GPU memory for layer
            gpu_manager = get_gpu_manager()
            layer_memory_mb = (canvas_state.settings.width * canvas_state.settings.height * 4) // (1024 * 1024)
            
            buffer_id = gpu_manager.allocate_buffer(layer_memory_mb, 'layer', 'dynamic')
            if not buffer_id:
                raise HTTPException(status_code=507, detail="Insufficient GPU memory for layer")
            
            canvas_state.layers[layer_info.id] = layer_info
            
            logger.info(f"Created layer: {layer_info.id} ({layer_info.name})")
            
            return {
                "status": "success",
                "layer_id": layer_info.id,
                "buffer_id": buffer_id,
                "memory_mb": layer_memory_mb
            }
            
        except Exception as e:
            logger.error(f"Failed to create layer: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/layers")
    async def get_layers():
        """Get all layers"""
        try:
            layers = [layer.dict() for layer in canvas_state.layers.values()]
            return {"layers": layers}
            
        except Exception as e:
            logger.error(f"Failed to get layers: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/layers/{layer_id}")
    async def update_layer(layer_id: str, layer_info: LayerInfo):
        """Update layer properties"""
        try:
            if layer_id not in canvas_state.layers:
                raise HTTPException(status_code=404, detail="Layer not found")
            
            canvas_state.layers[layer_id] = layer_info
            
            logger.info(f"Updated layer: {layer_id}")
            
            return {"status": "success", "layer_id": layer_id}
            
        except Exception as e:
            logger.error(f"Failed to update layer: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.delete("/layers/{layer_id}")
    async def delete_layer(layer_id: str):
        """Delete a layer"""
        try:
            if layer_id not in canvas_state.layers:
                raise HTTPException(status_code=404, detail="Layer not found")
            
            if layer_id == "background":
                raise HTTPException(status_code=400, detail="Cannot delete background layer")
            
            # Clean up GPU resources
            gpu_manager = get_gpu_manager()
            # Note: In a real implementation, we'd track buffer IDs per layer
            
            del canvas_state.layers[layer_id]
            
            logger.info(f"Deleted layer: {layer_id}")
            
            return {"status": "success", "layer_id": layer_id}
            
        except Exception as e:
            logger.error(f"Failed to delete layer: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/strokes")
    async def create_brush_stroke(stroke: BrushStroke, background_tasks: BackgroundTasks):
        """Create a new brush stroke"""
        try:
            if stroke.layer_id not in canvas_state.layers:
                raise HTTPException(status_code=404, detail="Layer not found")
            
            canvas_state.active_strokes[stroke.id] = stroke
            
            # Process stroke asynchronously
            image_processor = await get_image_processor()
            task_id = await image_processor.process_image_async(
                image_data=None,  # This would be actual canvas data
                operation='brush_stroke',
                stroke_data=stroke.dict()
            )
            
            logger.info(f"Created brush stroke: {stroke.id} on layer {stroke.layer_id}")
            
            return {
                "status": "success",
                "stroke_id": stroke.id,
                "processing_task_id": task_id,
                "point_count": len(stroke.points)
            }
            
        except Exception as e:
            logger.error(f"Failed to create brush stroke: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/strokes/{stroke_id}")
    async def get_brush_stroke(stroke_id: str):
        """Get brush stroke information"""
        try:
            if stroke_id not in canvas_state.active_strokes:
                raise HTTPException(status_code=404, detail="Stroke not found")
            
            stroke = canvas_state.active_strokes[stroke_id]
            return {"stroke": stroke.dict()}
            
        except Exception as e:
            logger.error(f"Failed to get brush stroke: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/process")
    async def process_canvas(request: ProcessingRequest):
        """Process canvas with specified operation"""
        try:
            image_processor = await get_image_processor()
            
            # Get canvas data (simplified - would get actual pixel data)
            canvas_data = None  # This would be the actual canvas pixel data
            
            task_id = await image_processor.process_image_async(
                image_data=canvas_data,
                operation=request.operation,
                **request.parameters
            )
            
            logger.info(f"Started processing operation: {request.operation}")
            
            return {
                "status": "processing",
                "task_id": task_id,
                "operation": request.operation,
                "estimated_time_ms": 1000  # Estimate based on operation
            }
            
        except Exception as e:
            logger.error(f"Failed to process canvas: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/process/{task_id}")
    async def get_processing_status(task_id: str):
        """Get processing task status"""
        try:
            image_processor = await get_image_processor()
            status = image_processor.get_task_status(task_id)
            
            if not status:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/export")
    async def export_canvas(request: ExportRequest, background_tasks: BackgroundTasks):
        """Export canvas to specified format"""
        try:
            if not canvas_state.settings:
                raise HTTPException(status_code=400, detail="No canvas to export")
            
            # Create project data for export
            from ..services.file_manager import ProjectData, FileMetadata
            
            metadata = FileMetadata(
                filename=f"canvas_export.{request.format}",
                size_bytes=0,  # Will be calculated
                format=request.format,
                version="1.0",
                created_at=datetime.now(),
                modified_at=datetime.now(),
                checksum=""  # Will be calculated
            )
            
            # Convert layers to export format
            layers = []
            for layer in canvas_state.layers.values():
                # This would convert actual layer data
                pass
            
            project_data = ProjectData(
                metadata=metadata,
                canvas_settings=canvas_state.settings.dict(),
                layers=layers,
                brush_strokes=list(canvas_state.active_strokes.values()),
                camera_settings={},
                lighting_settings={}
            )
            
            # Start export process
            file_manager = get_file_manager()
            export_path = f"/tmp/export_{int(datetime.now().timestamp())}.{request.format}"
            
            # Schedule export task
            background_tasks.add_task(
                export_canvas_task, 
                file_manager, 
                project_data, 
                export_path, 
                request.dict()
            )
            
            logger.info(f"Started canvas export to {request.format}")
            
            return {
                "status": "exporting",
                "format": request.format,
                "export_path": export_path,
                "estimated_size_mb": (canvas_state.settings.width * canvas_state.settings.height * 4) // (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Failed to export canvas: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/upload")
    async def upload_file(file: UploadFile = File(...), layer_id: str = Form(None)):
        """Upload and import a file to canvas"""
        try:
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file size (limit to 100MB)
            max_size = 100 * 1024 * 1024
            file_size = 0
            content = b""
            
            while chunk := await file.read(1024):
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(status_code=413, detail="File too large")
                content += chunk
            
            # Save temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{file.filename.split('.')[-1]}", delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Import file
            file_manager = get_file_manager()
            project_data = await file_manager.read_file(temp_path)
            
            # Process imported data
            if layer_id and layer_id in canvas_state.layers:
                # Import to specific layer
                pass
            else:
                # Create new layers from imported data
                for imported_layer in project_data.layers:
                    canvas_state.layers[imported_layer.id] = LayerInfo(
                        id=imported_layer.id,
                        name=imported_layer.name,
                        opacity=imported_layer.opacity,
                        blend_mode=imported_layer.blend_mode,
                        visible=imported_layer.visible,
                        locked=imported_layer.locked
                    )
            
            # Clean up temp file
            import os
            os.unlink(temp_path)
            
            logger.info(f"Imported file: {file.filename}")
            
            return {
                "status": "success",
                "filename": file.filename,
                "file_size_mb": file_size / (1024 * 1024),
                "layers_imported": len(project_data.layers),
                "strokes_imported": len(project_data.brush_strokes)
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/clear")
    async def clear_canvas():
        """Clear the entire canvas"""
        try:
            # Clear all layers except background
            layers_to_remove = [lid for lid in canvas_state.layers.keys() if lid != "background"]
            for layer_id in layers_to_remove:
                del canvas_state.layers[layer_id]
            
            # Clear all strokes
            canvas_state.active_strokes.clear()
            
            # Trigger GPU cleanup
            gpu_manager = get_gpu_manager()
            gpu_manager.cleanup_unused_resources()
            
            logger.info("Canvas cleared")
            
            return {
                "status": "success",
                "layers_removed": len(layers_to_remove),
                "strokes_cleared": len(canvas_state.active_strokes)
            }
            
        except Exception as e:
            logger.error(f"Failed to clear canvas: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Background tasks

async def cleanup_old_resources():
    """Clean up old GPU resources"""
    try:
        gpu_manager = get_gpu_manager()
        cleaned = gpu_manager.cleanup_unused_resources()
        logger.info(f"Cleaned up {cleaned} old GPU resources")
    except Exception as e:
        logger.error(f"Failed to cleanup resources: {e}")

async def export_canvas_task(file_manager, project_data, export_path, options):
    """Background task for canvas export"""
    try:
        await file_manager.write_file(project_data, export_path, **options)
        logger.info(f"Canvas exported to: {export_path}")
    except Exception as e:
        logger.error(f"Export task failed: {e}")

# Error handlers

if FASTAPI_AVAILABLE:
    @router.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return ErrorResponse(
            error="http_error",
            message=exc.detail,
            timestamp=datetime.now(),
            request_id=getattr(request.state, 'request_id', None)
        )
    
    @router.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}")
        return ErrorResponse(
            error="internal_error",
            message="An internal error occurred",
            timestamp=datetime.now(),
            request_id=getattr(request.state, 'request_id', None)
        )

def get_canvas_router():
    """Get the canvas API router"""
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI not available")
    return router