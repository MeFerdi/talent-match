from celery import shared_task
from datetime import datetime
from config.redis import get_redis
from domain.models import Task
from tasks.reassignment import reassign_task

@shared_task(bind=True)
def check_deadline(self, task_id: str):
    redis = get_redis()
    task_data = redis.hgetall(f"task:{task_id}")
    task = Task(**task_data)
    
    if task.is_overdue():
        if not task.extensions:
            reassign_task.delay(task_id)