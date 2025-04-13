"""
Talent Match - Integration Modules

This package contains all external service integrations (OpenAI, Slack, Redis, etc.)
"""

from .openai import OpenAIClient, ExtensionEvaluation
from .redis_events import RedisEventStream
from .mock.slack import MockSlackClient

__all__ = [
    'OpenAIClient',
    'ExtensionEvaluation', 
    'RedisEventStream',
    'MockSlackClient',
    'MockOpenAIClient'
]

# Package version
__version__ = '0.1.0'