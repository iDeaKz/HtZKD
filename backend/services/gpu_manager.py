"""
GPU Manager for 3D Paint Application
Provides GPU memory management and monitoring capabilities
"""

import logging
import psutil
import threading
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from collections import deque

# Setup logger
logger = logging.getLogger(__name__)

@dataclass
class GPUMemoryInfo:
    """GPU memory information structure"""
    total: int = 0
    used: int = 0
    free: int = 0
    utilization: float = 0.0
    temperature: float = 0.0
    power_usage: float = 0.0

@dataclass
class BufferInfo:
    """GPU buffer information"""
    id: str
    size: int
    type: str
    usage: str
    last_accessed: float
    reference_count: int

class GPUManager:
    """
    Advanced GPU resource management with monitoring and optimization
    """
    
    def __init__(self, max_memory_mb: int = 1024, monitoring_interval: float = 1.0):
        self.max_memory_mb = max_memory_mb
        self.monitoring_interval = monitoring_interval
        
        # Memory tracking
        self.allocated_memory = 0
        self.memory_pools = {}
        self.buffer_registry = {}
        self.texture_registry = {}
        
        # Performance monitoring
        self.memory_history = deque(maxlen=100)
        self.allocation_history = deque(maxlen=1000)
        self.performance_stats = {
            'allocations': 0,
            'deallocations': 0,
            'memory_pressure_events': 0,
            'gc_cycles': 0,
            'optimization_runs': 0
        }
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        self._lock = threading.RLock()
        
        # Cleanup policies
        self.auto_cleanup_enabled = True
        self.cleanup_threshold = 0.8  # 80% memory usage triggers cleanup
        self.buffer_timeout = 300.0  # 5 minutes buffer timeout
        
        # GPU detection
        self.gpu_info = self._detect_gpu()
        
        logger.info(f"GPU Manager initialized with max memory: {max_memory_mb}MB")
        
    def _detect_gpu(self) -> Dict:
        """Detect available GPU information"""
        gpu_info = {
            'vendor': 'Unknown',
            'model': 'Unknown',
            'memory_total': 0,
            'driver_version': 'Unknown',
            'compute_capability': 'Unknown'
        }
        
        try:
            # Try to detect NVIDIA GPU
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            gpu_info['vendor'] = 'NVIDIA'
            gpu_info['model'] = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info['memory_total'] = memory_info.total // (1024 * 1024)  # Convert to MB
            
            driver_version = pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
            gpu_info['driver_version'] = driver_version
            
            major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
            gpu_info['compute_capability'] = f"{major}.{minor}"
            
        except ImportError:
            logger.warning("pynvml not available, NVIDIA GPU detection disabled")
        except Exception as e:
            logger.warning(f"Failed to detect NVIDIA GPU: {e}")
            
        try:
            # Try to detect AMD GPU using alternative methods
            pass  # AMD GPU detection would go here
        except Exception as e:
            logger.warning(f"Failed to detect AMD GPU: {e}")
            
        logger.info(f"Detected GPU: {gpu_info}")
        return gpu_info
    
    def start_monitoring(self) -> None:
        """Start GPU monitoring thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("GPU monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop GPU monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("GPU monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._update_memory_stats()
                self._check_memory_pressure()
                self._cleanup_expired_buffers()
                
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _update_memory_stats(self) -> None:
        """Update memory statistics"""
        memory_info = self.get_memory_info()
        
        with self._lock:
            self.memory_history.append({
                'timestamp': time.time(),
                'used': memory_info.used,
                'utilization': memory_info.utilization,
                'temperature': memory_info.temperature
            })
    
    def _check_memory_pressure(self) -> None:
        """Check for memory pressure and trigger cleanup if needed"""
        memory_info = self.get_memory_info()
        
        if memory_info.utilization > self.cleanup_threshold:
            logger.warning(f"Memory pressure detected: {memory_info.utilization:.1%}")
            
            with self._lock:
                self.performance_stats['memory_pressure_events'] += 1
            
            if self.auto_cleanup_enabled:
                self.cleanup_unused_resources()
    
    def _cleanup_expired_buffers(self) -> None:
        """Clean up expired buffers"""
        current_time = time.time()
        expired_buffers = []
        
        with self._lock:
            for buffer_id, buffer_info in self.buffer_registry.items():
                if (current_time - buffer_info.last_accessed) > self.buffer_timeout:
                    if buffer_info.reference_count == 0:
                        expired_buffers.append(buffer_id)
        
        for buffer_id in expired_buffers:
            self.deallocate_buffer(buffer_id)
            logger.debug(f"Cleaned up expired buffer: {buffer_id}")
    
    def get_memory_info(self) -> GPUMemoryInfo:
        """Get current GPU memory information"""
        memory_info = GPUMemoryInfo()
        
        try:
            # Try to get NVIDIA GPU memory info
            import pynvml
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            gpu_memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_info.total = gpu_memory.total // (1024 * 1024)  # Convert to MB
            memory_info.used = gpu_memory.used // (1024 * 1024)
            memory_info.free = gpu_memory.free // (1024 * 1024)
            memory_info.utilization = memory_info.used / memory_info.total
            
            try:
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                memory_info.temperature = float(temperature)
            except:
                pass
                
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                memory_info.power_usage = power_usage
            except:
                pass
                
        except (ImportError, Exception) as e:
            # Fallback to system memory if GPU memory not available
            system_memory = psutil.virtual_memory()
            memory_info.total = self.max_memory_mb
            memory_info.used = self.allocated_memory
            memory_info.free = self.max_memory_mb - self.allocated_memory
            memory_info.utilization = self.allocated_memory / self.max_memory_mb
        
        return memory_info
    
    def allocate_buffer(self, size_mb: int, buffer_type: str = 'vertex', 
                       usage: str = 'static') -> Optional[str]:
        """
        Allocate GPU buffer
        
        Args:
            size_mb: Size in megabytes
            buffer_type: Type of buffer (vertex, index, texture, etc.)
            usage: Usage pattern (static, dynamic, stream)
            
        Returns:
            Buffer ID or None if allocation failed
        """
        try:
            # Check if allocation would exceed limits
            if self.allocated_memory + size_mb > self.max_memory_mb:
                logger.warning(f"Buffer allocation would exceed memory limit: {size_mb}MB")
                
                if self.auto_cleanup_enabled:
                    self.cleanup_unused_resources()
                    
                    # Try again after cleanup
                    if self.allocated_memory + size_mb > self.max_memory_mb:
                        logger.error(f"Failed to allocate buffer after cleanup: {size_mb}MB")
                        return None
                else:
                    return None
            
            # Generate buffer ID
            buffer_id = f"{buffer_type}_{int(time.time() * 1000000)}"
            
            # Create buffer info
            buffer_info = BufferInfo(
                id=buffer_id,
                size=size_mb * 1024 * 1024,  # Convert to bytes
                type=buffer_type,
                usage=usage,
                last_accessed=time.time(),
                reference_count=1
            )
            
            with self._lock:
                self.buffer_registry[buffer_id] = buffer_info
                self.allocated_memory += size_mb
                self.performance_stats['allocations'] += 1
                
                self.allocation_history.append({
                    'timestamp': time.time(),
                    'action': 'allocate',
                    'buffer_id': buffer_id,
                    'size': size_mb,
                    'type': buffer_type
                })
            
            logger.debug(f"Allocated {buffer_type} buffer: {buffer_id} ({size_mb}MB)")
            return buffer_id
            
        except Exception as e:
            logger.error(f"Failed to allocate buffer: {e}")
            return None
    
    def deallocate_buffer(self, buffer_id: str) -> bool:
        """
        Deallocate GPU buffer
        
        Args:
            buffer_id: Buffer ID to deallocate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if buffer_id not in self.buffer_registry:
                    logger.warning(f"Buffer not found for deallocation: {buffer_id}")
                    return False
                
                buffer_info = self.buffer_registry[buffer_id]
                size_mb = buffer_info.size // (1024 * 1024)
                
                del self.buffer_registry[buffer_id]
                self.allocated_memory -= size_mb
                self.performance_stats['deallocations'] += 1
                
                self.allocation_history.append({
                    'timestamp': time.time(),
                    'action': 'deallocate',
                    'buffer_id': buffer_id,
                    'size': size_mb,
                    'type': buffer_info.type
                })
            
            logger.debug(f"Deallocated buffer: {buffer_id} ({size_mb}MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deallocate buffer: {e}")
            return False
    
    def reference_buffer(self, buffer_id: str) -> bool:
        """Increment buffer reference count"""
        with self._lock:
            if buffer_id in self.buffer_registry:
                self.buffer_registry[buffer_id].reference_count += 1
                self.buffer_registry[buffer_id].last_accessed = time.time()
                return True
            return False
    
    def dereference_buffer(self, buffer_id: str) -> bool:
        """Decrement buffer reference count"""
        with self._lock:
            if buffer_id in self.buffer_registry:
                self.buffer_registry[buffer_id].reference_count -= 1
                return True
            return False
    
    def cleanup_unused_resources(self) -> int:
        """
        Clean up unused GPU resources
        
        Returns:
            Number of resources cleaned up
        """
        cleaned_count = 0
        
        with self._lock:
            # Find buffers with zero references
            buffers_to_remove = []
            for buffer_id, buffer_info in self.buffer_registry.items():
                if buffer_info.reference_count <= 0:
                    buffers_to_remove.append(buffer_id)
        
        # Remove unreferenced buffers
        for buffer_id in buffers_to_remove:
            if self.deallocate_buffer(buffer_id):
                cleaned_count += 1
        
        with self._lock:
            self.performance_stats['gc_cycles'] += 1
        
        logger.info(f"Cleaned up {cleaned_count} unused resources")
        return cleaned_count
    
    def optimize_memory_layout(self) -> None:
        """Optimize GPU memory layout for better performance"""
        logger.info("Starting memory layout optimization...")
        
        try:
            with self._lock:
                # Sort buffers by usage pattern and size
                buffers = list(self.buffer_registry.values())
                buffers.sort(key=lambda b: (b.usage, -b.size))
                
                # Implement memory defragmentation logic here
                # This is a simplified version - real implementation would be more complex
                
                self.performance_stats['optimization_runs'] += 1
            
            logger.info("Memory layout optimization completed")
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        memory_info = self.get_memory_info()
        
        with self._lock:
            stats = {
                'memory': {
                    'total_mb': memory_info.total,
                    'used_mb': memory_info.used,
                    'free_mb': memory_info.free,
                    'utilization': memory_info.utilization,
                    'temperature': memory_info.temperature,
                    'power_usage': memory_info.power_usage
                },
                'buffers': {
                    'count': len(self.buffer_registry),
                    'total_size_mb': self.allocated_memory,
                    'by_type': {}
                },
                'performance': dict(self.performance_stats),
                'gpu_info': self.gpu_info
            }
            
            # Calculate buffer statistics by type
            for buffer_info in self.buffer_registry.values():
                buffer_type = buffer_info.type
                if buffer_type not in stats['buffers']['by_type']:
                    stats['buffers']['by_type'][buffer_type] = {
                        'count': 0,
                        'size_mb': 0
                    }
                
                stats['buffers']['by_type'][buffer_type]['count'] += 1
                stats['buffers']['by_type'][buffer_type]['size_mb'] += buffer_info.size // (1024 * 1024)
        
        return stats
    
    def get_memory_timeline(self, minutes: int = 10) -> List[Dict]:
        """Get memory usage timeline for the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        
        with self._lock:
            timeline = [
                entry for entry in self.memory_history 
                if entry['timestamp'] > cutoff_time
            ]
        
        return timeline
    
    def set_memory_limit(self, max_memory_mb: int) -> None:
        """Set maximum memory limit"""
        with self._lock:
            old_limit = self.max_memory_mb
            self.max_memory_mb = max_memory_mb
        
        logger.info(f"Memory limit changed from {old_limit}MB to {max_memory_mb}MB")
        
        # Trigger cleanup if current usage exceeds new limit
        if self.allocated_memory > max_memory_mb:
            self.cleanup_unused_resources()
    
    def enable_auto_cleanup(self, enabled: bool, threshold: float = 0.8) -> None:
        """Enable/disable automatic cleanup"""
        self.auto_cleanup_enabled = enabled
        self.cleanup_threshold = threshold
        
        logger.info(f"Auto cleanup {'enabled' if enabled else 'disabled'} with threshold {threshold:.1%}")
    
    def force_garbage_collection(self) -> int:
        """Force immediate garbage collection"""
        logger.info("Forcing garbage collection...")
        
        # Clean up unused resources
        cleaned_count = self.cleanup_unused_resources()
        
        # Optimize memory layout
        self.optimize_memory_layout()
        
        return cleaned_count
    
    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()
        self.cleanup_unused_resources()


# Global GPU manager instance
_gpu_manager = None

def get_gpu_manager() -> GPUManager:
    """Get the global GPU manager instance"""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
        _gpu_manager.start_monitoring()
    return _gpu_manager

def initialize_gpu_manager(max_memory_mb: int = 1024) -> GPUManager:
    """Initialize the global GPU manager"""
    global _gpu_manager
    if _gpu_manager is not None:
        _gpu_manager.stop_monitoring()
    
    _gpu_manager = GPUManager(max_memory_mb=max_memory_mb)
    _gpu_manager.start_monitoring()
    return _gpu_manager