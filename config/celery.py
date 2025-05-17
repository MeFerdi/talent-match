import os
from celery import Celery
from celery.schedules import crontab
from domain.utils.security import validate_task_payload
from datetime import timedelta

app = Celery('talent-match')
app.config_from_object("config.settings", namespace="CELERY")

# Autodiscover all task modules
app.autodiscover_tasks([
    "tasks.assignment",
    "tasks.reassignment", 
    "tasks.monitoring",
    "tasks.extensions"
])

app.conf.update(
    # Broker and backend configuration
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Serialization and security
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    security_key=os.getenv('CELERY_SIGNING_KEY'),
    
    # Reliability settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,  # Prevent task pile-up
    
    # Queue routing
    task_routes={
        'tasks.monitoring.*': {'queue': 'monitoring'},
        'tasks.reassignment.*': {'queue': 'matching', 'priority': 5},
        'tasks.assignment.*': {'queue': 'matching', 'priority': 3},
        'tasks.extensions.*': {'queue': 'extensions'}
    },
    
    # Scheduled tasks
    beat_schedule={
        # Check for tasks needing reassignment every 10 minutes
        'check-expired-assignments': {
            'task': 'tasks.reassignment.check_expired_assignments',
            'schedule': crontab(minute='*/10'),
            'options': {'queue': 'monitoring'}
        },
        
        # Monitor system health every 5 minutes
        'monitor-system-health': {
            'task': 'tasks.monitoring.check_system_health',
            'schedule': crontab(minute='*/5'),
            'options': {'queue': 'monitoring'}
        },
        
        # Process pending extensions every hour
        'process-pending-extensions': {
            'task': 'tasks.extensions.process_pending',
            'schedule': crontab(minute=0, hour='*/1'),
            'options': {'queue': 'extensions'}
        },
        
        # Retry failed assignments every 15 minutes
        'retry-failed-assignments': {
            'task': 'tasks.assignment.retry_failed',
            'schedule': timedelta(minutes=15),
            'options': {'queue': 'matching'}
        }
    }
)

# Task with enhanced validation and error handling
@app.task(
    bind=True,
    autoretry_for=(ValueError,),
    retry_backoff=30,
    retry_kwargs={'max_retries': 3},
    time_limit=120,
    soft_time_limit=90
)
def validate_and_process_task(self, payload: dict):
    """Validates and processes task payload with retry logic"""
    if not validate_task_payload(payload):
        self.retry(exc=ValueError("Invalid task payload"))
    
    try:
        task_id = payload['task_id']
        logger.info(f"Processing task: {task_id}")
        
        # Additional processing logic here
        return {"status": "success", "task_id": task_id}
        
    except Exception as e:
        logger.error(f"Task processing failed: {str(e)}")
        raise self.retry(exc=e)