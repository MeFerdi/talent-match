from datetime import datetime, timedelta
from celery import shared_task
from domain.services import MatchingService
from config.redis import get_redis
from domain.utils.logging import logger

@shared_task(bind=True, max_retries=3)
def assign_task(self, task_id: str):
    redis = get_redis()
    try:
        talent_id = MatchingService.get_next_available(task_id)
        if not talent_id:
            raise ValueError("No available talent")

        now = datetime.now()
        due = now + timedelta(seconds=30)

        with redis.pipeline() as pipe:
            pipe.hset(f"task:{task_id}", mapping={
                "assigned_to": talent_id,
                "claimed_at": now.isoformat(),
                "status": "assigned",
                "deadline": due.isoformat(),
                "due_date": due.isoformat(),
                "extension_status": "none",
                "extension_requested_at": "",
                "extension_rejection_reason": "",
            })
            pipe.hset(f"talent:{talent_id}", "available", "false")
            pipe.execute()

        logger.info(f"Assigned {task_id} to {talent_id} with due date {due.isoformat()}")
    except Exception as e:
        logger.error(f"Assignment failed for {task_id}: {e}")
        self.retry(countdown=60)