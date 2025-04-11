from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Dict

class Task(BaseModel):
    task_id: str = Field(..., min_length=3)
    assigned_to: str | None = None
    claimed_at: datetime | None = None
    deadline: datetime | None = None
    status: str = "unassigned"
    extensions: List[Dict] = []
    
    def is_overdue(self) -> bool:
        return self.deadline and datetime.now() > self.deadline
    
    def add_extension(self, reason: str):
        self.extensions.append({
            "timestamp": datetime.now(),
            "reason": reason,
            "approved": None
        })