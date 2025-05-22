from celery import shared_task
from datetime import datetime
from config.redis import get_redis
from domain.models import Task
from domain.utils.logging import logger
from tasks.reassignment import reassign_task
from integrations.gemini import evaluate_extension

@shared_task
def check_deadlines():
    redis = get_redis()
    now = datetime.now()
    expired_tasks = redis.zrangebyscore(
        "assignments:active",
        0,
        now.timestamp()
    )

    for task_id in expired_tasks:
        task_id_str = task_id.decode() if isinstance(task_id, bytes) else task_id
        task = Task.from_redis(redis, task_id_str)
        if not task:
            logger.warning(f"Task {task_id_str} not found in Redis.")
            continue

        # If extension is pending, evaluate it
        if task.extension_status == "pending":
            logger.info(f"Evaluating extension for overdue task {task_id_str}")
            evaluate_extension.delay(task_id_str)
        # If extension is rejected or no extension, reassign
        elif task.status == "assigned" or task.extension_status == "rejected":
            logger.info(f"Reassigning overdue task {task_id_str}")
            reassign_task.delay(task_id_str)
        else:
            logger.info(f"No action needed for task {task_id_str} with status {task.status} and extension_status {task.extension_status}")