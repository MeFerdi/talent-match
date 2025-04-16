import openai
from domain.models import Task

class ExtensionService:
    @staticmethod
    def evaluate_requesst(task: Task, reason: str) -> bool:
        """Use OpenAI to evaluate extension requests"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Evaluate task extension requests. Respond only with APPROVE or REJECT."
            }, {
                "role": "user",
                "content": f"Reason: {reason}\nTask ID: {task.task_id}"
            }],
            temperature=0.3
        )
        return "APPROVE" in response.choices[0].message.content