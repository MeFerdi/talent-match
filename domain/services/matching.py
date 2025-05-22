from config.redis import get_redis
from domain.models import Talent, Task
from typing import Optional
from domain.utils.logging import logger

class MatchingService:
    @staticmethod
    def get_next_available(task_id: str) -> Optional[str]:
        """Finds the best available talent for a task (atomic operation)."""
        redis = get_redis()
        try:
            task = Task.from_redis(redis, task_id)
            if not task or not task.matches:
                return None

            # Check talents in descending match score order
            for talent_id, _ in sorted(task.matches.items(), key=lambda x: -x[1]):
                talent = Talent.from_redis(redis, talent_id)
                if talent and talent.available:
                    # Atomic lock to prevent race conditions
                    with redis.lock(f"talent:{talent_id}:lock", timeout=5):
                        if talent.available:
                            redis.hset(f"talent:{talent_id}", "available", "false")
                            return talent_id
            return None
        except Exception as e:
            logger.error(f"Matching failed for {task_id}: {e}")
            return None
    @staticmethod
    def get_best_match(task: Task) -> Optional[str]:
        """Returns the talent_id with the highest match score for the given task."""
        if not task or not task.matches:
            return None
        # Return the talent_id with the highest score
        return max(task.matches, key=task.matches.get)