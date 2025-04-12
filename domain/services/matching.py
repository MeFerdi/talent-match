from config.redis import get_redis
from domain.models import Task, Talent
from typing import Optional
from domain.utils.logging import logger

class MatchingService:
    @staticmethod
    def get_next_available(task_id: str) -> Optional[str]:
        """Get next best available talent"""
        try:
            redis = get_redis()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None

        # Load the task
        try:
            task = Task.from_redis(redis, task_id)
        except Exception as e:
            logger.error(f"Failed to load task {task_id} from Redis: {e}")
            return None

        if not task or not task.matches:
            logger.info(f"No matches found for task {task_id}")
            return None

        # Check talents in score order
        for talent_id, score in sorted(task.matches.items(), key=lambda x: -x[1]):  # Descending
            try:
                talent = Talent.from_redis(redis, talent_id)
            except Exception as e:
                logger.error(f"Failed to load talent {talent_id} from Redis: {e}")
                continue

            if talent and talent.available:
                logger.info(f"Found available talent {talent_id} for task {task_id}")
                return talent_id

        logger.info(f"No available talents found for task {task_id}")
        return None