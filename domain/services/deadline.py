from datetime import datetime, timedelta
from config.redis import get_redis
from domain.models import Task
from domain.utils.logging import logger
from integrations.gemini import GeminiAIClient
import json

class DeadlineService:
    @staticmethod
    def set_initial_deadline(task_id: str) -> bool:
        """Sets a 24-hour due_date and deadline when a task is assigned."""
        redis = get_redis()
        try:
            due = datetime.now() + timedelta(hours=24)
            redis.hset(
                f"task:{task_id}",
                mapping={
                    "deadline": due.isoformat(),
                    "due_date": due.isoformat()
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set deadline for {task_id}: {e}")
            return False

class ExtensionService:
    @staticmethod
    def request_extension(task_id: str, reason: str) -> bool:
        """Submits an extension request and updates task fields."""
        redis = get_redis()
        try:
            now = datetime.now()
            redis.hset(
                f"task:{task_id}",
                mapping={
                    "extension_status": "pending",
                    "extension_requested_at": now.isoformat(),
                    "status": "extension_requested"
                }
            )
            # Optionally, keeping history of extension requests
            extensions = redis.hget(f"task:{task_id}", "extensions")
            extensions_list = json.loads(extensions) if extensions else []
            extensions_list.append({
                "requested_at": now.isoformat(),
                "reason": reason,
                "approved": None
            })
            redis.hset(f"task:{task_id}", "extensions", json.dumps(extensions_list))
            return True
        except Exception as e:
            logger.error(f"Extension request failed for {task_id}: {e}")
            return False

    @staticmethod
    def evaluate_extension(task_id: str) -> bool:
        """Uses Gemini AI to approve/reject the latest extension request."""
        redis = get_redis()
        try:
            extensions = redis.hget(f"task:{task_id}", "extensions")
            extensions_list = json.loads(extensions) if extensions else []
            if not extensions_list:
                return False
            latest_req = extensions_list[-1]

            ai_client = GeminiAIClient()
            evaluation = ai_client.evaluate_extension(latest_req["reason"])

            now = datetime.now()
            if evaluation.approved:
                # Extend due_date and deadline by 24h
                new_due = now + timedelta(hours=24)
                redis.hset(
                    f"task:{task_id}",
                    mapping={
                        "status": "assigned",
                        "due_date": new_due.isoformat(),
                        "deadline": new_due.isoformat(),
                        "extension_status": "approved",
                        "extension_requested_at": now.isoformat(),
                        "extension_rejection_reason": ""
                    }
                )
                latest_req["approved"] = True
            else:
                redis.hset(
                    f"task:{task_id}",
                    mapping={
                        "extension_status": "rejected",
                        "extension_rejection_reason": evaluation.reason or "Rejected by AI",
                        "status": "reassigning"
                    }
                )
                latest_req["approved"] = False
                latest_req["rejection_reason"] = evaluation.reason or "Rejected by AI"

            # Update extensions history
            extensions_list[-1] = latest_req
            redis.hset(f"task:{task_id}", "extensions", json.dumps(extensions_list))

            return True
        except Exception as e:
            logger.error(f"AI extension evaluation failed for {task_id}: {e}")
            return False