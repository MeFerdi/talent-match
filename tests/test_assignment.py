from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock
from tasks.assignment import assign_task

@patch("tasks.assignment.get_redis")
@patch("tasks.assignment.MatchingService.get_next_available")
@patch("tasks.assignment.Task")
@patch("tasks.assignment.datetime")
def test_assign_task(mock_datetime, mock_task, mock_get_next_available, mock_get_redis):
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis
    mock_get_next_available.return_value = "talent_123"

    # Mock datetime.now()
    fixed_datetime = datetime(2025, 4, 12, 16, 33, 3, 974639)
    mock_datetime.now.return_value = fixed_datetime

    # Mock Task
    mock_task_instance = MagicMock()
    mock_task.return_value = mock_task_instance
    mock_task_instance.model_dump_json.return_value = '{"task_id": "task_123", "assigned_to": "talent_123", "claimed_at": "2025-04-12T16:33:03.974639"}'

    task_id = "task_123"

    # Act
    assign_task(task_id=task_id)

    # Assert
    mock_get_next_available.assert_called_once_with(task_id)
    mock_task.assert_called_once_with(
        task_id=task_id,
        assigned_to="talent_123",
        claimed_at=fixed_datetime
    )
    mock_redis.hset.assert_called_once_with(
        f"task:{task_id}",
        '{"task_id": "task_123", "assigned_to": "talent_123", "claimed_at": "2025-04-12T16:33:03.974639"}'
    )