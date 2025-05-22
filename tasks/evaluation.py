from celery import shared_task
from config.redis import get_redis
from domain.models import Task
from domain.services.extension import ExtensionService

@shared_task
def evaluate_extension_task(task_id: str):
    redis = get_redis()
    task = Task.from_redis(redis, task_id)
    if not task:
        return
    reason = ""
    if task.extensions and isinstance(task.extensions, list):
        reason = task.extensions[-1].get("reason", "")
    result = ExtensionService.evaluate_request(task, reason)