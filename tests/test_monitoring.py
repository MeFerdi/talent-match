import pytest
from unittest.mock import patch, MagicMock
from tasks.monitoring import check_deadline
from domain.models import Task

@patch("tasks.monitoring.get_redis")
@patch("tasks.monitoring.reassign_task")
@patch("tasks.monitoring.logger")
def test_check_deadline_task_not_found(mock_logger, mock_reassign_task, mock_get_redis):

    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {}
    mock_get_redis.return_value = mock_redis

    check_deadline(task_id="task_123")

    mock_logger.warning.assert_called_once_with("No data found for task_id: task_123")
    mock_reassign_task.delay.assert_not_called()


@patch("tasks.monitoring.get_redis")
@patch("tasks.monitoring.reassign_task")
@patch("tasks.monitoring.logger")
def test_check_deadline_task_not_overdue(mock_logger, mock_reassign_task, mock_get_redis):
    # Mock Redis to return task data
    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {
        "task_id": "task_123",
        "assigned_to": "talent_1",
        "claimed_at": "2025-04-15T10:00:00",
        "deadline": "2025-04-20T10:00:00",
        "extensions": "[]",
    }
    mock_get_redis.return_value = mock_redis

    with patch("tasks.monitoring.Task") as MockTask:
        mock_task = MagicMock()
        mock_task.is_overdue.return_value = False
        MockTask.return_value = mock_task

        check_deadline(task_id="task_123")

        mock_logger.info.assert_any_call("Task task_123 is not overdue")
        mock_reassign_task.delay.assert_not_called()


@patch("tasks.monitoring.get_redis")
@patch("tasks.monitoring.reassign_task")
@patch("tasks.monitoring.logger")
def test_check_deadline_task_overdue_no_extensions(mock_logger, mock_reassign_task, mock_get_redis):

    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {
        "task_id": "task_123",
        "assigned_to": "talent_1",
        "claimed_at": "2025-04-15T10:00:00",
        "deadline": "2025-04-15T12:00:00",
        "extensions": "[]",
    }
    mock_get_redis.return_value = mock_redis

    with patch("tasks.monitoring.Task") as MockTask:
        mock_task = MagicMock()
        mock_task.is_overdue.return_value = True
        mock_task.extensions = []
        MockTask.return_value = mock_task

        check_deadline(task_id="task_123")


        mock_logger.info.assert_any_call("Task task_123 is overdue")
        mock_logger.info.assert_any_call("No extensions found for task task_123. Triggering reassignment.")
        mock_reassign_task.delay.assert_called_once_with("task_123")


@patch("tasks.monitoring.get_redis")
@patch("tasks.monitoring.reassign_task")
@patch("tasks.monitoring.logger")
def test_check_deadline_task_overdue_with_extensions(mock_logger, mock_reassign_task, mock_get_redis):

    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {
        "task_id": "task_123",
        "assigned_to": "talent_1",
        "claimed_at": "2025-04-15T10:00:00",
        "deadline": "2025-04-15T12:00:00",
        "extensions": '[{"approved": true}]',
    }
    mock_get_redis.return_value = mock_redis


    with patch("tasks.monitoring.Task") as MockTask:
        mock_task = MagicMock()
        mock_task.is_overdue.return_value = True
        mock_task.extensions = [{"approved": True}]
        MockTask.return_value = mock_task

        check_deadline(task_id="task_123")

        mock_logger.info.assert_any_call("Task task_123 is overdue")
        mock_logger.info.assert_any_call("Task task_123 has extensions. No reassignment needed.")
        mock_reassign_task.delay.assert_not_called()