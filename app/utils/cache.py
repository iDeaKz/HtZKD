# app/utils/cache.py

import json
import logging
from typing import Any, Optional

import redis

from app.utils.logging import setup_logger

# Setup logging for the RedisCache
logger = logging.getLogger("RedisCache")
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create console handler and set level
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Create file handler and set level
file_handler = logging.handlers.RotatingFileHandler(
    "cache.log", maxBytes=5_000_000, backupCount=3
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class RedisCache:
    """
    RedisCache provides methods to interact with a Redis database for caching purposes.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        """
        Initializes the RedisCache client.

        Args:
            host (str): Redis server hostname.
            port (int): Redis server port.
            db (int): Redis database index.
        """
        try:
            self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {host}:{port}, DB: {db}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Sets a key-value pair in Redis.

        Args:
            key (str): Cache key.
            value (Any): Data to cache (will be JSON serialized).
            expire (Optional[int]): Expiration time in seconds.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            self.client.set(key, json.dumps(value), ex=expire)
            logger.info(f"Set key '{key}' with expiration {expire} seconds.")
            return True
        except Exception as e:
            logger.error(f"Error setting key '{key}': {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a value from Redis by key.

        Args:
            key (str): Cache key.

        Returns:
            Optional[Any]: JSON deserialized value, or None if the key does not exist.
        """
        try:
            value = self.client.get(key)
            if value:
                logger.info(f"Retrieved key '{key}'.")
                return json.loads(value)
            else:
                logger.warning(f"Key '{key}' not found.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving key '{key}': {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Deletes a key from Redis.

        Args:
            key (str): Cache key.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            self.client.delete(key)
            logger.info(f"Deleted key '{key}'.")
            return True
        except Exception as e:
            logger.error(f"Error deleting key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Checks if a key exists in Redis.

        Args:
            key (str): Cache key.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        try:
            exists = self.client.exists(key)
            logger.info(f"Key '{key}' exists: {bool(exists)}.")
            return bool(exists)
        except Exception as e:
            logger.error(f"Error checking existence of key '{key}': {e}")
            return False

    def flush(self) -> bool:
        """
        Flushes all keys from the Redis database.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            self.client.flushdb()
            logger.warning("Flushed all keys from Redis database.")
            return True
        except Exception as e:
            logger.error(f"Error flushing database: {e}")
            return False


# Example usage
if __name__ == "__main__":
    try:
        cache = RedisCache()
        cache.set("test_key", {"name": "example", "value": 42}, expire=3600)
        value = cache.get("test_key")
        print("Retrieved value:", value)
        cache.delete("test_key")
        print("Key exists after deletion:", cache.exists("test_key"))
    except Exception as err:
        print(f"Cache setup failed: {err}")
