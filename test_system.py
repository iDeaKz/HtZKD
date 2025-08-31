#!/usr/bin/env python3
"""
Test script for LivePrecisionCalculator Ultimate Edition
Comprehensive testing of all components and features
"""

import asyncio
import json
import time
from decimal import Decimal

# Test the healing suite
async def test_healing_suite():
    print("=== Testing The Healing Suite™ ===")
    
    try:
        from healing_suite import healing_suite
        
        # Test division by zero healing
        print("Testing division by zero healing...")
        try:
            1 / 0
        except Exception as e:
            result = await healing_suite.heal_error(e, {
                "operation": "divide",
                "operand1": "10",
                "operand2": "0"
            })
            print(f"Healing result: {result['success']}")
            print(f"Auto-fix applied: {result.get('auto_fix_applied', False)}")
        
        # Test invalid decimal healing
        print("Testing invalid decimal healing...")
        try:
            Decimal("invalid_number")
        except Exception as e:
            result = await healing_suite.heal_error(e, {
                "operation": "add",
                "operand1": "invalid_number"
            })
            print(f"Healing result: {result['success']}")
        
        # Get healing status
        status = healing_suite.get_healing_status()
        print(f"Healing suite active: {status['active']}")
        print(f"Total errors processed: {status['statistics']['total_errors_processed']}")
        
        print("✅ Healing Suite tests completed\n")
        
    except ImportError as e:
        print(f"❌ Could not import healing suite: {e}\n")

# Test currency manager
async def test_currency_manager():
    print("=== Testing Currency Manager ===")
    
    try:
        from currency_manager import currency_manager
        
        # Test supported currencies
        currencies = currency_manager.get_supported_currencies()
        print(f"Supported currencies: {len(currencies)}")
        
        fiat_currencies = currency_manager.get_fiat_currencies()
        crypto_currencies = currency_manager.get_crypto_currencies()
        print(f"Fiat currencies: {len(fiat_currencies)}")
        print(f"Crypto currencies: {len(crypto_currencies)}")
        
        # Test exchange rate
        print("Testing exchange rates...")
        rate, metadata = await currency_manager.get_exchange_rate("USD", "EUR")
        if rate:
            print(f"USD/EUR rate: {rate}")
            print(f"Source: {metadata.get('source') if metadata else 'Unknown'}")
        else:
            print("❌ Failed to get USD/EUR rate")
        
        # Test currency conversion
        print("Testing currency conversion...")
        converted, metadata = await currency_manager.convert_amount("100.00", "USD", "EUR")
        if converted:
            print(f"$100 USD = {converted} EUR")
        else:
            print("❌ Failed to convert currency")
        
        # Test crypto rate
        print("Testing crypto rates...")
        btc_rate, metadata = await currency_manager.get_exchange_rate("BTC", "USD")
        if btc_rate:
            print(f"BTC/USD rate: {btc_rate}")
        else:
            print("❌ Failed to get BTC/USD rate")
        
        print("✅ Currency Manager tests completed\n")
        
    except ImportError as e:
        print(f"❌ Could not import currency manager: {e}\n")

# Test LivePrecisionCalculator
async def test_calculator():
    print("=== Testing LivePrecisionCalculator ===")
    
    try:
        from fastapi_main import LivePrecisionCalculator
        
        calculator = LivePrecisionCalculator()
        
        # Test basic calculation
        print("Testing basic calculation...")
        try:
            result = await calculator.calculate_with_healing(
                "add", 
                "123.456789012345678901234567890", 
                "987.654321098765432109876543210"
            )
            if result['success']:
                print(f"Addition result: {result['result']}")
                print(f"Precision: {result['metadata']['precision_used']}")
            else:
                print(f"❌ Calculation failed: {result.get('error')}")
        except Exception as e:
            print(f"❌ Calculator error: {e}")
        
        # Test division
        print("Testing division...")
        try:
            result = await calculator.calculate_with_healing(
                "divide",
                "1000.0",
                "3.0"
            )
            if result['success']:
                print(f"Division result: {result['result']}")
            else:
                print(f"❌ Division failed: {result.get('error')}")
        except Exception as e:
            print(f"❌ Division error: {e}")
        
        # Test metrics
        metrics = calculator.get_metrics()
        print(f"Calculations performed: {metrics['calculations_performed']}")
        print(f"Success rate: {metrics['success_rate']:.2%}")
        
        print("✅ Calculator tests completed\n")
        
    except ImportError as e:
        print(f"❌ Could not import calculator: {e}\n")
    except Exception as e:
        print(f"❌ Calculator test error: {e}\n")

# Test database models
async def test_database():
    print("=== Testing Database Models ===")
    
    try:
        from fastapi_models import create_database_engine, create_tables, get_session_maker
        from fastapi_models import CalculationRecord, SystemMetrics, CurrencyRate
        import uuid
        
        # Create test database
        engine = create_database_engine("sqlite:///test_db.sqlite")
        create_tables(engine)
        
        SessionLocal = get_session_maker(engine)
        session = SessionLocal()
        
        # Test calculation record
        calc_record = CalculationRecord(
            calculation_id=str(uuid.uuid4()),
            operation="add",
            operand1="123.456",
            operand2="789.012",
            result="912.468",
            precision_used=60,
            status="success",
            execution_time_ms=25.5
        )
        
        session.add(calc_record)
        session.commit()
        
        # Test metrics record
        metrics_record = SystemMetrics(
            calculations_count=1,
            error_count=0,
            success_rate=100.0,
            avg_response_time_ms=25.5
        )
        
        session.add(metrics_record)
        session.commit()
        
        # Test currency rate
        rate_record = CurrencyRate(
            from_currency="USD",
            to_currency="EUR",
            rate="0.85",
            rate_decimal=0.85,
            source="test"
        )
        
        session.add(rate_record)
        session.commit()
        
        session.close()
        
        print("✅ Database models test completed\n")
        
    except ImportError as e:
        print(f"❌ Could not import database models: {e}\n")
    except Exception as e:
        print(f"❌ Database test error: {e}\n")

# Test API models
def test_api_models():
    print("=== Testing API Models ===")
    
    try:
        from fastapi_models import CalculationRequest, CalculationResponse, MetricsResponse
        
        # Test calculation request
        request = CalculationRequest(
            operation="add",
            operand1="123.456",
            operand2="789.012",
            currency_from="USD",
            currency_to="EUR"
        )
        print(f"Request operation: {request.operation}")
        print(f"Request currencies: {request.currency_from} -> {request.currency_to}")
        
        # Test response model
        response = CalculationResponse(
            success=True,
            calculation_id="test-123",
            result="912.468",
            result_decimal=912.468,
            operation="add",
            operand1="123.456",
            operand2="789.012",
            precision_used=60,
            execution_time_ms=25.5,
            timestamp=time.time()
        )
        print(f"Response success: {response.success}")
        print(f"Response result: {response.result}")
        
        print("✅ API models test completed\n")
        
    except ImportError as e:
        print(f"❌ Could not import API models: {e}\n")
    except Exception as e:
        print(f"❌ API models test error: {e}\n")

# Main test runner
async def run_all_tests():
    print("🚀 LivePrecisionCalculator Ultimate Edition - Component Tests\n")
    
    await test_healing_suite()
    await test_currency_manager()
    await test_calculator()
    await test_database()
    test_api_models()
    
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: python fastapi_main.py")
    print("2. Open dashboard: http://localhost:8000/dashboard")
    print("3. API documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(run_all_tests())