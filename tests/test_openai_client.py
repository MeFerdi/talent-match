import pytest
from unittest.mock import patch, MagicMock
from integrations.openai import OpenAIClient, ExtensionEvaluation
import json

@patch("openai.ChatCompletion.create")
def test_evaluate_extension_success(mock_create):
    """Test successful extension evaluation with valid response"""
    # Setup mock response
    mock_response = {
        "approved": True,
        "reason": "Valid reason",
        "confidence": 0.95
    }
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(mock_response)))]
    )
    
    client = OpenAIClient()
    test_reason = "Need more time to complete the task."
    
    # Execute
    result = client.evaluate_extension(request_context=test_reason)  # Pass as keyword argument
    
    # Verify
    assert result is not None
    assert isinstance(result, ExtensionEvaluation)
    assert result.approved is True
    assert result.reason == "Valid reason"
    assert result.confidence == 0.95

@patch("openai.ChatCompletion.create")
def test_evaluate_extension_invalid_response(mock_create):
    """Test handling of malformed API response"""
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({"invalid": "response"})))]
    )
    
    client = OpenAIClient()
    result = client.evaluate_extension(request_context="Test reason")  # Keyword argument
    assert result is None

@patch("openai.ChatCompletion.create")
def test_evaluate_extension_api_error(mock_create):
    """Test API failure handling"""
    mock_create.side_effect = Exception("API Error")
    client = OpenAIClient()
    result = client.evaluate_extension(request_context="Error test")  # Keyword argument
    assert result is None