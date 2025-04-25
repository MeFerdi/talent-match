from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import redis
from domain.utils.logging import logger


class Task(BaseModel):
    """
    Represents a Task object with attributes for Redis storage and retrieval.
    """
    task_id: str = Field(..., min_length=3, description="Unique identifier for the task.")
    assigned_to: Optional[str] = None
    claimed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str = "unassigned"
    extensions: List[Dict[str, Any]] = []
    matches: Dict[str, float] = Field(default_factory=dict)

    def is_overdue(self) -> bool:
        """
        Check if the task has passed its deadline.

        Returns:
            bool: True if the task is overdue, False otherwise.
        """
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline

    def add_extension(self, reason: str) -> None:
        """
        Add an extension request to the task.

        Args:
            reason (str): The reason for the extension request.
        """
        self.extensions.append({
            "timestamp": datetime.now(),
            "reason": reason,
            "approved": None
        })

    @classmethod
    def from_redis(cls, redis_client: redis.Redis, task_id: str) -> Optional['Task']:
        """
        Load a Task object from Redis with proper error handling.

        Args:
            redis_client (redis.Redis): Redis client instance.
            task_id (str): The ID of the task to load.

        Returns:
            Optional[Task]: The Task object if found, otherwise None.
        """
        try:
            data = redis_client.hgetall(f"task:{task_id}")
            if not data:
                logger.warning(f"No data found for task_id: {task_id}")
                return None

            # Convert bytes to strings for Python 3
            decoded_data = {}
            for key, value in data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                decoded_data[key] = value

            # Safely parse matches
            if 'matches' in decoded_data:
                try:
                    decoded_data['matches'] = {k: float(v) for k, v in json.loads(decoded_data['matches']).items()}
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Invalid matches format for task {task_id}: {e}")
                    return None
            
            # Safely parse extensions
            if 'extensions' in decoded_data:
                try:
                    decoded_data['extensions'] = json.loads(decoded_data['extensions'])
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Invalid extensions format for task {task_id}: {e}")
                    return None

            # Convert datetime fields
            datetime_fields = ['claimed_at', 'deadline']
            for field in datetime_fields:
                if decoded_data.get(field):
                    try:
                        decoded_data[field] = datetime.fromisoformat(decoded_data[field])
                    except ValueError as e:
                        logger.error(f"Invalid {field} format for task {task_id}: {e}")
                        return None

            return cls(**decoded_data)

        except Exception as e:
            logger.error(f"Error loading task from Redis: {e}")
            return None

    def to_redis(self, redis_client: redis.Redis) -> bool:
        """
        Save the Task object to Redis.

        Args:
            redis_client (redis.Redis): Redis client instance.

        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            redis_data = self.model_dump()
            
            # Serialize matches
            redis_data['matches'] = json.dumps(redis_data['matches'])
            
            # Serialize extensions
            redis_data['extensions'] = json.dumps(self.extensions)

            # Convert datetime fields to ISO format strings
            for field in ['claimed_at', 'deadline']:
                if redis_data.get(field) is not None:
                    redis_data[field] = redis_data[field].isoformat()

            # Remove None values to avoid Redis errors
            redis_data = {k: v for k, v in redis_data.items() if v is not None}
            
            redis_client.hset(f"task:{self.task_id}", mapping=redis_data)
            logger.info(f"Task {self.task_id} saved to Redis successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving task {self.task_id} to Redis: {e}")
            return False