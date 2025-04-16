import os
from celery import Celery
from domain.utils.security import validate_task_payload

app = Celery('talent-match')
app.config_from_object("config.settings", namespace="CELERY")
app.autodiscover_tasks(["tasks.assignment", "tasks.reassignment", "tasks.monitoring"])
app.conf.update(
    broker_url=os.getenv('REDIS_URL'),
    result_backend=os.getenv('REDIS_URL'),
    task_serializer='json',
    security_key=os.getenv('CELERY_SIGNING_KEY'),
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
    task_routes={
        'tasks.monitoring.*': {'queue': 'deadlines'},
        'tasks.reassignment.*': {'queue': 'matching'}
    }
)

@app.task(bind=True)
def validate_and_process_task(self, payload: dict):
    if not validate_task_payload(payload):
        raise ValueError("Invalid task payload")
    print(f"Processing task: {payload['task_id']}")