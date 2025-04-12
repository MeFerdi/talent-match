from celery import shared_task
from domain.services import MatchingService
from tasks.assignment import assign_task

@shared_task(bind=True)
def reassign_task(self, task_id: str):
    new_talent = MatchingService.get_next_available(task_id)
    if new_talent:
        assign_task.delay(task_id)