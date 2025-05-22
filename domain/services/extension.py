import os
import google.generativeai as genai
from domain.models import Task
import json

from tasks.reassignment import reassign_task

class ExtensionService:
    @staticmethod
    def evaluate_request(task: Task, reason: str) -> dict:
        """Use Gemini API to evaluate extension requests and return decision and reason."""
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = f"""
        Evaluate this task extension request:
        - Task ID: {task.task_id}
        - Status: {task.status}
        - Reason: {reason}

        Respond ONLY with either "APPROVE" or "REJECT" and a short reason, as JSON:
        {{"decision": "APPROVE"|"REJECT", "reason": "short_reason"}}
        """

        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 30,
                }
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            result = json.loads(text)
            return {
                "approved": result.get("decision", "").upper() == "APPROVE",
                "reason": result.get("reason", "")
            }
        except Exception as e:
            print(f"Gemini API error: {e}")
            return {
                "approved": False,
                "reason": "AI evaluation failed"
            }
    @staticmethod
    def process_extension_decision(task, decision: str, reason: str, redis_client):
        task.extension_status = decision.lower()
        task.extension_rejection_reason = reason if decision.lower() == "rejected" else ""
        if decision.lower() == "rejected":
            task.status = "reassigning"
            task.to_redis(redis_client)
            reassign_task.delay(task.task_id)
        else:
            task.to_redis(redis_client)
        return task