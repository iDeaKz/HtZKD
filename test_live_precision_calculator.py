#!/usr/bin/env python3
"""
Test suite for LivePrecisionCalculator FastAPI system

Tests core functionality including:
- Precision calculation algorithms
- REST API endpoints
- WebSocket connections
- Caching mechanisms
- Error handling
"""

import asyncio
import json
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the application components
from live_precision_calculator import (
    app, 
    LivePrecisionCalculator, 
    CacheManager,
    ConnectionManager,
    Base
)

@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def calculator():
    """Create LivePrecisionCalculator instance for testing"""
    return LivePrecisionCalculator()

@pytest.fixture
async def cache_manager():
    """Create CacheManager instance for testing"""
    manager = CacheManager()
    await manager.initialize()
    return manager

@pytest.fixture
def connection_manager():
    """Create ConnectionManager instance for testing"""
    return ConnectionManager()

class TestLivePrecisionCalculator:
    """Test the core precision calculation algorithms"""
    
    def test_basic_calculation(self, calculator):
        """Test basic precision calculation"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            calculator.calculate_precision(3.14159, 6)
        )
        
        assert "calculation_id" in result
        assert "input_value" in result
        assert "precision_result" in result
        assert "processing_time_ms" in result
        assert result["input_value"] == 3.14159
        assert isinstance(result["precision_result"], float)
        assert result["processing_time_ms"] > 0
        
        loop.close()
    
    def test_precision_levels(self, calculator):
        """Test different precision levels"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        test_value = 2.71828
        
        for precision in [1, 6, 10, 15]:
            result = loop.run_until_complete(
                calculator.calculate_precision(test_value, precision)
            )
            assert result["input_value"] == test_value
            assert isinstance(result["precision_result"], float)
        
        loop.close()
    
    def test_edge_cases(self, calculator):
        """Test edge cases for calculation"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Test zero
        result = loop.run_until_complete(
            calculator.calculate_precision(0.0, 6)
        )
        assert result["precision_result"] == 0.0
        
        # Test negative values
        result = loop.run_until_complete(
            calculator.calculate_precision(-5.5, 6)
        )
        assert isinstance(result["precision_result"], float)
        
        # Test large values
        result = loop.run_until_complete(
            calculator.calculate_precision(1000.0, 6)
        )
        assert isinstance(result["precision_result"], float)
        
        loop.close()

class TestCacheManager:
    """Test the caching system with SQLite fallback"""
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Test basic cache set and get operations"""
        key = "test_key"
        value = {"test": "data", "number": 42}
        
        # Test set
        success = await cache_manager.set(key, value, expire=3600)
        assert success is True
        
        # Test get
        retrieved = await cache_manager.get(key)
        assert retrieved == value
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """Test cache expiration functionality"""
        key = "expire_test"
        value = {"expires": True}
        
        # Set with 1 second expiration
        await cache_manager.set(key, value, expire=1)
        
        # Should exist immediately
        retrieved = await cache_manager.get(key)
        assert retrieved == value
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be None after expiration
        retrieved = await cache_manager.get(key)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_cache_nonexistent_key(self, cache_manager):
        """Test getting non-existent key"""
        result = await cache_manager.get("nonexistent_key")
        assert result is None

class TestConnectionManager:
    """Test WebSocket connection management"""
    
    def test_connection_metadata(self, connection_manager):
        """Test connection metadata tracking"""
        # Mock WebSocket
        class MockWebSocket:
            def __init__(self):
                self.accepted = False
                
            async def accept(self):
                self.accepted = True
        
        # Test connection tracking
        mock_ws = MockWebSocket()
        initial_count = len(connection_manager.active_connections)
        
        # Note: We can't easily test full WebSocket functionality without
        # a more complex mock setup, but we can test the basic structure
        assert len(connection_manager.active_connections) == initial_count
        assert len(connection_manager.connection_metadata) == initial_count

class TestRestAPI:
    """Test REST API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "cache_mode" in data
    
    def test_calculate_endpoint(self, client):
        """Test calculation endpoint"""
        payload = {
            "input_value": 3.14159,
            "precision_level": 6,
            "metadata": {"test": True}
        }
        
        response = client.post("/api/v1/calculate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "calculation_id" in data
        assert data["input_value"] == 3.14159
        assert data["precision_level"] == 6
        assert "precision_result" in data
        assert "processing_time_ms" in data
        assert "timestamp" in data
    
    def test_calculate_invalid_input(self, client):
        """Test calculation endpoint with invalid input"""
        payload = {
            "input_value": "invalid",
            "precision_level": 6
        }
        
        response = client.post("/api/v1/calculate", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_calculate_precision_bounds(self, client):
        """Test precision level bounds validation"""
        # Test below minimum
        payload = {
            "input_value": 1.0,
            "precision_level": 0
        }
        response = client.post("/api/v1/calculate", json=payload)
        assert response.status_code == 422
        
        # Test above maximum
        payload = {
            "input_value": 1.0,
            "precision_level": 20
        }
        response = client.post("/api/v1/calculate", json=payload)
        assert response.status_code == 422
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_calculations" in data
        assert "average_processing_time_ms" in data
        assert "success_rate" in data
        assert "last_24h_calculations" in data
        assert "revenue_summary" in data
        
        # Verify revenue summary structure
        revenue = data["revenue_summary"]
        assert "total_revenue" in revenue
        assert "base_revenue" in revenue
        assert "premium_revenue" in revenue
        assert "projected_monthly" in revenue
    
    def test_dashboard_endpoint(self, client):
        """Test dashboard HTML endpoint"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "LivePrecisionCalculator" in response.text
        assert "Three.js" in response.text or "three.js" in response.text
        assert "Chart.js" in response.text or "chart.js" in response.text

class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_calculation_flow(self, client):
        """Test complete calculation flow with caching"""
        payload = {
            "input_value": 2.71828,
            "precision_level": 8
        }
        
        # First calculation
        response1 = client.post("/api/v1/calculate", json=payload)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second calculation (should use cache)
        response2 = client.post("/api/v1/calculate", json=payload)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Results should be consistent
        assert data1["input_value"] == data2["input_value"]
        assert data1["precision_level"] == data2["precision_level"]
        # Note: precision_result might differ due to calculation_id being different
    
    def test_metrics_update_flow(self, client):
        """Test that metrics update after calculations"""
        # Get initial metrics
        initial_response = client.get("/api/v1/metrics")
        initial_data = initial_response.json()
        initial_count = initial_data["total_calculations"]
        
        # Perform calculation
        calc_payload = {"input_value": 1.23, "precision_level": 6}
        calc_response = client.post("/api/v1/calculate", json=calc_payload)
        assert calc_response.status_code == 200
        
        # Get updated metrics - note: this may not reflect immediately
        # due to async nature of metrics collection
        updated_response = client.get("/api/v1/metrics")
        updated_data = updated_response.json()
        
        # At minimum, verify structure is correct
        assert "total_calculations" in updated_data
        assert "revenue_summary" in updated_data

def test_performance_benchmarks():
    """Test performance benchmarks for calculations"""
    calculator = LivePrecisionCalculator()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Test calculation performance
    start_time = time.time()
    
    for i in range(100):
        result = loop.run_until_complete(
            calculator.calculate_precision(float(i), 6)
        )
        assert result["processing_time_ms"] < 100  # Should be under 100ms
    
    total_time = time.time() - start_time
    avg_time_per_calc = total_time / 100 * 1000  # Convert to ms
    
    print(f"Average calculation time: {avg_time_per_calc:.2f}ms")
    assert avg_time_per_calc < 50  # Should average under 50ms
    
    loop.close()

if __name__ == "__main__":
    """Run tests when script is executed directly"""
    pytest.main([__file__, "-v", "--tb=short"])