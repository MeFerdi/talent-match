import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timedelta

from domain.models.task import Task
from domain.services.deadline import ExtensionService
from tasks.assignment import assign_task
from tasks.reassignment import reassign_task
from integrations.redis_events import RedisEventStream
import redis

app = FastAPI(title="Talent Match API")

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
event_stream = RedisEventStream()

# --- Pydantic Schemas for API ---
class TaskCreate(BaseModel):
    description: str
    matches: Dict[str, float]

class ExtensionRequest(BaseModel):
    reason: str

class ExtensionProcess(BaseModel):
    status: str  # "approved" or "rejected"
    reason: Optional[str] = None

@app.post("/tasks", response_model=Task)
def create_task(payload: TaskCreate):
    # Generating a new task_id (for demo, use timestamp)
    task_id = f"task_{int(datetime.now().timestamp())}"
    task = Task(
        task_id=task_id,
        status="unassigned",
        matches=payload.matches,
        extensions=[],
        deadline=datetime.now() + timedelta(hours=24),
        due_date=datetime.now() + timedelta(hours=24)
    )
    task.to_redis(redis_client)
    # Ensuring automatic assignment by triggering the Celery assignment task immediately
    assign_task.delay(task_id)
    event_stream.publish("tasks", {"event": "created", "task_id": task_id})
    return Task.from_redis(redis_client, task_id)  # Return the latest state (may still be unassigned if Celery is async)

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = Task.from_redis(redis_client, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks/{task_id}/request-extension")
def request_extension(task_id: str, req: ExtensionRequest):
    ok = ExtensionService.request_extension(task_id, req.reason)
    if not ok:
        raise HTTPException(status_code=400, detail="Extension request failed")
    event_stream.publish("tasks", {"event": "extension_requested", "task_id": task_id})
    return {"status": "pending"}

@app.post("/tasks/{task_id}/process-extension")
def process_extension(task_id: str, req: ExtensionProcess):
    # updating fields directly
    task = Task.from_redis(redis_client, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.extension_status = req.status
    if req.status == "rejected":
        task.extension_rejection_reason = req.reason or "Rejected"
    else:
        task.extension_rejection_reason = ""
        # Optionally extend deadline
        task.deadline = datetime.now() + timedelta(hours=24)
        task.due_date = task.deadline
    task.to_redis(redis_client)
    event_stream.publish("tasks", {"event": "extension_processed", "task_id": task_id, "status": req.status})
    return {"extension_status": req.status}

@app.post("/cron/reassign-tasks")
def trigger_reassignment():
    reassign_task.delay("task_id_placeholder")
    event_stream.publish("tasks", {"event": "reassignment_triggered"})
    return {"status": "reassignment triggered"}

@app.post("/tasks/{task_id}/complete")
def complete_task(task_id: str):
    task = Task.from_redis(redis_client, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.extension_status == "rejected":
        raise HTTPException(status_code=400, detail="Cannot complete while extension is rejected.")
    task.status = "completed"
    task.to_redis(redis_client)
    event_stream.publish("tasks", {"event": "completed", "task_id": task_id})
    return {"status": "completed"}
# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}