from celery import shared_task
from config.redis import get_redis
from domain.models import Task
from domain.services import MatchingService
from datetime import datetime
from domain.utils.logging import logger

@shared_task(bind=True)
def assign_task(self, task_id: str):
    logger.info(f"Starting task assignment for task_id: {task_id}")
    redis = get_redis()
    talent_id = MatchingService.get_next_available(task_id)
    
    if talent_id:
        task = Task(
            task_id=task_id,
            assigned_to=talent_id,
            claimed_at=datetime.now()
        )
        redis.hset(f"task:{task_id}", task.model_dump_json())
        logger.info(f"Task {task_id} successfully assigned to talent {talent_id}")
    else:
        logger.warning(f"No available talent found for task {task_id}")