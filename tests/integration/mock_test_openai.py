from unittest.mock import patch
import json
from integrations.openai import ExtensionEvaluation, OpenAIClient

def test_with_mock_responses():
    test_cases = [
        {
            "input": "Client needs more time",
            "mock_response": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "approved": True,
                            "reason": "Client request",
                            "confidence": 0.9
                        })
                    }
                }]
            },
            "expected": {
                "approved": True,
                "reason": "Client request",
                "confidence": 0.9
            }
        }
    ]
    
    client = OpenAIClient()
    
    for case in test_cases:
        with patch('openai.ChatCompletion.create') as mock_create:
            mock_create.return_value = case["mock_response"]
            result = client.evaluate_extension(case["input"])
            assert result == ExtensionEvaluation(**case["expected"])