from pydantic import BaseModel, Field, ValidationError
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import redis
from typing import Any

class Task(BaseModel):
    task_id: str = Field(..., min_length=3)
    assigned_to: Optional[str] = None
    claimed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str = "unassigned"
    extensions: List[Dict[str, Any]] = []
    matches: Dict[str, float] = Field(default_factory=dict)
    
    def is_overdue(self) -> bool:
        """Check if task has passed its deadline"""
        return self.deadline and datetime.now() > self.deadline
    
    def add_extension(self, reason: str) -> None:
        """Add an extension request to the task"""
        self.extensions.append({
            "timestamp": datetime.now(),
            "reason": reason,
            "approved": None
        })
    
    @classmethod
    def from_redis(cls, redis_client: redis.Redis, task_id: str) -> Optional['Task']:
        """Safely load a Task from Redis with proper error handling"""
        try:
            data = redis_client.hgetall(f"task:{task_id}")
            if not data:
                return None

            # Safely parse matches (avoid eval security risk)
            if 'matches' in data:
                try:
                    data['matches'] = {k: float(v) for k, v in json.loads(data['matches']).items()}
                except (json.JSONDecodeError, ValueError) as e:
                    raise ValueError(f"Invalid matches format: {e}")

            # Convert datetime fields
            datetime_fields = ['claimed_at', 'deadline']
            for field in datetime_fields:
                if data.get(field):
                    try:
                        data[field] = datetime.fromisoformat(data[field])
                    except ValueError as e:
                        raise ValueError(f"Invalid {field} format: {e}")

            return cls(**data)
            
        except Exception as e:
            # Log the error in production
            print(f"Error loading task from Redis: {e}")
            return None

    def to_redis(self, redis_client: redis.Redis) -> bool:
        """Save the task to Redis"""
        try:
            # Convert to Redis-safe format
            redis_data = self.model_dump()
            redis_data['matches'] = json.dumps(redis_data['matches'])
            
            # Convert datetime fields to ISO format
            for field in ['claimed_at', 'deadline']:
                if redis_data.get(field):
                    redis_data[field] = redis_data[field].isoformat()
            
            return redis_client.hset(
                f"task:{self.task_id}",
                mapping=redis_data
            )
        except Exception as e:
            print(f"Error saving task to Redis: {e}")
            return False