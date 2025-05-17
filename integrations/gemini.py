import json
import os
import google.generativeai as genai
from datetime import datetime, timedelta
from domain.utils.logging import logger
from domain.utils.decorators import retry, validate_input
from pydantic import BaseModel
from typing import Optional, Dict
from functools import lru_cache
import redis

class ExtensionEvaluation(BaseModel):
    approved: bool
    reason: str
    confidence: float

class GeminiAIClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiAIClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables!")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.timeout = int(os.getenv("GEMINI_TIMEOUT", "30"))
        self.redis = redis.Redis.from_url(os.getenv('REDIS_URL'))
        self.cache_ttl = timedelta(hours=1)
        logger.info("Gemini AI client initialized successfully")

    @retry(max_retries=3, backoff_factor=1.5)
    @validate_input
    def evaluate_extension(self, request_context: str) -> Optional[ExtensionEvaluation]:
        """Evaluate extension request using Gemini API with caching"""
        cache_key = f"gemini:eval:{hash(request_context)}"
        
        # Check cache first
        cached = self._get_cached_evaluation(cache_key)
        if cached:
            return cached
            
        try:
            # Build structured prompt
            prompt = self._build_evaluation_prompt(request_context)
            
            # Get AI response
            response = self._get_ai_response(prompt)
            
            # Parse and validate response
            result = self._parse_ai_response(response)
            evaluation = ExtensionEvaluation(**result)
            
            # Cache successful evaluation
            self._cache_evaluation(cache_key, evaluation)
            
            return evaluation
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return None
        except genai.types.GenerativeAIError as e:
            logger.error(f"Gemini API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in evaluation: {e}")
            return None

    def _build_evaluation_prompt(self, context: str) -> str:
        """Construct the evaluation prompt with clear instructions"""
        return f"""
        You are a task management AI evaluating extension requests.
        Analyze this request carefully:

        CONTEXT:
        {context}

        Provide JSON response with these exact fields:
        - "approved" (boolean): Should this request be approved?
        - "reason" (string): Short justification (1-2 sentences)
        - "confidence" (float 0-1): Your confidence in this decision

        Guidelines:
        1. Approve only for valid reasons (illness, technical issues)
        2. Reject vague requests ("need more time")
        3. Confidence must reflect certainty

        Respond ONLY with valid JSON:
        {{
            "approved": true|false,
            "reason": "your_reason",
            "confidence": 0.95
        }}
        """

    def _get_ai_response(self, prompt: str):
        """Get response from Gemini with error handling"""
        return self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 200,
                "top_p": 0.95
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )

    def _parse_ai_response(self, response) -> Dict:
        """Parse and validate the AI response"""
        response_text = response.text.strip()
        
        # Handle code block responses
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        
        result = json.loads(response_text)
        
        # Validate required fields
        if not all(k in result for k in ["approved", "reason", "confidence"]):
            raise ValueError("Missing required fields in response")
            
        if not isinstance(result["approved"], bool):
            raise ValueError("Approved field must be boolean")
            
        if not 0 <= result["confidence"] <= 1:
            raise ValueError("Confidence must be between 0 and 1")
            
        return result

    def _cache_evaluation(self, key: str, evaluation: ExtensionEvaluation):
        """Cache the evaluation result in Redis"""
        try:
            self.redis.setex(
                key,
                self.cache_ttl,
                json.dumps(evaluation.model_dump())
            )
        except redis.RedisError as e:
            logger.warning(f"Failed to cache evaluation: {e}")

    def _get_cached_evaluation(self, key: str) -> Optional[ExtensionEvaluation]:
        """Retrieve cached evaluation if available"""
        try:
            cached = self.redis.get(key)
            if cached:
                return ExtensionEvaluation(**json.loads(cached))
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read cached evaluation: {e}")
        return None

    @staticmethod
    def get_fallback_evaluation() -> ExtensionEvaluation:
        """Provide a default response when AI fails"""
        return ExtensionEvaluation(
            approved=False,
            reason="System could not process request",
            confidence=0.0
        )