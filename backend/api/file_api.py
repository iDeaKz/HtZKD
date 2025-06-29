"""
File API for 3D Paint Application
Provides REST endpoints for file operations
"""

import logging
import asyncio
import os
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

try:
    from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
    from fastapi.responses import FileResponse, StreamingResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available, file API endpoints will be disabled")

from ..services.file_manager import get_file_manager

# Setup logger
logger = logging.getLogger(__name__)

# Pydantic models
if FASTAPI_AVAILABLE:
    class FileInfo(BaseModel):
        filename: str
        size_bytes: int
        format: str
        created_at: datetime
        modified_at: datetime
        checksum: str
        supported_operations: List[str]

    class FileListResponse(BaseModel):
        files: List[FileInfo]
        total_count: int
        total_size_bytes: int

    class ConversionRequest(BaseModel):
        source_format: str
        target_format: str
        quality: int = Field(default=95, ge=1, le=100)
        compression_level: int = Field(default=6, ge=1, le=9)
        preserve_layers: bool = Field(default=True)
        custom_options: Dict[str, Any] = Field(default_factory=dict)

    class ConversionStatus(BaseModel):
        task_id: str
        status: str
        progress: float
        source_file: str
        target_file: str
        start_time: datetime
        estimated_completion: Optional[datetime] = None
        error_message: Optional[str] = None

# Create router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/files", tags=["files"])
else:
    router = None

# File operation tracking
active_operations = {}
upload_directory = Path("uploads")
export_directory = Path("exports")

# Ensure directories exist
upload_directory.mkdir(exist_ok=True)
export_directory.mkdir(exist_ok=True)

if FASTAPI_AVAILABLE:
    
    @router.post("/upload")
    async def upload_file(file: UploadFile = File(...), overwrite: bool = Form(False)):
        """Upload a file to the server"""
        try:
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Validate file format
            file_manager = get_file_manager()
            file_ext = Path(file.filename).suffix.lower()
            supported_formats = file_manager.get_supported_formats()
            
            if file_ext not in supported_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file format: {file_ext}"
                )
            
            if not supported_formats[file_ext]['read']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Reading not supported for format: {file_ext}"
                )
            
            # Check file size (limit to 1GB)
            max_size = 1024 * 1024 * 1024
            file_size = 0
            
            # Prepare upload path
            upload_path = upload_directory / file.filename
            
            if upload_path.exists() and not overwrite:
                raise HTTPException(
                    status_code=409, 
                    detail="File already exists. Use overwrite=true to replace."
                )
            
            # Stream file to disk
            with open(upload_path, "wb") as buffer:
                while chunk := await file.read(8192):
                    file_size += len(chunk)
                    if file_size > max_size:
                        # Clean up partial file
                        buffer.close()
                        upload_path.unlink()
                        raise HTTPException(status_code=413, detail="File too large")
                    buffer.write(chunk)
            
            # Validate file integrity
            try:
                project_data = await file_manager.read_file(upload_path)
                
                file_info = FileInfo(
                    filename=file.filename,
                    size_bytes=file_size,
                    format=file_ext,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    checksum=file_manager._calculate_file_checksum(upload_path),
                    supported_operations=["read", "convert", "download"]
                )
                
                logger.info(f"File uploaded successfully: {file.filename} ({file_size} bytes)")
                
                return {
                    "status": "success",
                    "file_info": file_info.dict(),
                    "layers_count": len(project_data.layers),
                    "strokes_count": len(project_data.brush_strokes),
                    "canvas_size": f"{project_data.canvas_settings.get('width', 0)}x{project_data.canvas_settings.get('height', 0)}"
                }
                
            except Exception as e:
                # Clean up invalid file
                upload_path.unlink()
                raise HTTPException(
                    status_code=400, 
                    detail=f"File validation failed: {str(e)}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")
    
    @router.get("/list")
    async def list_files(
        directory: str = "uploads",
        format_filter: Optional[str] = None,
        sort_by: str = "modified_at",
        sort_desc: bool = True
    ):
        """List uploaded files"""
        try:
            if directory == "uploads":
                target_dir = upload_directory
            elif directory == "exports":
                target_dir = export_directory
            else:
                raise HTTPException(status_code=400, detail="Invalid directory")
            
            files = []
            total_size = 0
            
            file_manager = get_file_manager()
            supported_formats = file_manager.get_supported_formats()
            
            for file_path in target_dir.iterdir():
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    
                    # Apply format filter
                    if format_filter and file_ext != format_filter:
                        continue
                    
                    # Get file stats
                    stat = file_path.stat()
                    
                    # Determine supported operations
                    operations = []
                    if file_ext in supported_formats:
                        if supported_formats[file_ext]['read']:
                            operations.extend(["read", "download"])
                        if supported_formats[file_ext]['write']:
                            operations.append("convert")
                    
                    file_info = FileInfo(
                        filename=file_path.name,
                        size_bytes=stat.st_size,
                        format=file_ext,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                        checksum=file_manager._calculate_file_checksum(file_path),
                        supported_operations=operations
                    )
                    
                    files.append(file_info)
                    total_size += stat.st_size
            
            # Sort files
            if sort_by in ["filename", "size_bytes", "created_at", "modified_at"]:
                files.sort(key=lambda f: getattr(f, sort_by), reverse=sort_desc)
            
            return FileListResponse(
                files=files,
                total_count=len(files),
                total_size_bytes=total_size
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise HTTPException(status_code=500, detail="Failed to list files")
    
    @router.get("/download/{filename}")
    async def download_file(filename: str, directory: str = "uploads"):
        """Download a file"""
        try:
            if directory == "uploads":
                target_dir = upload_directory
            elif directory == "exports":
                target_dir = export_directory
            else:
                raise HTTPException(status_code=400, detail="Invalid directory")
            
            file_path = target_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/octet-stream"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise HTTPException(status_code=500, detail="Download failed")
    
    @router.delete("/delete/{filename}")
    async def delete_file(filename: str, directory: str = "uploads"):
        """Delete a file"""
        try:
            if directory == "uploads":
                target_dir = upload_directory
            elif directory == "exports":
                target_dir = export_directory
            else:
                raise HTTPException(status_code=400, detail="Invalid directory")
            
            file_path = target_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            file_size = file_path.stat().st_size
            file_path.unlink()
            
            logger.info(f"File deleted: {filename}")
            
            return {
                "status": "success",
                "filename": filename,
                "size_bytes": file_size,
                "deleted_at": datetime.now()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise HTTPException(status_code=500, detail="Delete failed")
    
    @router.post("/convert/{filename}")
    async def convert_file(filename: str, request: ConversionRequest):
        """Convert a file to another format"""
        try:
            source_path = upload_directory / filename
            
            if not source_path.exists():
                raise HTTPException(status_code=404, detail="Source file not found")
            
            # Validate conversion
            file_manager = get_file_manager()
            supported_formats = file_manager.get_supported_formats()
            
            if request.source_format not in supported_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported source format: {request.source_format}"
                )
            
            if request.target_format not in supported_formats:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported target format: {request.target_format}"
                )
            
            if not supported_formats[request.source_format]['read']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Reading not supported for: {request.source_format}"
                )
            
            if not supported_formats[request.target_format]['write']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Writing not supported for: {request.target_format}"
                )
            
            # Generate task ID and output filename
            task_id = f"convert_{int(datetime.now().timestamp())}"
            output_filename = f"{Path(filename).stem}.{request.target_format.lstrip('.')}"
            output_path = export_directory / output_filename
            
            # Start conversion task
            conversion_task = asyncio.create_task(
                perform_conversion(
                    task_id, source_path, output_path, request
                )
            )
            
            # Track operation
            active_operations[task_id] = ConversionStatus(
                task_id=task_id,
                status="started",
                progress=0.0,
                source_file=filename,
                target_file=output_filename,
                start_time=datetime.now()
            )
            
            logger.info(f"Started conversion: {filename} -> {output_filename}")
            
            return {
                "status": "started",
                "task_id": task_id,
                "source_file": filename,
                "target_file": output_filename,
                "estimated_time_seconds": 30
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise HTTPException(status_code=500, detail="Conversion failed")
    
    @router.get("/convert/status/{task_id}")
    async def get_conversion_status(task_id: str):
        """Get conversion task status"""
        try:
            if task_id not in active_operations:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return active_operations[task_id].dict()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get conversion status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get status")
    
    @router.get("/formats")
    async def get_supported_formats():
        """Get list of supported file formats"""
        try:
            file_manager = get_file_manager()
            formats = file_manager.get_supported_formats()
            
            format_info = {}
            for ext, capabilities in formats.items():
                format_info[ext] = {
                    "extension": ext,
                    "can_read": capabilities['read'],
                    "can_write": capabilities['write'],
                    "supports_layers": capabilities['layers'],
                    "supports_compression": capabilities['compression']
                }
            
            return {
                "formats": format_info,
                "total_formats": len(formats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get formats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get formats")
    
    @router.get("/info/{filename}")
    async def get_file_info(filename: str, directory: str = "uploads"):
        """Get detailed file information"""
        try:
            if directory == "uploads":
                target_dir = upload_directory
            elif directory == "exports":
                target_dir = export_directory
            else:
                raise HTTPException(status_code=400, detail="Invalid directory")
            
            file_path = target_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            # Read file to get detailed info
            file_manager = get_file_manager()
            
            try:
                project_data = await file_manager.read_file(file_path)
                
                detailed_info = {
                    "filename": filename,
                    "file_size_bytes": file_path.stat().st_size,
                    "format": project_data.metadata.format,
                    "version": project_data.metadata.version,
                    "created_at": project_data.metadata.created_at,
                    "modified_at": project_data.metadata.modified_at,
                    "checksum": project_data.metadata.checksum,
                    "canvas_settings": project_data.canvas_settings,
                    "layer_count": len(project_data.layers),
                    "stroke_count": len(project_data.brush_strokes),
                    "layers": [
                        {
                            "id": layer.id,
                            "name": layer.name,
                            "width": layer.width,
                            "height": layer.height,
                            "opacity": layer.opacity,
                            "visible": layer.visible,
                            "size_bytes": len(layer.data)
                        }
                        for layer in project_data.layers
                    ]
                }
                
                return detailed_info
                
            except Exception as e:
                # Fallback to basic file info
                stat = file_path.stat()
                return {
                    "filename": filename,
                    "file_size_bytes": stat.st_size,
                    "format": file_path.suffix.lower(),
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime),
                    "error": f"Could not read file details: {str(e)}"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get file info")
    
    @router.post("/cleanup")
    async def cleanup_files(
        older_than_hours: int = 24,
        directory: str = "all",
        dry_run: bool = False
    ):
        """Clean up old files"""
        try:
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            
            directories = []
            if directory == "all":
                directories = [upload_directory, export_directory]
            elif directory == "uploads":
                directories = [upload_directory]
            elif directory == "exports":
                directories = [export_directory]
            else:
                raise HTTPException(status_code=400, detail="Invalid directory")
            
            cleaned_files = []
            total_size_freed = 0
            
            for target_dir in directories:
                for file_path in target_dir.iterdir():
                    if file_path.is_file():
                        if file_path.stat().st_mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            
                            cleaned_files.append({
                                "filename": file_path.name,
                                "directory": target_dir.name,
                                "size_bytes": file_size,
                                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime)
                            })
                            
                            total_size_freed += file_size
                            
                            if not dry_run:
                                file_path.unlink()
            
            logger.info(f"Cleanup completed: {len(cleaned_files)} files, {total_size_freed} bytes freed")
            
            return {
                "status": "completed" if not dry_run else "dry_run",
                "files_cleaned": len(cleaned_files),
                "total_size_freed_bytes": total_size_freed,
                "files": cleaned_files
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise HTTPException(status_code=500, detail="Cleanup failed")

# Background tasks

async def perform_conversion(task_id: str, source_path: Path, output_path: Path, request: ConversionRequest):
    """Perform file conversion in background"""
    try:
        # Update status
        active_operations[task_id].status = "reading"
        active_operations[task_id].progress = 10.0
        
        # Read source file
        file_manager = get_file_manager()
        project_data = await file_manager.read_file(source_path, request.source_format)
        
        # Update status
        active_operations[task_id].status = "converting"
        active_operations[task_id].progress = 50.0
        
        # Prepare conversion options
        conversion_options = {
            "quality": request.quality,
            "compression_level": request.compression_level,
            **request.custom_options
        }
        
        # Handle layer preservation
        if not request.preserve_layers:
            # Flatten layers for formats that don't support them
            pass  # Implementation would go here
        
        # Update status
        active_operations[task_id].status = "writing"
        active_operations[task_id].progress = 80.0
        
        # Write output file
        await file_manager.write_file(
            project_data, 
            output_path, 
            request.target_format,
            **conversion_options
        )
        
        # Update status
        active_operations[task_id].status = "completed"
        active_operations[task_id].progress = 100.0
        active_operations[task_id].estimated_completion = datetime.now()
        
        logger.info(f"Conversion completed: {task_id}")
        
    except Exception as e:
        active_operations[task_id].status = "failed"
        active_operations[task_id].error_message = str(e)
        logger.error(f"Conversion failed: {task_id} - {e}")

def get_file_router():
    """Get the file API router"""
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI not available")
    return router