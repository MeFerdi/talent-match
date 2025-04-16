import logging
from celery import shared_task
from domain.services.matching import MatchingService
from tasks.assignment import assign_task

@shared_task(bind=True)
def reassign_task(self, task_id: str):
    logger = logging.getLogger(__name__)
    logger.info(f"Reassigning task {task_id}")
    new_talent = MatchingService.get_next_available(task_id)
    if new_talent:
        logger.info(f"Task {task_id} reassigned to talent {new_talent}")
        assign_task.delay(task_id)
    else:
        logger.warning(f"No available talent to reassign task {task_id}")