from celery import shared_task
from datetime import datetime
from config.redis import get_redis
from domain.models import Task
from tasks.reassignment import reassign_task
from domain.utils.logging import logger

@shared_task(bind=True)
def check_deadline(self, task_id: str):
    logger.info(f"Checking deadline for task_id: {task_id}")
    redis = get_redis()
    task_data = redis.hgetall(f"task:{task_id}")
    
    if not task_data:
        logger.warning(f"No data found for task_id: {task_id}")
        return

    task = Task(**task_data)
    
    if task.is_overdue():
        logger.info(f"Task {task_id} is overdue")
        if not task.extensions:
            logger.info(f"No extensions found for task {task_id}. Triggering reassignment.")
            reassign_task.delay(task_id)
        else:
            logger.info(f"Task {task_id} has extensions. No reassignment needed.")
    else:
        logger.info(f"Task {task_id} is not overdue")