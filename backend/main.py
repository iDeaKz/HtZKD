"""
Main Backend Application for 3D Paint Studio
FastAPI-based REST API server with comprehensive error handling
"""

import logging
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available. Backend API will be disabled.")

# Import services
from backend.services.gpu_manager import initialize_gpu_manager, get_gpu_manager
from backend.services.image_processor import initialize_image_processor, get_image_processor
from backend.services.file_manager import initialize_file_manager, get_file_manager

# Import API routers
if FASTAPI_AVAILABLE:
    from backend.api.canvas_api import get_canvas_router
    from backend.api.file_api import get_file_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Paint3DBackend:
    """Main backend application class"""
    
    def __init__(self):
        self.app = None
        self.services_initialized = False
        self.startup_time = None
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        # Service instances
        self.gpu_manager = None
        self.image_processor = None
        self.file_manager = None
    
    def create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not available")
        
        # Create FastAPI instance
        app = FastAPI(
            title="3D Paint Studio API",
            description="Advanced 3D paint application backend with comprehensive graphics processing",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Add middleware
        self._setup_middleware(app)
        
        # Add event handlers
        app.add_event_handler("startup", self.startup_event)
        app.add_event_handler("shutdown", self.shutdown_event)
        
        # Add exception handlers
        self._setup_exception_handlers(app)
        
        # Include API routers
        self._setup_routes(app)
        
        # Serve static files
        self._setup_static_files(app)
        
        self.app = app
        return app
    
    def _setup_middleware(self, app: FastAPI):
        """Setup middleware"""
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Compression middleware
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Request tracking middleware
        @app.middleware("http")
        async def track_requests(request: Request, call_next):
            start_time = asyncio.get_event_loop().time()
            
            try:
                response = await call_next(request)
                
                # Track successful requests
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                
                self.request_count += 1
                self.total_response_time += response_time
                
                # Add performance headers
                response.headers["X-Response-Time"] = f"{response_time:.3f}s"
                response.headers["X-Request-ID"] = str(self.request_count)
                
                return response
                
            except Exception as e:
                # Track errors
                self.error_count += 1
                logger.error(f"Request failed: {e}")
                raise
    
    def _setup_exception_handlers(self, app: FastAPI):
        """Setup global exception handlers"""
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": "http_error",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "timestamp": datetime.now().isoformat(),
                    "path": str(request.url)
                }
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An internal server error occurred",
                    "timestamp": datetime.now().isoformat(),
                    "path": str(request.url)
                }
            )
    
    def _setup_routes(self, app: FastAPI):
        """Setup API routes"""
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Check service health
                services_status = {}
                
                if self.gpu_manager:
                    gpu_stats = self.gpu_manager.get_performance_stats()
                    services_status["gpu_manager"] = {
                        "status": "healthy",
                        "memory_utilization": gpu_stats["memory"]["utilization"],
                        "allocated_buffers": gpu_stats["buffers"]["count"]
                    }
                
                if self.image_processor:
                    proc_stats = self.image_processor.get_performance_stats()
                    services_status["image_processor"] = {
                        "status": "healthy",
                        "active_tasks": proc_stats["active_tasks"],
                        "workers_active": proc_stats["workers_active"]
                    }
                
                if self.file_manager:
                    file_stats = self.file_manager.get_performance_stats()
                    services_status["file_manager"] = {
                        "status": "healthy",
                        "files_processed": file_stats["files_read"] + file_stats["files_written"]
                    }
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
                    "services": services_status,
                    "performance": {
                        "total_requests": self.request_count,
                        "error_rate": self.error_count / max(self.request_count, 1),
                        "avg_response_time": self.total_response_time / max(self.request_count, 1)
                    }
                }
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        # System status endpoint
        @app.get("/api/status")
        async def system_status():
            """Get comprehensive system status"""
            try:
                import psutil
                
                # System info
                system_info = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
                
                # Service stats
                service_stats = {}
                
                if self.gpu_manager:
                    service_stats["gpu"] = self.gpu_manager.get_performance_stats()
                
                if self.image_processor:
                    service_stats["image_processing"] = self.image_processor.get_performance_stats()
                
                if self.file_manager:
                    service_stats["file_operations"] = self.file_manager.get_performance_stats()
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "system": system_info,
                    "services": service_stats,
                    "application": {
                        "version": "1.0.0",
                        "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
                        "requests_handled": self.request_count,
                        "errors_occurred": self.error_count
                    }
                }
                
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to get system status")
        
        # Include API routers
        try:
            canvas_router = get_canvas_router()
            app.include_router(canvas_router)
            logger.info("Canvas API router included")
        except Exception as e:
            logger.warning(f"Failed to include canvas router: {e}")
        
        try:
            file_router = get_file_router()
            app.include_router(file_router)
            logger.info("File API router included")
        except Exception as e:
            logger.warning(f"Failed to include file router: {e}")
    
    def _setup_static_files(self, app: FastAPI):
        """Setup static file serving"""
        # Serve frontend files
        frontend_path = project_root / "frontend"
        if frontend_path.exists():
            app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
            logger.info(f"Serving frontend from: {frontend_path}")
        else:
            logger.warning(f"Frontend directory not found: {frontend_path}")
        
        # Serve uploaded files
        uploads_path = Path("uploads")
        uploads_path.mkdir(exist_ok=True)
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
        
        # Serve exported files
        exports_path = Path("exports")
        exports_path.mkdir(exist_ok=True)
        app.mount("/exports", StaticFiles(directory="exports"), name="exports")
    
    async def startup_event(self):
        """Application startup event"""
        try:
            logger.info("Starting 3D Paint Studio Backend...")
            self.startup_time = datetime.now()
            
            # Initialize services
            await self.initialize_services()
            
            logger.info("3D Paint Studio Backend started successfully")
            
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise
    
    async def shutdown_event(self):
        """Application shutdown event"""
        try:
            logger.info("Shutting down 3D Paint Studio Backend...")
            
            # Cleanup services
            await self.cleanup_services()
            
            logger.info("3D Paint Studio Backend shut down completed")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    async def initialize_services(self):
        """Initialize all backend services"""
        try:
            # Initialize GPU manager
            logger.info("Initializing GPU manager...")
            self.gpu_manager = initialize_gpu_manager(max_memory_mb=2048)
            
            # Initialize image processor
            logger.info("Initializing image processor...")
            self.image_processor = await initialize_image_processor(max_workers=4, cache_size_mb=512)
            
            # Initialize file manager
            logger.info("Initializing file manager...")
            self.file_manager = initialize_file_manager(max_file_size_mb=1024)
            
            self.services_initialized = True
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise
    
    async def cleanup_services(self):
        """Cleanup all services"""
        try:
            if self.image_processor:
                await self.image_processor.stop_workers()
                logger.info("Image processor stopped")
            
            if self.gpu_manager:
                self.gpu_manager.stop_monitoring()
                self.gpu_manager.cleanup_unused_resources()
                logger.info("GPU manager cleaned up")
            
            if self.file_manager:
                self.file_manager.clear_temp_files()
                logger.info("File manager cleaned up")
            
        except Exception as e:
            logger.error(f"Service cleanup error: {e}")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the application"""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not available")
        
        if not self.app:
            self.create_app()
        
        logger.info(f"Starting server on {host}:{port}")
        
        # Configure uvicorn
        config = {
            "host": host,
            "port": port,
            "log_level": "info",
            "access_log": True,
            "reload": kwargs.get("reload", False),
            "workers": kwargs.get("workers", 1)
        }
        
        # Run server
        uvicorn.run(self.app, **config)

# Global backend instance
backend = Paint3DBackend()

def create_app() -> FastAPI:
    """Create the FastAPI application"""
    return backend.create_app()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="3D Paint Studio Backend")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    try:
        # Run the application
        backend.run(
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()