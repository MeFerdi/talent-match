from celery import shared_task
from datetime import datetime
from config.redis import get_redis
from domain.models import Task
from domain.utils.logging import logger
from integrations.gemini import GeminiAIClient
from tasks.reassignment import reassign_task
from tasks.evaluation import evaluate_extension_task

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
            evaluate_extension_task.delay(task_id_str)
        elif task.status == "rejected" or (task.status == "assigned" and task.is_overdue()):
            logger.info(f"Setting task {task_id_str} to reassigning")
            task.status = "reassigning"
            task.to_redis(redis)
            reassign_task.delay(task_id_str)
        else:
            logger.info(f"No action needed for task {task_id_str} with status {task.status} and extension_status {task.extension_status}")

@shared_task
def evaluate_extension_task(task_id: str):
    ai_client = GeminiAIClient()
    ai_client.evaluate_extension(task_id)