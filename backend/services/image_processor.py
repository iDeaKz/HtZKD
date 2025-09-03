"""
Image Processor for 3D Paint Application
Provides advanced image processing capabilities with OpenCV and PIL
"""

import logging
import numpy as np
import asyncio
import threading
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import tempfile
import time

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available, some features will be disabled")

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available, some features will be disabled")

# Setup logger
logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    """Image metadata structure"""
    width: int
    height: int
    channels: int
    format: str
    size_bytes: int
    dpi: Tuple[int, int] = (72, 72)
    color_space: str = 'RGB'
    has_alpha: bool = False

@dataclass
class ProcessingTask:
    """Image processing task structure"""
    task_id: str
    operation: str
    parameters: Dict[str, Any]
    input_data: np.ndarray
    output_data: Optional[np.ndarray] = None
    status: str = 'pending'  # pending, processing, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None

class ImageProcessor:
    """
    Advanced image processing engine with GPU acceleration support
    """
    
    def __init__(self, max_workers: int = 4, cache_size_mb: int = 256):
        self.max_workers = max_workers
        self.cache_size_mb = cache_size_mb
        
        # Processing state
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.completed_tasks = {}
        self.processing_workers = []
        
        # Performance tracking
        self.performance_stats = {
            'tasks_processed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'memory_usage_mb': 0
        }
        
        # Image cache
        self.image_cache = {}
        self.cache_usage_mb = 0
        
        # Threading
        self._lock = threading.RLock()
        self.workers_active = False
        
        # Supported formats
        self.supported_input_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
        self.supported_output_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        
        # OpenCV initialization
        if OPENCV_AVAILABLE:
            self._init_opencv()
        
        logger.info(f"Image Processor initialized with {max_workers} workers")
    
    def _init_opencv(self):
        """Initialize OpenCV with optimizations"""
        try:
            # Enable OpenCV optimizations
            cv2.setUseOptimized(True)
            cv2.setNumThreads(self.max_workers)
            
            # Check for GPU support
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                logger.info(f"CUDA devices available: {cv2.cuda.getCudaEnabledDeviceCount()}")
                self.gpu_available = True
            else:
                self.gpu_available = False
                
        except Exception as e:
            logger.warning(f"OpenCV GPU initialization failed: {e}")
            self.gpu_available = False
    
    async def start_workers(self):
        """Start processing workers"""
        if self.workers_active:
            return
        
        self.workers_active = True
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker_{i}"))
            self.processing_workers.append(worker)
        
        logger.info(f"Started {self.max_workers} processing workers")
    
    async def stop_workers(self):
        """Stop processing workers"""
        self.workers_active = False
        
        # Cancel all workers
        for worker in self.processing_workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.processing_workers, return_exceptions=True)
        
        self.processing_workers.clear()
        logger.info("Stopped all processing workers")
    
    async def _worker_loop(self, worker_id: str):
        """Main worker processing loop"""
        logger.debug(f"Worker {worker_id} started")
        
        try:
            while self.workers_active:
                try:
                    # Get task from queue
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                    
                    # Process task
                    await self._process_task(task)
                    
                    # Mark task as done
                    self.task_queue.task_done()
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                    
        except asyncio.CancelledError:
            logger.debug(f"Worker {worker_id} cancelled")
        except Exception as e:
            logger.error(f"Worker {worker_id} fatal error: {e}")
    
    async def _process_task(self, task: ProcessingTask):
        """Process a single image processing task"""
        task.status = 'processing'
        task.start_time = time.time()
        
        try:
            # Route to appropriate processing function
            if task.operation == 'resize':
                result = await self._resize_image(task.input_data, **task.parameters)
            elif task.operation == 'rotate':
                result = await self._rotate_image(task.input_data, **task.parameters)
            elif task.operation == 'blur':
                result = await self._blur_image(task.input_data, **task.parameters)
            elif task.operation == 'sharpen':
                result = await self._sharpen_image(task.input_data, **task.parameters)
            elif task.operation == 'color_adjust':
                result = await self._adjust_colors(task.input_data, **task.parameters)
            elif task.operation == 'filter':
                result = await self._apply_filter(task.input_data, **task.parameters)
            elif task.operation == 'composite':
                result = await self._composite_images(task.input_data, **task.parameters)
            elif task.operation == 'extract_features':
                result = await self._extract_features(task.input_data, **task.parameters)
            else:
                raise ValueError(f"Unknown operation: {task.operation}")
            
            task.output_data = result
            task.status = 'completed'
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
        
        finally:
            task.end_time = time.time()
            
            with self._lock:
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]
                self.completed_tasks[task.task_id] = task
                
                # Update performance stats
                self.performance_stats['tasks_processed'] += 1
                processing_time = task.end_time - task.start_time
                self.performance_stats['total_processing_time'] += processing_time
                self.performance_stats['average_processing_time'] = (
                    self.performance_stats['total_processing_time'] / 
                    self.performance_stats['tasks_processed']
                )
    
    async def process_image_async(self, image_data: np.ndarray, operation: str, 
                                **parameters) -> str:
        """
        Process image asynchronously
        
        Args:
            image_data: Input image as numpy array
            operation: Processing operation name
            **parameters: Operation parameters
            
        Returns:
            Task ID for tracking
        """
        task_id = f"task_{int(time.time() * 1000000)}"
        
        task = ProcessingTask(
            task_id=task_id,
            operation=operation,
            parameters=parameters,
            input_data=image_data.copy()
        )
        
        with self._lock:
            self.active_tasks[task_id] = task
        
        await self.task_queue.put(task)
        
        logger.debug(f"Queued task {task_id}: {operation}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    'id': task.task_id,
                    'operation': task.operation,
                    'status': task.status,
                    'start_time': task.start_time
                }
            elif task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                return {
                    'id': task.task_id,
                    'operation': task.operation,
                    'status': task.status,
                    'start_time': task.start_time,
                    'end_time': task.end_time,
                    'processing_time': task.end_time - task.start_time if task.start_time else None,
                    'error_message': task.error_message
                }
        
        return None
    
    def get_task_result(self, task_id: str) -> Optional[np.ndarray]:
        """Get task result"""
        with self._lock:
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                if task.status == 'completed':
                    return task.output_data
        
        return None
    
    # Image processing operations
    
    async def _resize_image(self, image: np.ndarray, width: int, height: int, 
                          interpolation: str = 'linear') -> np.ndarray:
        """Resize image"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for resize operation")
        
        # Map interpolation methods
        interp_map = {
            'nearest': cv2.INTER_NEAREST,
            'linear': cv2.INTER_LINEAR,
            'cubic': cv2.INTER_CUBIC,
            'lanczos': cv2.INTER_LANCZOS4
        }
        
        interp_method = interp_map.get(interpolation, cv2.INTER_LINEAR)
        
        # Resize image
        resized = cv2.resize(image, (width, height), interpolation=interp_method)
        
        return resized
    
    async def _rotate_image(self, image: np.ndarray, angle: float, 
                          expand: bool = True) -> np.ndarray:
        """Rotate image"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for rotate operation")
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        if expand:
            # Calculate new image dimensions
            cos_val = abs(rotation_matrix[0, 0])
            sin_val = abs(rotation_matrix[0, 1])
            new_width = int((height * sin_val) + (width * cos_val))
            new_height = int((height * cos_val) + (width * sin_val))
            
            # Adjust translation
            rotation_matrix[0, 2] += (new_width - width) / 2
            rotation_matrix[1, 2] += (new_height - height) / 2
            
            # Rotate image
            rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height))
        else:
            rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
        
        return rotated
    
    async def _blur_image(self, image: np.ndarray, blur_type: str = 'gaussian', 
                        **parameters) -> np.ndarray:
        """Apply blur to image"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for blur operation")
        
        if blur_type == 'gaussian':
            kernel_size = parameters.get('kernel_size', 15)
            sigma_x = parameters.get('sigma_x', 0)
            sigma_y = parameters.get('sigma_y', 0)
            
            # Ensure kernel size is odd
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x, sigmaY=sigma_y)
            
        elif blur_type == 'median':
            kernel_size = parameters.get('kernel_size', 5)
            if kernel_size % 2 == 0:
                kernel_size += 1
            blurred = cv2.medianBlur(image, kernel_size)
            
        elif blur_type == 'bilateral':
            d = parameters.get('d', 9)
            sigma_color = parameters.get('sigma_color', 75)
            sigma_space = parameters.get('sigma_space', 75)
            blurred = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
            
        else:
            raise ValueError(f"Unknown blur type: {blur_type}")
        
        return blurred
    
    async def _sharpen_image(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """Sharpen image"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for sharpen operation")
        
        # Create sharpening kernel
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ]) * strength
        
        # Apply filter
        sharpened = cv2.filter2D(image, -1, kernel)
        
        return sharpened
    
    async def _adjust_colors(self, image: np.ndarray, brightness: float = 0, 
                           contrast: float = 1.0, saturation: float = 1.0, 
                           hue: float = 0) -> np.ndarray:
        """Adjust image colors"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for color adjustment")
        
        # Convert to float for processing
        img_float = image.astype(np.float32) / 255.0
        
        # Adjust brightness and contrast
        img_float = img_float * contrast + brightness
        
        # Convert to HSV for saturation and hue adjustment
        if len(image.shape) == 3 and image.shape[2] == 3:
            hsv = cv2.cvtColor(img_float, cv2.COLOR_RGB2HSV)
            
            # Adjust hue
            hsv[:, :, 0] = (hsv[:, :, 0] + hue) % 180
            
            # Adjust saturation
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 1)
            
            # Convert back to RGB
            img_float = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        # Clamp values and convert back to uint8
        img_float = np.clip(img_float, 0, 1)
        adjusted = (img_float * 255).astype(np.uint8)
        
        return adjusted
    
    async def _apply_filter(self, image: np.ndarray, filter_type: str, 
                          **parameters) -> np.ndarray:
        """Apply various filters to image"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for filter operation")
        
        if filter_type == 'edge_detect':
            # Sobel edge detection
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(sobel_x**2 + sobel_y**2)
            edges = np.clip(edges, 0, 255).astype(np.uint8)
            
            # Convert back to color if needed
            if len(image.shape) == 3:
                edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            
            return edges
            
        elif filter_type == 'emboss':
            kernel = np.array([
                [-2, -1,  0],
                [-1,  1,  1],
                [ 0,  1,  2]
            ])
            embossed = cv2.filter2D(image, -1, kernel)
            return embossed
            
        elif filter_type == 'noise_reduction':
            # Non-local means denoising
            if len(image.shape) == 3:
                denoised = cv2.fastNlMeansDenoisingColored(image)
            else:
                denoised = cv2.fastNlMeansDenoising(image)
            return denoised
            
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
    
    async def _composite_images(self, base_image: np.ndarray, overlay_image: np.ndarray, 
                              blend_mode: str = 'normal', opacity: float = 1.0, 
                              x: int = 0, y: int = 0) -> np.ndarray:
        """Composite two images"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for composite operation")
        
        # Ensure images have the same number of channels
        if len(base_image.shape) != len(overlay_image.shape):
            if len(base_image.shape) == 3 and len(overlay_image.shape) == 2:
                overlay_image = cv2.cvtColor(overlay_image, cv2.COLOR_GRAY2RGB)
            elif len(base_image.shape) == 2 and len(overlay_image.shape) == 3:
                base_image = cv2.cvtColor(base_image, cv2.COLOR_GRAY2RGB)
        
        # Create result image
        result = base_image.copy()
        
        # Calculate overlay region
        h_overlay, w_overlay = overlay_image.shape[:2]
        h_base, w_base = base_image.shape[:2]
        
        x_end = min(x + w_overlay, w_base)
        y_end = min(y + h_overlay, h_base)
        
        if x >= w_base or y >= h_base or x_end <= x or y_end <= y:
            return result  # No overlap
        
        # Extract regions
        overlay_region = overlay_image[0:y_end-y, 0:x_end-x]
        base_region = result[y:y_end, x:x_end]
        
        # Apply blending
        if blend_mode == 'normal':
            blended = cv2.addWeighted(base_region, 1.0 - opacity, overlay_region, opacity, 0)
        elif blend_mode == 'multiply':
            blended = (base_region.astype(np.float32) * overlay_region.astype(np.float32) / 255.0).astype(np.uint8)
            blended = cv2.addWeighted(base_region, 1.0 - opacity, blended, opacity, 0)
        elif blend_mode == 'screen':
            inv_base = 255 - base_region.astype(np.float32)
            inv_overlay = 255 - overlay_region.astype(np.float32)
            blended = 255 - (inv_base * inv_overlay / 255.0)
            blended = blended.astype(np.uint8)
            blended = cv2.addWeighted(base_region, 1.0 - opacity, blended, opacity, 0)
        else:
            blended = cv2.addWeighted(base_region, 1.0 - opacity, overlay_region, opacity, 0)
        
        # Update result
        result[y:y_end, x:x_end] = blended
        
        return result
    
    async def _extract_features(self, image: np.ndarray, feature_type: str = 'corners') -> np.ndarray:
        """Extract image features"""
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV not available for feature extraction")
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        if feature_type == 'corners':
            corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)
            return corners
        elif feature_type == 'edges':
            edges = cv2.Canny(gray, 50, 150)
            return edges
        else:
            raise ValueError(f"Unknown feature type: {feature_type}")
    
    # Utility methods
    
    def load_image_from_path(self, file_path: Union[str, Path]) -> Tuple[np.ndarray, ImageMetadata]:
        """Load image from file path"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        if file_path.suffix.lower() not in self.supported_input_formats:
            raise ValueError(f"Unsupported image format: {file_path.suffix}")
        
        if OPENCV_AVAILABLE:
            # Use OpenCV for loading
            image = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"Failed to load image: {file_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        elif PIL_AVAILABLE:
            # Use PIL for loading
            pil_image = Image.open(file_path)
            image = np.array(pil_image)
            
        else:
            raise RuntimeError("No image loading library available")
        
        # Create metadata
        metadata = ImageMetadata(
            width=image.shape[1],
            height=image.shape[0],
            channels=image.shape[2] if len(image.shape) == 3 else 1,
            format=file_path.suffix.lower(),
            size_bytes=image.nbytes,
            has_alpha=image.shape[2] == 4 if len(image.shape) == 3 else False
        )
        
        return image, metadata
    
    def save_image_to_path(self, image: np.ndarray, file_path: Union[str, Path], 
                          quality: int = 95) -> None:
        """Save image to file path"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() not in self.supported_output_formats:
            raise ValueError(f"Unsupported output format: {file_path.suffix}")
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if OPENCV_AVAILABLE:
            # Convert RGB to BGR for OpenCV
            if len(image.shape) == 3:
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image
            
            # Set quality for JPEG
            if file_path.suffix.lower() in ['.jpg', '.jpeg']:
                cv2.imwrite(str(file_path), image_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(str(file_path), image_bgr)
                
        elif PIL_AVAILABLE:
            pil_image = Image.fromarray(image)
            pil_image.save(file_path, quality=quality)
            
        else:
            raise RuntimeError("No image saving library available")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        with self._lock:
            stats = dict(self.performance_stats)
            stats.update({
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'cache_size_mb': self.cache_usage_mb,
                'cache_efficiency': (
                    self.performance_stats['cache_hits'] / 
                    (self.performance_stats['cache_hits'] + self.performance_stats['cache_misses'])
                    if (self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']) > 0 
                    else 0
                ),
                'workers_active': self.workers_active,
                'opencv_available': OPENCV_AVAILABLE,
                'pil_available': PIL_AVAILABLE,
                'gpu_available': getattr(self, 'gpu_available', False)
            })
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear image cache"""
        with self._lock:
            self.image_cache.clear()
            self.cache_usage_mb = 0
            logger.info("Image cache cleared")
    
    def clear_completed_tasks(self) -> None:
        """Clear completed tasks"""
        with self._lock:
            self.completed_tasks.clear()
            logger.info("Completed tasks cleared")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_workers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_workers()


# Global image processor instance
_image_processor = None

async def get_image_processor() -> ImageProcessor:
    """Get the global image processor instance"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
        await _image_processor.start_workers()
    return _image_processor

async def initialize_image_processor(max_workers: int = 4, cache_size_mb: int = 256) -> ImageProcessor:
    """Initialize the global image processor"""
    global _image_processor
    if _image_processor is not None:
        await _image_processor.stop_workers()
    
    _image_processor = ImageProcessor(max_workers=max_workers, cache_size_mb=cache_size_mb)
    await _image_processor.start_workers()
    return _image_processor