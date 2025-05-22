from datetime import datetime
import json
from typing import Dict, List, Optional
from venv import logger

from pydantic import BaseModel
import redis

class Task(BaseModel):
    task_id: str
    assigned_to: Optional[str] = None
    claimed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str = "unassigned"
    extensions: List[Dict] = []
    matches: Dict[str, float] = {}
    due_date: Optional[datetime] = None
    extension_status: str = "none"  # "none", "pending", "approved", "rejected"
    extension_requested_at: Optional[datetime] = None
    extension_rejection_reason: Optional[str] = None

    def is_overdue(self) -> bool:
        # Use due_date if present, fallback to deadline for backward compatibility
        check_date = self.due_date or self.deadline
        return check_date and datetime.now() > check_date

    def has_requested_extension(self) -> bool:
        """Return True if any extension requests exist for this task."""
        return self.extension_status in ("pending", "approved", "rejected")

    @classmethod
    def from_redis(cls, redis_client: redis.Redis, task_id: str) -> Optional["Task"]:
        try:
            data = redis_client.hgetall(f"task:{task_id}")
            if not data:
                return None
            decoded = {k.decode() if isinstance(k, bytes) else k:
                       v.decode() if isinstance(v, bytes) else v
                       for k, v in data.items()}
            return cls(
                task_id=task_id,
                assigned_to=decoded.get("assigned_to"),
                claimed_at=datetime.fromisoformat(decoded["claimed_at"]) if decoded.get("claimed_at") else None,
                deadline=datetime.fromisoformat(decoded["deadline"]) if decoded.get("deadline") else None,
                status=decoded.get("status", "unassigned"),
                extensions=json.loads(decoded.get("extensions", "[]")),
                matches=json.loads(decoded.get("matches", "{}")),
                due_date=datetime.fromisoformat(decoded["due_date"]) if decoded.get("due_date") else None,
                extension_status=decoded.get("extension_status", "none"),
                extension_requested_at=datetime.fromisoformat(decoded["extension_requested_at"]) if decoded.get("extension_requested_at") else None,
                extension_rejection_reason=decoded.get("extension_rejection_reason")
            )
        except Exception as e:
            logger.error(f"Failed to load task {task_id}: {e}")
            return None

    def to_redis(self, redis_client: redis.Redis) -> bool:
        try:
            redis_client.hset(
                f"task:{self.task_id}",
                mapping={
                    "assigned_to": self.assigned_to or "",
                    "claimed_at": self.claimed_at.isoformat() if self.claimed_at else "",
                    "deadline": self.deadline.isoformat() if self.deadline else "",
                    "status": self.status,
                    "extensions": json.dumps(self.extensions),
                    "matches": json.dumps(self.matches),
                    "due_date": self.due_date.isoformat() if self.due_date else "",
                    "extension_status": self.extension_status,
                    "extension_requested_at": self.extension_requested_at.isoformat() if self.extension_requested_at else "",
                    "extension_rejection_reason": self.extension_rejection_reason or ""
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save task {self.task_id}: {e}")
            return False