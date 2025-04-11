import os
from celery import Celery
# from .security import validate_task_payload

app = Celery('talent-match')
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