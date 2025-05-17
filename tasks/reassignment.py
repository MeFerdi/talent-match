from celery import Task, shared_task
from domain.services import MatchingService
from config.redis import get_redis
from domain.utils.logging import logger

@shared_task(bind=True, max_retries=3)
def reassign_task(self, task_id: str):
    redis = get_redis()
    try:
        task = Task.from_redis(redis, task_id)
        if not task or task.status != "reassigning":
            return False

        new_talent = MatchingService.get_next_available(task_id)
        if not new_talent:
            raise ValueError("No available talent")

        # Atomic reassignment
        with redis.pipeline() as pipe:
            pipe.hset(f"task:{task_id}", mapping={
                "assigned_to": new_talent,
                "claimed_at": datetime.now().isoformat(),
                "status": "assigned"
            })
            pipe.hset(f"talent:{new_talent}", "available", "false")
            pipe.execute()

        DeadlineService.set_initial_deadline(task_id)
        logger.info(f"Reassigned {task_id} to {new_talent}")
    except Exception as e:
        logger.error(f"Reassignment failed for {task_id}: {e}")
        self.retry(countdown=120)