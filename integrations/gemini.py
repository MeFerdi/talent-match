import json
import os
import google.generativeai as genai
from domain.utils.logging import logger
from domain.utils.decorators import retry, validate_input
from pydantic import BaseModel
from typing import Optional

class ExtensionEvaluation(BaseModel):
    approved: bool
    reason: str
    confidence: float

class GeminiAIClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables!")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.timeout = int(os.getenv("GEMINI_TIMEOUT", "30"))
        logger.info("Gemini AI client initialized successfully")

    @retry(max_retries=3)
    @validate_input
    def evaluate_extension(self, request_context: str) -> Optional[ExtensionEvaluation]:
        """Evaluate extension request using Gemini API"""
        
        try:
            prompt = f"""
            Analyze this task extension request and provide a JSON response with:
            - "approved" (boolean): Whether to approve the request
            - "reason" (string): Brief justification
            - "confidence" (float 0-1): Your confidence in this decision

            Request Context:
            {request_context}

            Respond ONLY with valid JSON in this exact format:
            {{
                "approved": true|false,
                "reason": "your_reason_here",
                "confidence": 0.95
            }}
            """

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 200,
                }
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            
            result = json.loads(response_text)
            return ExtensionEvaluation(**result)

        except Exception as e:
            logger.error(f"Gemini evaluation failed: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Gemini response: {e.response.text}")
            return None