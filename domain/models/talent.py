from pydantic import BaseModel, Field, ValidationError
from typing import Optional
import redis
import json

class Talent(BaseModel):
    talent_id: str = Field(..., min_length=1)
    available: bool = True
    rating: float = Field(ge=0, le=5)  # Rating between 0-5
    
    @classmethod
    def from_redis(cls, redis_client: redis.Redis, talent_id: str) -> Optional['Talent']:
        """Safely load Talent from Redis with comprehensive error handling"""
        try:
            data = redis_client.hgetall(f"talent:{talent_id}")
            if not data:
                return None

            # Convert Redis string values to proper types
            converted_data = {
                'talent_id': talent_id,
                'available': data.get('available', 'False').lower() == 'true',
                'rating': float(data.get('rating', 0))
            }

            return cls(**converted_data)
            
        except (ValueError, TypeError) as e:
            print(f"Error converting Redis data for talent {talent_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error loading talent {talent_id}: {e}")
            return None

    def to_redis(self, redis_client: redis.Redis) -> bool:
        """Save talent data to Redis atomically"""
        try:
            redis_data = {
                'available': str(self.available),
                'rating': str(self.rating)
            }
            return redis_client.hset(
                f"talent:{self.talent_id}",
                mapping=redis_data
            )
        except Exception as e:
            print(f"Error saving talent {self.talent_id} to Redis: {e}")
            return False

    @classmethod
    def bulk_save(cls, redis_client: redis.Redis, talents: list['Talent']) -> int:
        """Save multiple talents efficiently using pipeline"""
        try:
            with redis_client.pipeline() as pipe:
                for talent in talents:
                    pipe.hset(
                        f"talent:{talent.talent_id}",
                        mapping={
                            'available': str(talent.available),
                            'rating': str(talent.rating)
                        }
                    )
                return len(pipe.execute())
        except Exception as e:
            print(f"Error bulk saving talents: {e}")
            return 0