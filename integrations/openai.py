import json
import openai
import os
from typing import Optional
from domain.utils.logging import logger
from domain.utils.decorators import retry, validate_input
from pydantic import BaseModel

class ExtensionEvaluation(BaseModel):
    approved: bool
    reason: str
    confidence: float

class OpenAIClient:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    @retry(max_retries=3)
    @validate_input
    def evaluate_extension(self, request_context: str) -> Optional[ExtensionEvaluation]:
        if not isinstance(request_context, str):
            raise TypeError(f"request_context must be a string, got {type(request_context).__name__}")
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Evaluate task extension requests. Respond with JSON containing 'approved', 'reason', and 'confidence' fields."
                    },
                    {
                        "role": "user",
                        "content": request_context
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return ExtensionEvaluation(**result)
            
        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {e}")
            return None