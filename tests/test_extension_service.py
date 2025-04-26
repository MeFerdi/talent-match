import pytest
from unittest.mock import patch, MagicMock
from domain.services.extension import ExtensionService
from domain.models import Task

@pytest.fixture(autouse=True)
def mock_gemini():
    with patch("google.generativeai.GenerativeModel") as mock_model:
        mock_response = MagicMock()
        mock_response.text = "APPROVE"
        mock_model.return_value.generate_content.return_value = mock_response
        yield mock_model

def test_evaluate_request_approve(mock_gemini):
    mock_gemini.return_value.generate_content.return_value.text = "APPROVE"
    task = Task(task_id="task_123")
    reason = "Need more time to complete the task."

    result = ExtensionService.evaluate_request(task, reason)

    assert result is True
    mock_gemini.return_value.generate_content.assert_called_once()
    
    args, kwargs = mock_gemini.return_value.generate_content.call_args
    prompt = args[0]
    

    assert task.task_id in prompt
    assert reason in prompt
    assert "APPROVE" in prompt or "approve" in prompt.lower()
    assert "REJECT" in prompt or "reject" in prompt.lower()
    assert kwargs["generation_config"]["temperature"] == 0.3
    assert kwargs["generation_config"]["max_output_tokens"] == 10

def test_evaluate_request_reject(mock_gemini):
    mock_gemini.return_value.generate_content.return_value.text = "REJECT"
    task = Task(task_id="task_123")
    reason = "Need more time to complete the task."

    result = ExtensionService.evaluate_request(task, reason)

    assert result is False
    mock_gemini.return_value.generate_content.assert_called_once()
    
    args, kwargs = mock_gemini.return_value.generate_content.call_args
    prompt = args[0]
    
    assert task.task_id in prompt
    assert reason in prompt
    assert "APPROVE" in prompt or "approve" in prompt.lower()
    assert "REJECT" in prompt or "reject" in prompt.lower()
    assert kwargs["generation_config"]["temperature"] == 0.3
    assert kwargs["generation_config"]["max_output_tokens"] == 10