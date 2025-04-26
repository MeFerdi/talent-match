from pydantic import BaseModel, Field
from typing import ClassVar, Optional, List
import redis
from domain.utils.logging import logger


class Talent(BaseModel):
    """
    Represents a Talent object with attributes for Redis storage and retrieval.
    """
    AVAILABLE_KEY: ClassVar[str] = 'available'
    RATING_KEY: ClassVar[str] = 'rating'

    talent_id: str = Field(..., min_length=1, description="Unique identifier for the talent.")
    available: bool = True
    rating: float = Field(ge=0, le=5, description="Talent's rating, between 0 and 5.")

    @classmethod
    def from_redis(cls, redis_client: redis.Redis, talent_id: str) -> Optional['Talent']:
        """
        Load a Talent object from Redis.

        Args:
            redis_client (redis.Redis): Redis client instance.
            talent_id (str): The ID of the talent to load.

        Returns:
            Optional[Talent]: The Talent object if found, otherwise None.
        """
        try:
            data = redis_client.hgetall(f"talent:{talent_id}")
            if not data:
                logger.warning(f"No data found for talent {talent_id}")
                return None
            decoded_data = {key.decode('utf-8'): value.decode('utf-8') for key, value in data.items()}

            if cls.AVAILABLE_KEY not in decoded_data or cls.RATING_KEY not in decoded_data:
                logger.warning(f"Incomplete data for talent {talent_id}: {decoded_data}")
                return None

            converted_data = {
            'talent_id': decoded_data.get('talent_id', ''),
            'available': decoded_data.get(cls.AVAILABLE_KEY, 'False').lower() == 'true',
            'rating': float(decoded_data.get(cls.RATING_KEY, '0'))
        }

            return cls(**converted_data)

        except (ValueError, TypeError) as e:
            logger.error(f"Error converting Redis data for talent {talent_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading talent {talent_id}: {e}")
            return None

    def to_redis(self, redis_client: redis.Redis) -> bool:
        """
        Save the Talent object to Redis.

        Args:
            redis_client (redis.Redis): Redis client instance.

        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            redis_data = {
                self.AVAILABLE_KEY: str(self.available),
                self.RATING_KEY: str(self.rating),
                "talent_id": self.talent_id
            }
            redis_client.hset(f"talent:{self.talent_id}", mapping=redis_data)
            logger.info(f"Talent {self.talent_id} saved to Redis successfully.")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis error while saving talent {self.talent_id}: {e}")
            return False

    @classmethod
    def bulk_save(cls, redis_client: redis.Redis, talents: List['Talent']) -> int:
        """
        Save multiple Talent objects to Redis using a pipeline.

        Args:
            redis_client (redis.Redis): Redis client instance.
            talents (List[Talent]): List of Talent objects to save.

        Returns:
            int: The number of successfully saved talents.
        """
        success_count = 0
        try:
            with redis_client.pipeline() as pipe:
                for talent in talents:
                    pipe.hset(
                        f"talent:{talent.talent_id}",
                        mapping={
                            cls.AVAILABLE_KEY: str(talent.available),
                            cls.RATING_KEY: str(talent.rating),
                            "talent_id": talent.talent_id  # Include talent_id for completeness
                        }
                    )
                results = pipe.execute()
                success_count = sum(1 for result in results if result)
            logger.info(f"Successfully saved {success_count} talents to Redis.")
        except redis.RedisError as e:
            logger.error(f"Error bulk saving talents: {e}")
        return success_count