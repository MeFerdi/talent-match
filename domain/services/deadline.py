from datetime import datetime, timedelta
from domain.models import Task

class DeadlineService:
    @staticmethod
    def set_initial_deadline(task: Task) -> Task:
        task.deadline = datetime.now() + timedelta(hours=24)
        return task