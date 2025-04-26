import os
import google.generativeai as genai
from domain.models import Task

class ExtensionService:
    @staticmethod
    def evaluate_request(task: Task, reason: str) -> bool:
        """Use Gemini API to evaluate extension requests"""
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        Evaluate this task extension request:
        - Task ID: {task.task_id}
        - Status: {task.status}
        - Reason: {reason}

        Respond ONLY with either "APPROVE" or "REJECT".
        """
        
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 10,
                }
            )
            
            result = response.text.strip().upper()
            return "APPROVE" in result
        
        except Exception as e:
            print(f"Gemini API error: {e}")
            return False