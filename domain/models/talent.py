from pydantic import BaseModel, Field
from typing import Optional
import redis
from datetime import datetime
from domain.utils.logging import logger
import json

class Talent(BaseModel):
    talent_id: str = Field(..., min_length=1)
    available: bool = True
    rating: float = Field(ge=0, le=5)
    last_assigned_at: Optional[datetime] = None
    skills: list[str] = []

    @classmethod
    def from_redis(cls, redis_client: redis.Redis, talent_id: str) -> Optional["Talent"]:
        try:
            data = redis_client.hgetall(f"talent:{talent_id}")
            if not data:
                return None
            decoded = {k.decode() if isinstance(k, bytes) else k:
                   v.decode() if isinstance(v, bytes) else v
                   for k, v in data.items()}
            return cls(
                talent_id=talent_id,
                available=decoded.get("available", "true").lower() == "true",
                rating=float(decoded.get("rating", 0)),
                skills=json.loads(decoded.get("skills", "[]")),
                last_assigned_at=datetime.fromisoformat(decoded["last_assigned_at"]) if decoded.get("last_assigned_at") else None
            )
        except Exception as e:
            logger.error(f"Failed to load talent {talent_id}: {e}")
            return None

    def to_redis(self, redis_client: redis.Redis) -> bool:
        try:
            redis_client.hset(
                f"talent:{self.talent_id}",
                mapping={
                    "available": str(self.available).lower(),
                    "rating": str(self.rating),
                    "skills": json.dumps(self.skills),
                    "last_assigned_at": self.last_assigned_at.isoformat() if self.last_assigned_at else ""
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save talent {self.talent_id}: {e}")
            return False