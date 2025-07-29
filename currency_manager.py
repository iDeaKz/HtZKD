"""
Multi-Currency Support System for LivePrecisionCalculator
Real-time exchange rates with fallback mechanisms and high-precision calculations
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import os
from collections import defaultdict

# Set high precision for currency calculations
getcontext().prec = 60

logger = logging.getLogger(__name__)

class CurrencyType(Enum):
    FIAT = "fiat"
    CRYPTO = "crypto"
    COMMODITY = "commodity"

@dataclass
class Currency:
    """Currency definition with metadata"""
    code: str
    name: str
    symbol: str
    type: CurrencyType
    decimal_places: int = 8
    is_active: bool = True
    country: Optional[str] = None
    
class ExchangeRateProvider:
    """Base class for exchange rate providers"""
    
    def __init__(self, name: str, base_url: str, api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.last_update = None
        self.request_count = 0
        self.error_count = 0
        self.avg_response_time = 0.0
    
    async def get_rate(self, from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
        """Get exchange rate between two currencies. Returns (rate, metadata)"""
        raise NotImplementedError
    
    async def get_multiple_rates(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Decimal]:
        """Get multiple exchange rates from a base currency"""
        rates = {}
        for target in target_currencies:
            rate, _ = await self.get_rate(base_currency, target)
            if rate:
                rates[target] = rate
        return rates
    
    def get_stats(self) -> dict:
        """Get provider statistics"""
        return {
            "name": self.name,
            "requests": self.request_count,
            "errors": self.error_count,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1),
            "avg_response_time_ms": self.avg_response_time,
            "last_update": self.last_update
        }

class ExchangeRatesAPIProvider(ExchangeRateProvider):
    """ExchangeRates-API.io provider for fiat currencies"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="ExchangeRates-API",
            base_url="https://api.exchangerate-api.com/v4/latest",
            api_key=api_key
        )
    
    async def get_rate(self, from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
        """Get exchange rate from ExchangeRates-API"""
        if from_currency == to_currency:
            return Decimal('1.0'), {"source": self.name, "timestamp": datetime.utcnow()}
        
        start_time = time.time()
        self.request_count += 1
        
        try:
            url = f"{self.base_url}/{from_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if to_currency in data.get('rates', {}):
                            rate = Decimal(str(data['rates'][to_currency]))
                            self.last_update = datetime.utcnow()
                            
                            # Update response time
                            response_time = (time.time() - start_time) * 1000
                            self.avg_response_time = (self.avg_response_time + response_time) / 2
                            
                            metadata = {
                                "source": self.name,
                                "timestamp": datetime.utcnow(),
                                "base_currency": from_currency,
                                "response_time_ms": response_time,
                                "provider_timestamp": data.get('date')
                            }
                            
                            return rate, metadata
                        else:
                            logger.warning(f"Currency {to_currency} not found in response")
                            self.error_count += 1
                            return None, None
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        self.error_count += 1
                        return None, None
                        
        except Exception as e:
            logger.error(f"Error fetching exchange rate: {e}")
            self.error_count += 1
            return None, None

class CoinGeckoProvider(ExchangeRateProvider):
    """CoinGecko provider for cryptocurrency rates"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="CoinGecko",
            base_url="https://api.coingecko.com/api/v3",
            api_key=api_key
        )
        
        # Mapping of currency codes to CoinGecko IDs
        self.crypto_mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'SOL': 'solana',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'LTC': 'litecoin'
        }
    
    async def get_rate(self, from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
        """Get cryptocurrency exchange rate"""
        if from_currency == to_currency:
            return Decimal('1.0'), {"source": self.name, "timestamp": datetime.utcnow()}
        
        start_time = time.time()
        self.request_count += 1
        
        try:
            # Handle crypto to fiat conversions
            if from_currency in self.crypto_mapping:
                crypto_id = self.crypto_mapping[from_currency]
                vs_currency = to_currency.lower()
                
                url = f"{self.base_url}/simple/price"
                params = {
                    'ids': crypto_id,
                    'vs_currencies': vs_currency,
                    'precision': '18'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if crypto_id in data and vs_currency in data[crypto_id]:
                                rate = Decimal(str(data[crypto_id][vs_currency]))
                                self.last_update = datetime.utcnow()
                                
                                # Update response time
                                response_time = (time.time() - start_time) * 1000
                                self.avg_response_time = (self.avg_response_time + response_time) / 2
                                
                                metadata = {
                                    "source": self.name,
                                    "timestamp": datetime.utcnow(),
                                    "crypto_id": crypto_id,
                                    "vs_currency": vs_currency,
                                    "response_time_ms": response_time
                                }
                                
                                return rate, metadata
            
            # Handle fiat to crypto conversions
            elif to_currency in self.crypto_mapping:
                # Get crypto rate in from_currency and invert
                rate, metadata = await self.get_rate(to_currency, from_currency)
                if rate and rate != Decimal('0'):
                    inverted_rate = Decimal('1') / rate
                    if metadata:
                        metadata["inverted"] = True
                    return inverted_rate, metadata
            
            logger.warning(f"Currency pair {from_currency}/{to_currency} not supported by CoinGecko")
            self.error_count += 1
            return None, None
            
        except Exception as e:
            logger.error(f"Error fetching crypto rate: {e}")
            self.error_count += 1
            return None, None

class MockProvider(ExchangeRateProvider):
    """Mock provider for development and fallback"""
    
    def __init__(self):
        super().__init__(
            name="MockProvider",
            base_url="mock://localhost"
        )
        
        # Mock exchange rates (not for production use!)
        self.mock_rates = {
            # Fiat to USD rates
            ('EUR', 'USD'): Decimal('1.0850'),
            ('GBP', 'USD'): Decimal('1.2650'),
            ('JPY', 'USD'): Decimal('0.0091'),
            ('CHF', 'USD'): Decimal('1.0950'),
            ('CAD', 'USD'): Decimal('0.7850'),
            ('AUD', 'USD'): Decimal('0.6750'),
            
            # Crypto to USD rates
            ('BTC', 'USD'): Decimal('45000.00'),
            ('ETH', 'USD'): Decimal('3000.00'),
            ('ADA', 'USD'): Decimal('0.45'),
            ('DOT', 'USD'): Decimal('6.50'),
            ('SOL', 'USD'): Decimal('95.00'),
            ('MATIC', 'USD'): Decimal('0.85'),
            ('AVAX', 'USD'): Decimal('18.50'),
            ('LINK', 'USD'): Decimal('14.50'),
            ('UNI', 'USD'): Decimal('6.25'),
            ('LTC', 'USD'): Decimal('95.00'),
        }
    
    async def get_rate(self, from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
        """Get mock exchange rate"""
        if from_currency == to_currency:
            return Decimal('1.0'), {"source": self.name, "timestamp": datetime.utcnow()}
        
        start_time = time.time()
        self.request_count += 1
        
        # Add small random delay to simulate network latency
        await asyncio.sleep(0.1)
        
        try:
            # Direct rate lookup
            if (from_currency, to_currency) in self.mock_rates:
                rate = self.mock_rates[(from_currency, to_currency)]
            # Inverse rate lookup
            elif (to_currency, from_currency) in self.mock_rates:
                rate = Decimal('1') / self.mock_rates[(to_currency, from_currency)]
            # Cross-rate calculation via USD
            elif (from_currency, 'USD') in self.mock_rates and (to_currency, 'USD') in self.mock_rates:
                from_usd_rate = self.mock_rates[(from_currency, 'USD')]
                to_usd_rate = self.mock_rates[(to_currency, 'USD')]
                rate = from_usd_rate / to_usd_rate
            elif ('USD', from_currency) in self.mock_rates and ('USD', to_currency) in self.mock_rates:
                from_rate = Decimal('1') / self.mock_rates[('USD', from_currency)]
                to_rate = Decimal('1') / self.mock_rates[('USD', to_currency)]
                rate = from_rate / to_rate
            else:
                # Default rate for unsupported pairs
                rate = Decimal('1.0')
            
            self.last_update = datetime.utcnow()
            
            # Update response time
            response_time = (time.time() - start_time) * 1000
            self.avg_response_time = (self.avg_response_time + response_time) / 2
            
            metadata = {
                "source": self.name,
                "timestamp": datetime.utcnow(),
                "response_time_ms": response_time,
                "mock_data": True
            }
            
            return rate, metadata
            
        except Exception as e:
            logger.error(f"Mock provider error: {e}")
            self.error_count += 1
            return None, None

class CurrencyManager:
    """Comprehensive currency management system"""
    
    def __init__(self):
        self.currencies = self._initialize_currencies()
        self.providers = [
            ExchangeRatesAPIProvider(),
            CoinGeckoProvider(),
            MockProvider()  # Fallback provider
        ]
        
        # Cache settings
        self.rate_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "provider_failures": defaultdict(int),
            "successful_conversions": 0,
            "failed_conversions": 0
        }
    
    def _initialize_currencies(self) -> Dict[str, Currency]:
        """Initialize supported currencies"""
        currencies = {}
        
        # Major fiat currencies
        fiat_currencies = [
            Currency("USD", "US Dollar", "$", CurrencyType.FIAT, 2, True, "United States"),
            Currency("EUR", "Euro", "€", CurrencyType.FIAT, 2, True, "European Union"),
            Currency("GBP", "British Pound", "£", CurrencyType.FIAT, 2, True, "United Kingdom"),
            Currency("JPY", "Japanese Yen", "¥", CurrencyType.FIAT, 0, True, "Japan"),
            Currency("CHF", "Swiss Franc", "CHF", CurrencyType.FIAT, 2, True, "Switzerland"),
            Currency("CAD", "Canadian Dollar", "C$", CurrencyType.FIAT, 2, True, "Canada"),
            Currency("AUD", "Australian Dollar", "A$", CurrencyType.FIAT, 2, True, "Australia"),
            Currency("NZD", "New Zealand Dollar", "NZ$", CurrencyType.FIAT, 2, True, "New Zealand"),
            Currency("SEK", "Swedish Krona", "kr", CurrencyType.FIAT, 2, True, "Sweden"),
            Currency("NOK", "Norwegian Krone", "kr", CurrencyType.FIAT, 2, True, "Norway"),
            Currency("DKK", "Danish Krone", "kr", CurrencyType.FIAT, 2, True, "Denmark"),
            Currency("PLN", "Polish Zloty", "zł", CurrencyType.FIAT, 2, True, "Poland"),
            Currency("CZK", "Czech Koruna", "Kč", CurrencyType.FIAT, 2, True, "Czech Republic"),
            Currency("HUF", "Hungarian Forint", "Ft", CurrencyType.FIAT, 0, True, "Hungary"),
            Currency("BGN", "Bulgarian Lev", "лв", CurrencyType.FIAT, 2, True, "Bulgaria"),
            Currency("RON", "Romanian Leu", "lei", CurrencyType.FIAT, 2, True, "Romania"),
            Currency("HRK", "Croatian Kuna", "kn", CurrencyType.FIAT, 2, True, "Croatia"),
            Currency("RUB", "Russian Ruble", "₽", CurrencyType.FIAT, 2, True, "Russia"),
            Currency("CNY", "Chinese Yuan", "¥", CurrencyType.FIAT, 2, True, "China"),
            Currency("INR", "Indian Rupee", "₹", CurrencyType.FIAT, 2, True, "India"),
            Currency("BRL", "Brazilian Real", "R$", CurrencyType.FIAT, 2, True, "Brazil"),
            Currency("MXN", "Mexican Peso", "$", CurrencyType.FIAT, 2, True, "Mexico"),
            Currency("ZAR", "South African Rand", "R", CurrencyType.FIAT, 2, True, "South Africa"),
            Currency("SGD", "Singapore Dollar", "S$", CurrencyType.FIAT, 2, True, "Singapore"),
            Currency("HKD", "Hong Kong Dollar", "HK$", CurrencyType.FIAT, 2, True, "Hong Kong"),
        ]
        
        # Major cryptocurrencies
        crypto_currencies = [
            Currency("BTC", "Bitcoin", "₿", CurrencyType.CRYPTO, 8, True),
            Currency("ETH", "Ethereum", "Ξ", CurrencyType.CRYPTO, 8, True),
            Currency("ADA", "Cardano", "₳", CurrencyType.CRYPTO, 8, True),
            Currency("DOT", "Polkadot", "DOT", CurrencyType.CRYPTO, 8, True),
            Currency("SOL", "Solana", "SOL", CurrencyType.CRYPTO, 8, True),
            Currency("MATIC", "Polygon", "MATIC", CurrencyType.CRYPTO, 8, True),
            Currency("AVAX", "Avalanche", "AVAX", CurrencyType.CRYPTO, 8, True),
            Currency("LINK", "Chainlink", "LINK", CurrencyType.CRYPTO, 8, True),
            Currency("UNI", "Uniswap", "UNI", CurrencyType.CRYPTO, 8, True),
            Currency("LTC", "Litecoin", "Ł", CurrencyType.CRYPTO, 8, True),
        ]
        
        # Add all currencies to dictionary
        for currency in fiat_currencies + crypto_currencies:
            currencies[currency.code] = currency
        
        return currencies
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str, force_refresh: bool = False) -> Tuple[Optional[Decimal], Optional[dict]]:
        """Get exchange rate with caching and fallback mechanisms"""
        self.stats["total_requests"] += 1
        
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency check
        if from_currency == to_currency:
            return Decimal('1.0'), {
                "source": "internal",
                "timestamp": datetime.utcnow(),
                "same_currency": True
            }
        
        # Check currency support
        if from_currency not in self.currencies or to_currency not in self.currencies:
            logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
            self.stats["failed_conversions"] += 1
            return None, None
        
        # Check cache first (unless force refresh)
        cache_key = f"{from_currency}_{to_currency}"
        if not force_refresh and cache_key in self.rate_cache:
            cached_data = self.rate_cache[cache_key]
            cache_age = datetime.utcnow() - cached_data["timestamp"]
            
            if cache_age < self.cache_duration:
                self.stats["cache_hits"] += 1
                return cached_data["rate"], {
                    **cached_data["metadata"],
                    "from_cache": True,
                    "cache_age_seconds": cache_age.total_seconds()
                }
        
        self.stats["cache_misses"] += 1
        
        # Try providers in order
        for provider in self.providers:
            try:
                rate, metadata = await provider.get_rate(from_currency, to_currency)
                
                if rate is not None:
                    # Cache the result
                    self.rate_cache[cache_key] = {
                        "rate": rate,
                        "metadata": metadata,
                        "timestamp": datetime.utcnow()
                    }
                    
                    self.stats["successful_conversions"] += 1
                    return rate, metadata
                
            except Exception as e:
                logger.error(f"Provider {provider.name} failed: {e}")
                self.stats["provider_failures"][provider.name] += 1
                continue
        
        # All providers failed
        logger.error(f"All providers failed for {from_currency}/{to_currency}")
        self.stats["failed_conversions"] += 1
        return None, None
    
    async def convert_amount(self, amount: Union[str, Decimal], from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
        """Convert amount from one currency to another with high precision"""
        try:
            # Convert amount to high-precision Decimal
            if isinstance(amount, str):
                amount_decimal = Decimal(amount)
            else:
                amount_decimal = Decimal(str(amount))
            
            # Get exchange rate
            rate, metadata = await self.get_exchange_rate(from_currency, to_currency)
            
            if rate is None:
                return None, None
            
            # Perform high-precision conversion
            converted_amount = amount_decimal * rate
            
            # Round to appropriate decimal places for target currency
            target_currency = self.currencies.get(to_currency.upper())
            if target_currency:
                decimal_places = target_currency.decimal_places
                converted_amount = converted_amount.quantize(Decimal('0.1') ** decimal_places)
            
            # Enhanced metadata
            if metadata:
                metadata.update({
                    "original_amount": str(amount_decimal),
                    "converted_amount": str(converted_amount),
                    "exchange_rate": str(rate),
                    "conversion_timestamp": datetime.utcnow()
                })
            
            return converted_amount, metadata
            
        except Exception as e:
            logger.error(f"Amount conversion failed: {e}")
            return None, None
    
    def get_supported_currencies(self) -> List[Dict[str, Any]]:
        """Get list of all supported currencies with metadata"""
        return [
            {
                "code": currency.code,
                "name": currency.name,
                "symbol": currency.symbol,
                "type": currency.type.value,
                "decimal_places": currency.decimal_places,
                "is_active": currency.is_active,
                "country": currency.country
            }
            for currency in self.currencies.values()
            if currency.is_active
        ]
    
    def get_fiat_currencies(self) -> List[str]:
        """Get list of supported fiat currency codes"""
        return [
            code for code, currency in self.currencies.items()
            if currency.type == CurrencyType.FIAT and currency.is_active
        ]
    
    def get_crypto_currencies(self) -> List[str]:
        """Get list of supported cryptocurrency codes"""
        return [
            code for code, currency in self.currencies.items()
            if currency.type == CurrencyType.CRYPTO and currency.is_active
        ]
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        return {
            "providers": [provider.get_stats() for provider in self.providers],
            "cache_stats": {
                "total_requests": self.stats["total_requests"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["total_requests"], 1),
                "cached_pairs": len(self.rate_cache)
            },
            "conversion_stats": {
                "successful_conversions": self.stats["successful_conversions"],
                "failed_conversions": self.stats["failed_conversions"],
                "success_rate": self.stats["successful_conversions"] / max(self.stats["total_requests"], 1)
            },
            "provider_failures": dict(self.stats["provider_failures"])
        }
    
    async def get_currency_matrix(self, base_currencies: List[str] = None) -> Dict[str, Dict[str, Decimal]]:
        """Get exchange rate matrix for multiple currencies"""
        if base_currencies is None:
            base_currencies = ['USD', 'EUR', 'BTC']
        
        matrix = {}
        
        for base in base_currencies:
            matrix[base] = {}
            for target_code in self.currencies.keys():
                if base != target_code:
                    rate, _ = await self.get_exchange_rate(base, target_code)
                    if rate:
                        matrix[base][target_code] = rate
                else:
                    matrix[base][target_code] = Decimal('1.0')
        
        return matrix
    
    def clear_cache(self):
        """Clear the exchange rate cache"""
        self.rate_cache.clear()
        logger.info("Exchange rate cache cleared")
    
    def is_currency_supported(self, currency_code: str) -> bool:
        """Check if a currency is supported"""
        return currency_code.upper() in self.currencies

# Global currency manager instance
currency_manager = CurrencyManager()

# Utility functions
async def convert_currency(amount: Union[str, Decimal], from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
    """Convenient function for currency conversion"""
    return await currency_manager.convert_amount(amount, from_currency, to_currency)

async def get_exchange_rate(from_currency: str, to_currency: str) -> Tuple[Optional[Decimal], Optional[dict]]:
    """Convenient function for getting exchange rates"""
    return await currency_manager.get_exchange_rate(from_currency, to_currency)

def get_supported_currencies() -> List[Dict[str, Any]]:
    """Get all supported currencies"""
    return currency_manager.get_supported_currencies()

# Example usage and testing
if __name__ == "__main__":
    async def test_currency_system():
        manager = CurrencyManager()
        
        print("Testing Currency Manager...")
        print(f"Supported currencies: {len(manager.get_supported_currencies())}")
        print(f"Fiat currencies: {len(manager.get_fiat_currencies())}")
        print(f"Crypto currencies: {len(manager.get_crypto_currencies())}")
        
        # Test exchange rate
        rate, metadata = await manager.get_exchange_rate("USD", "EUR")
        print(f"USD/EUR rate: {rate}")
        print(f"Metadata: {metadata}")
        
        # Test conversion
        converted, metadata = await manager.convert_amount("100.00", "USD", "EUR")
        print(f"$100 USD = {converted} EUR")
        
        # Test crypto conversion
        btc_rate, metadata = await manager.get_exchange_rate("BTC", "USD")
        print(f"BTC/USD rate: {btc_rate}")
        
        # Test provider stats
        stats = manager.get_provider_stats()
        print(f"Provider stats: {stats}")
    
    # Run test
    asyncio.run(test_currency_system())