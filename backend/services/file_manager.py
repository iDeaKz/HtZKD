"""
File Manager for 3D Paint Application
Handles multiple file formats with comprehensive error management
"""

import logging
import asyncio
import json
import struct
import zipfile
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional, Union, Any, BinaryIO
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import base64
import hashlib

# Setup logger
logger = logging.getLogger(__name__)

@dataclass
class FileMetadata:
    """File metadata structure"""
    filename: str
    size_bytes: int
    format: str
    version: str
    created_at: datetime
    modified_at: datetime
    checksum: str
    compression: Optional[str] = None
    encryption: Optional[str] = None
    custom_data: Optional[Dict] = None

@dataclass
class LayerData:
    """Layer data structure for 3D paint files"""
    id: str
    name: str
    opacity: float
    blend_mode: str
    visible: bool
    locked: bool
    data: bytes
    width: int
    height: int
    format: str
    position: Tuple[int, int] = (0, 0)
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)

@dataclass
class BrushStrokeData:
    """Brush stroke data structure"""
    id: str
    layer_id: str
    brush_type: str
    points: List[Dict]
    settings: Dict
    timestamp: float

@dataclass
class ProjectData:
    """Complete project data structure"""
    metadata: FileMetadata
    canvas_settings: Dict
    layers: List[LayerData]
    brush_strokes: List[BrushStrokeData]
    camera_settings: Dict
    lighting_settings: Dict
    custom_data: Optional[Dict] = None

class FileManager:
    """
    Comprehensive file management system supporting multiple formats
    """
    
    def __init__(self, temp_dir: Optional[Path] = None, max_file_size_mb: int = 1024):
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "paint3d"
        self.max_file_size_mb = max_file_size_mb
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported formats
        self.supported_formats = {
            # Native format
            '.p3d': self._handle_p3d_format,
            
            # Image formats
            '.png': self._handle_png_format,
            '.jpg': self._handle_jpg_format,
            '.jpeg': self._handle_jpg_format,
            '.bmp': self._handle_bmp_format,
            '.tiff': self._handle_tiff_format,
            '.webp': self._handle_webp_format,
            
            # Adobe formats
            '.psd': self._handle_psd_format,
            '.psb': self._handle_psb_format,
            
            # 3D formats
            '.obj': self._handle_obj_format,
            '.ply': self._handle_ply_format,
            '.stl': self._handle_stl_format,
            
            # Vector formats
            '.svg': self._handle_svg_format,
            
            # Archive formats
            '.zip': self._handle_zip_format,
            '.tar': self._handle_tar_format
        }
        
        # Format capabilities
        self.format_capabilities = {
            '.p3d': {'read': True, 'write': True, 'layers': True, 'compression': True},
            '.png': {'read': True, 'write': True, 'layers': False, 'compression': True},
            '.jpg': {'read': True, 'write': True, 'layers': False, 'compression': True},
            '.jpeg': {'read': True, 'write': True, 'layers': False, 'compression': True},
            '.bmp': {'read': True, 'write': True, 'layers': False, 'compression': False},
            '.tiff': {'read': True, 'write': True, 'layers': True, 'compression': True},
            '.webp': {'read': True, 'write': True, 'layers': False, 'compression': True},
            '.psd': {'read': True, 'write': False, 'layers': True, 'compression': True},
            '.psb': {'read': True, 'write': False, 'layers': True, 'compression': True},
            '.obj': {'read': True, 'write': True, 'layers': False, 'compression': False},
            '.ply': {'read': True, 'write': True, 'layers': False, 'compression': False},
            '.stl': {'read': True, 'write': True, 'layers': False, 'compression': False},
            '.svg': {'read': True, 'write': True, 'layers': True, 'compression': False},
            '.zip': {'read': True, 'write': True, 'layers': True, 'compression': True},
        }
        
        # Performance tracking
        self.performance_stats = {
            'files_read': 0,
            'files_written': 0,
            'bytes_read': 0,
            'bytes_written': 0,
            'read_errors': 0,
            'write_errors': 0,
            'compression_ratio': 0.0,
            'avg_read_speed_mbps': 0.0,
            'avg_write_speed_mbps': 0.0
        }
        
        logger.info(f"File Manager initialized with temp dir: {self.temp_dir}")
    
    # Public API methods
    
    async def read_file(self, file_path: Union[str, Path], 
                       format_hint: Optional[str] = None) -> ProjectData:
        """
        Read file and return project data
        
        Args:
            file_path: Path to file
            format_hint: Optional format hint to override detection
            
        Returns:
            ProjectData object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
        
        # Detect format
        format_ext = format_hint or file_path.suffix.lower()
        
        if format_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {format_ext}")
        
        if not self.format_capabilities[format_ext]['read']:
            raise ValueError(f"Reading not supported for format: {format_ext}")
        
        try:
            # Get handler for format
            handler = self.supported_formats[format_ext]
            
            # Read file
            start_time = asyncio.get_event_loop().time()
            project_data = await handler(file_path, 'read')
            end_time = asyncio.get_event_loop().time()
            
            # Update stats
            read_time = end_time - start_time
            file_size_bytes = file_path.stat().st_size
            
            self.performance_stats['files_read'] += 1
            self.performance_stats['bytes_read'] += file_size_bytes
            
            if read_time > 0:
                speed_mbps = (file_size_bytes / (1024 * 1024)) / read_time
                self.performance_stats['avg_read_speed_mbps'] = (
                    (self.performance_stats['avg_read_speed_mbps'] * (self.performance_stats['files_read'] - 1) + speed_mbps) /
                    self.performance_stats['files_read']
                )
            
            logger.info(f"Read file: {file_path} ({file_size_mb:.1f}MB) in {read_time:.2f}s")
            return project_data
            
        except Exception as e:
            self.performance_stats['read_errors'] += 1
            logger.error(f"Failed to read file {file_path}: {e}")
            raise
    
    async def write_file(self, project_data: ProjectData, file_path: Union[str, Path], 
                        format_hint: Optional[str] = None, **options) -> None:
        """
        Write project data to file
        
        Args:
            project_data: Project data to write
            file_path: Output file path
            format_hint: Optional format hint
            **options: Format-specific options
        """
        file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Detect format
        format_ext = format_hint or file_path.suffix.lower()
        
        if format_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {format_ext}")
        
        if not self.format_capabilities[format_ext]['write']:
            raise ValueError(f"Writing not supported for format: {format_ext}")
        
        try:
            # Get handler for format
            handler = self.supported_formats[format_ext]
            
            # Write file
            start_time = asyncio.get_event_loop().time()
            await handler(file_path, 'write', project_data, **options)
            end_time = asyncio.get_event_loop().time()
            
            # Update stats
            write_time = end_time - start_time
            file_size_bytes = file_path.stat().st_size if file_path.exists() else 0
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            self.performance_stats['files_written'] += 1
            self.performance_stats['bytes_written'] += file_size_bytes
            
            if write_time > 0:
                speed_mbps = file_size_mb / write_time
                self.performance_stats['avg_write_speed_mbps'] = (
                    (self.performance_stats['avg_write_speed_mbps'] * (self.performance_stats['files_written'] - 1) + speed_mbps) /
                    self.performance_stats['files_written']
                )
            
            logger.info(f"Wrote file: {file_path} ({file_size_mb:.1f}MB) in {write_time:.2f}s")
            
        except Exception as e:
            self.performance_stats['write_errors'] += 1
            logger.error(f"Failed to write file {file_path}: {e}")
            raise
    
    # Format handlers
    
    async def _handle_p3d_format(self, file_path: Path, operation: str, 
                                project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle native .p3d format"""
        if operation == 'read':
            return await self._read_p3d_file(file_path)
        elif operation == 'write':
            await self._write_p3d_file(file_path, project_data, **options)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _read_p3d_file(self, file_path: Path) -> ProjectData:
        """Read native .p3d file"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Read metadata
                metadata_json = zip_file.read('metadata.json').decode('utf-8')
                metadata_dict = json.loads(metadata_json)
                
                # Read project data
                project_json = zip_file.read('project.json').decode('utf-8')
                project_dict = json.loads(project_json)
                
                # Read layers
                layers = []
                for layer_info in project_dict.get('layers', []):
                    layer_data_file = f"layers/{layer_info['id']}.dat"
                    if layer_data_file in zip_file.namelist():
                        layer_data = zip_file.read(layer_data_file)
                        
                        layer = LayerData(
                            id=layer_info['id'],
                            name=layer_info['name'],
                            opacity=layer_info['opacity'],
                            blend_mode=layer_info['blend_mode'],
                            visible=layer_info['visible'],
                            locked=layer_info['locked'],
                            data=layer_data,
                            width=layer_info['width'],
                            height=layer_info['height'],
                            format=layer_info['format'],
                            position=tuple(layer_info.get('position', [0, 0])),
                            rotation=layer_info.get('rotation', 0.0),
                            scale=tuple(layer_info.get('scale', [1.0, 1.0]))
                        )
                        layers.append(layer)
                
                # Read brush strokes
                brush_strokes = []
                for stroke_info in project_dict.get('brush_strokes', []):
                    stroke = BrushStrokeData(
                        id=stroke_info['id'],
                        layer_id=stroke_info['layer_id'],
                        brush_type=stroke_info['brush_type'],
                        points=stroke_info['points'],
                        settings=stroke_info['settings'],
                        timestamp=stroke_info['timestamp']
                    )
                    brush_strokes.append(stroke)
                
                # Create metadata
                metadata = FileMetadata(
                    filename=metadata_dict['filename'],
                    size_bytes=metadata_dict['size_bytes'],
                    format=metadata_dict['format'],
                    version=metadata_dict['version'],
                    created_at=datetime.fromisoformat(metadata_dict['created_at']),
                    modified_at=datetime.fromisoformat(metadata_dict['modified_at']),
                    checksum=metadata_dict['checksum'],
                    compression=metadata_dict.get('compression'),
                    custom_data=metadata_dict.get('custom_data')
                )
                
                # Create project data
                project_data = ProjectData(
                    metadata=metadata,
                    canvas_settings=project_dict.get('canvas_settings', {}),
                    layers=layers,
                    brush_strokes=brush_strokes,
                    camera_settings=project_dict.get('camera_settings', {}),
                    lighting_settings=project_dict.get('lighting_settings', {}),
                    custom_data=project_dict.get('custom_data')
                )
                
                return project_data
                
        except Exception as e:
            logger.error(f"Failed to read P3D file: {e}")
            raise
    
    async def _write_p3d_file(self, file_path: Path, project_data: ProjectData, 
                             compression_level: int = 6) -> None:
        """Write native .p3d file"""
        try:
            # Create temporary file
            temp_file = self.temp_dir / f"temp_{file_path.name}"
            
            with zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED, 
                               compresslevel=compression_level) as zip_file:
                
                # Prepare metadata
                metadata_dict = asdict(project_data.metadata)
                metadata_dict['created_at'] = project_data.metadata.created_at.isoformat()
                metadata_dict['modified_at'] = project_data.metadata.modified_at.isoformat()
                
                # Write metadata
                zip_file.writestr('metadata.json', json.dumps(metadata_dict, indent=2))
                
                # Prepare project data
                project_dict = {
                    'canvas_settings': project_data.canvas_settings,
                    'camera_settings': project_data.camera_settings,
                    'lighting_settings': project_data.lighting_settings,
                    'custom_data': project_data.custom_data,
                    'layers': [],
                    'brush_strokes': []
                }
                
                # Add layer info and write layer data
                for layer in project_data.layers:
                    layer_info = {
                        'id': layer.id,
                        'name': layer.name,
                        'opacity': layer.opacity,
                        'blend_mode': layer.blend_mode,
                        'visible': layer.visible,
                        'locked': layer.locked,
                        'width': layer.width,
                        'height': layer.height,
                        'format': layer.format,
                        'position': list(layer.position),
                        'rotation': layer.rotation,
                        'scale': list(layer.scale)
                    }
                    project_dict['layers'].append(layer_info)
                    
                    # Write layer data
                    layer_data_file = f"layers/{layer.id}.dat"
                    zip_file.writestr(layer_data_file, layer.data)
                
                # Add brush stroke data
                for stroke in project_data.brush_strokes:
                    stroke_info = asdict(stroke)
                    project_dict['brush_strokes'].append(stroke_info)
                
                # Write project data
                zip_file.writestr('project.json', json.dumps(project_dict, indent=2))
            
            # Move temporary file to final location
            shutil.move(temp_file, file_path)
            
        except Exception as e:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
            logger.error(f"Failed to write P3D file: {e}")
            raise
    
    async def _handle_png_format(self, file_path: Path, operation: str, 
                                project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle PNG format"""
        if operation == 'read':
            return await self._read_image_file(file_path, 'png')
        elif operation == 'write':
            await self._write_image_file(file_path, project_data, 'png', **options)
    
    async def _handle_jpg_format(self, file_path: Path, operation: str, 
                                project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle JPG/JPEG format"""
        if operation == 'read':
            return await self._read_image_file(file_path, 'jpg')
        elif operation == 'write':
            await self._write_image_file(file_path, project_data, 'jpg', **options)
    
    async def _handle_bmp_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle BMP format"""
        if operation == 'read':
            return await self._read_image_file(file_path, 'bmp')
        elif operation == 'write':
            await self._write_image_file(file_path, project_data, 'bmp', **options)
    
    async def _handle_tiff_format(self, file_path: Path, operation: str, 
                                 project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle TIFF format"""
        if operation == 'read':
            return await self._read_image_file(file_path, 'tiff')
        elif operation == 'write':
            await self._write_image_file(file_path, project_data, 'tiff', **options)
    
    async def _handle_webp_format(self, file_path: Path, operation: str, 
                                 project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle WebP format"""
        if operation == 'read':
            return await self._read_image_file(file_path, 'webp')
        elif operation == 'write':
            await self._write_image_file(file_path, project_data, 'webp', **options)
    
    async def _read_image_file(self, file_path: Path, format_type: str) -> ProjectData:
        """Read standard image file"""
        try:
            # Use image processor to load image
            from .image_processor import get_image_processor
            image_processor = await get_image_processor()
            
            image_data, metadata = image_processor.load_image_from_path(file_path)
            
            # Create single layer with image data
            layer = LayerData(
                id="layer_0",
                name="Background",
                opacity=1.0,
                blend_mode="normal",
                visible=True,
                locked=False,
                data=image_data.tobytes(),
                width=metadata.width,
                height=metadata.height,
                format=format_type
            )
            
            # Create file metadata
            file_metadata = FileMetadata(
                filename=file_path.name,
                size_bytes=file_path.stat().st_size,
                format=format_type,
                version="1.0",
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                modified_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                checksum=self._calculate_file_checksum(file_path)
            )
            
            # Create project data
            project_data = ProjectData(
                metadata=file_metadata,
                canvas_settings={
                    'width': metadata.width,
                    'height': metadata.height,
                    'background_color': [255, 255, 255, 255]
                },
                layers=[layer],
                brush_strokes=[],
                camera_settings={},
                lighting_settings={}
            )
            
            return project_data
            
        except Exception as e:
            logger.error(f"Failed to read image file: {e}")
            raise
    
    async def _write_image_file(self, file_path: Path, project_data: ProjectData, 
                               format_type: str, quality: int = 95, **options) -> None:
        """Write standard image file"""
        try:
            if not project_data.layers:
                raise ValueError("No layers to export")
            
            # Flatten all visible layers into single image
            # This is a simplified implementation - real implementation would be more complex
            main_layer = project_data.layers[0]
            
            # Convert layer data back to numpy array
            import numpy as np
            image_data = np.frombuffer(main_layer.data, dtype=np.uint8)
            image_data = image_data.reshape((main_layer.height, main_layer.width, -1))
            
            # Use image processor to save image
            from .image_processor import get_image_processor
            image_processor = await get_image_processor()
            
            image_processor.save_image_to_path(image_data, file_path, quality=quality)
            
        except Exception as e:
            logger.error(f"Failed to write image file: {e}")
            raise
    
    async def _handle_psd_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle PSD format (read-only)"""
        if operation == 'read':
            return await self._read_psd_file(file_path)
        else:
            raise ValueError("PSD writing not supported")
    
    async def _read_psd_file(self, file_path: Path) -> ProjectData:
        """Read PSD file (simplified implementation)"""
        # This would require a PSD parsing library like psd-tools
        # For now, return a placeholder
        raise NotImplementedError("PSD reading not yet implemented")
    
    async def _handle_psb_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle PSB format (read-only)"""
        if operation == 'read':
            return await self._read_psb_file(file_path)
        else:
            raise ValueError("PSB writing not supported")
    
    async def _read_psb_file(self, file_path: Path) -> ProjectData:
        """Read PSB file (simplified implementation)"""
        raise NotImplementedError("PSB reading not yet implemented")
    
    async def _handle_obj_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle OBJ 3D format"""
        if operation == 'read':
            return await self._read_obj_file(file_path)
        elif operation == 'write':
            await self._write_obj_file(file_path, project_data, **options)
    
    async def _read_obj_file(self, file_path: Path) -> ProjectData:
        """Read OBJ 3D file"""
        # OBJ reading implementation would go here
        raise NotImplementedError("OBJ reading not yet implemented")
    
    async def _write_obj_file(self, file_path: Path, project_data: ProjectData, **options) -> None:
        """Write OBJ 3D file"""
        # OBJ writing implementation would go here
        raise NotImplementedError("OBJ writing not yet implemented")
    
    async def _handle_ply_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle PLY 3D format"""
        raise NotImplementedError("PLY format not yet implemented")
    
    async def _handle_stl_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle STL 3D format"""
        raise NotImplementedError("STL format not yet implemented")
    
    async def _handle_svg_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle SVG vector format"""
        raise NotImplementedError("SVG format not yet implemented")
    
    async def _handle_zip_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle ZIP archive format"""
        if operation == 'read':
            return await self._read_zip_file(file_path)
        elif operation == 'write':
            await self._write_zip_file(file_path, project_data, **options)
    
    async def _read_zip_file(self, file_path: Path) -> ProjectData:
        """Read ZIP archive"""
        # Check if it contains a P3D project
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                if 'project.json' in zip_file.namelist():
                    # It's a P3D file
                    return await self._read_p3d_file(file_path)
        except Exception as e:
            logger.warning(f"ZIP file is not a P3D project: {e}")
        
        raise NotImplementedError("Generic ZIP reading not yet implemented")
    
    async def _write_zip_file(self, file_path: Path, project_data: ProjectData, **options) -> None:
        """Write ZIP archive"""
        # For now, write as P3D format
        await self._write_p3d_file(file_path, project_data, **options)
    
    async def _handle_tar_format(self, file_path: Path, operation: str, 
                               project_data: Optional[ProjectData] = None, **options) -> Optional[ProjectData]:
        """Handle TAR archive format"""
        raise NotImplementedError("TAR format not yet implemented")
    
    # Utility methods
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def get_supported_formats(self) -> Dict[str, Dict]:
        """Get supported file formats and their capabilities"""
        return dict(self.format_capabilities)
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return dict(self.performance_stats)
    
    def clear_temp_files(self) -> int:
        """Clear temporary files"""
        count = 0
        
        try:
            for temp_file in self.temp_dir.glob("temp_*"):
                temp_file.unlink()
                count += 1
        except Exception as e:
            logger.warning(f"Failed to clear some temp files: {e}")
        
        logger.info(f"Cleared {count} temporary files")
        return count
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.clear_temp_files()
        except:
            pass


# Global file manager instance
_file_manager = None

def get_file_manager() -> FileManager:
    """Get the global file manager instance"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager

def initialize_file_manager(temp_dir: Optional[Path] = None, 
                          max_file_size_mb: int = 1024) -> FileManager:
    """Initialize the global file manager"""
    global _file_manager
    _file_manager = FileManager(temp_dir=temp_dir, max_file_size_mb=max_file_size_mb)
    return _file_manager