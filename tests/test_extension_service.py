import pytest
from unittest.mock import patch, MagicMock
from domain.services.extension import ExtensionService
from domain.models import Task

@patch("domain.services.extension.openai.ChatCompletion.create")
def test_evaluate_request_approve(mock_openai_create):
    # Arrange
    mock_openai_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="APPROVE"))]
    )
    task = Task(task_id="task_123")
    reason = "Need more time to complete the task."

    # Act
    result = ExtensionService.evaluate_requesst(task, reason)

    # Assert
    assert result is True
    mock_openai_create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Evaluate task extension requests. Respond only with APPROVE or REJECT."
            },
            {
                "role": "user",
                "content": f"Reason: {reason}\nTask ID: {task.task_id}"
            }
        ],
        temperature=0.3
    )

@patch("domain.services.extension.openai.ChatCompletion.create")
def test_evaluate_request_reject(mock_openai_create):
    # Arrange
    mock_openai_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="REJECT"))]
    )
    task = Task(task_id="task_123")
    reason = "Need more time to complete the task."

    # Act
    result = ExtensionService.evaluate_requesst(task, reason)

    # Assert
    assert result is False
    mock_openai_create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Evaluate task extension requests. Respond only with APPROVE or REJECT."
            },
            {
                "role": "user",
                "content": f"Reason: {reason}\nTask ID: {task.task_id}"
            }
        ],
        temperature=0.3
    )