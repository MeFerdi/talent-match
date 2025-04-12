import redis
import json
from typing import Callable, Dict, Any
from domain.utils.logging import logger

class RedisEventStream:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.client.pubsub()
        logger.info("Redis event stream initialized")

    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to Redis channel with message handler"""
        def wrapped_callback(message: Dict):
            try:
                data = json.loads(message["data"])
                callback(data)
            except json.JSONDecodeError:
                callback({"raw": message["data"]})
            except Exception as e:
                logger.error(f"Message handling failed: {e}")

        self.pubsub.subscribe(**{channel: wrapped_callback})
        logger.info(f"Subscribed to Redis channel: {channel}")

    def publish(self, channel: str, data: Dict[str, Any]) -> bool:
        """Publish data to Redis channel"""
        try:
            self.client.publish(channel, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False

    def run(self) -> None:
        """Start listening for messages (blocking)"""
        self.pubsub.run_in_thread(sleep_time=0.1)