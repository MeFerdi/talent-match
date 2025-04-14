from datetime import time
import json
import os
from typing import Optional
import requests
from domain.utils.logging import logger
from domain.utils.decorators import retry, validate_input
from pydantic import BaseModel

class ExtensionEvaluation(BaseModel):
    approved: bool
    reason: str
    confidence: float

class LocalAIClient:
    def __init__(self):
        self.base_url = os.getenv("LOCAL_AI_URL", "http://localhost:11434")
        self.model = os.getenv("LOCAL_AI_MODEL", "mistral")
        self.timeout = int(os.getenv("LOCAL_AI_TIMEOUT", "30"))
        
        # Verify connection on startup
        self._verify_connection()

    def _verify_connection(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if not resp.ok:
                raise ConnectionError(f"Ollama server error: {resp.text}")
            logger.info(f"Connected to local AI model: {self.model}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to local AI: {e}")
            raise ConnectionError(f"Failed to connect to local AI: {e}")

    @retry(max_retries=3)
    @validate_input
    def evaluate_extension(self, request_context: str) -> Optional[ExtensionEvaluation]:
        """Evaluate extension request using local LLM"""
        
        try:
            prompt = f"""
            [SYSTEM] Evaluate this task extension request. 
            Respond ONLY with valid JSON containing these fields:
            - "approved" (boolean)
            - "reason" (string)
            - "confidence" (float between 0-1)

            [REQUEST] {request_context}

            [RESPONSE] 
            """

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "options": {"temperature": 0.3}
                },
                timeout=self.timeout
            )
            response.raise_for_status()

        
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")

            result = json.loads(full_response)
            return ExtensionEvaluation(**result)

        except requests.exceptions.RequestException as e:
            logger.error(f"Local AI evaluation failed: {e}")
            logger.error(f"Local AI evaluation failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}\nResponse: {full_response}")
            return None
        except Exception as e:
            logger.error(f"Local AI evaluation failed: {e}")
            return None