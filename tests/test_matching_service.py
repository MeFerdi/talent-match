import pytest
from unittest.mock import patch, MagicMock
from domain.services.matching import MatchingService

@patch("domain.services.matching.Talent")
@patch("domain.services.matching.Task")
@patch("domain.services.matching.get_redis")
def test_get_next_available_success(mock_get_redis, mock_task, mock_talent):
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis

    # Mock Task
    mock_task_instance = MagicMock()
    mock_task_instance.matches = {"talent_1": 90, "talent_2": 80}
    mock_task.from_redis.return_value = mock_task_instance

    # Mock Talent
    mock_talent_instance = MagicMock()
    mock_talent_instance.available = True
    mock_talent.from_redis.side_effect = lambda redis, talent_id: mock_talent_instance if talent_id == "talent_1" else None

    # Act
    result = MatchingService.get_next_available("task_123")

    # Assert
    assert result == "talent_1"
    mock_task.from_redis.assert_called_once_with(mock_redis, "task_123")
    mock_talent.from_redis.assert_any_call(mock_redis, "talent_1")
    mock_talent.from_redis.assert_any_call(mock_redis, "talent_2")

@patch("domain.services.matching.Talent")
@patch("domain.services.matching.Task")
@patch("domain.services.matching.get_redis")
def test_get_next_available_no_matches(mock_get_redis, mock_task, mock_talent):
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis

    # Mock Task with no matches
    mock_task_instance = MagicMock()
    mock_task_instance.matches = {}
    mock_task.from_redis.return_value = mock_task_instance

    # Act
    result = MatchingService.get_next_available("task_123")

    # Assert
    assert result is None
    mock_task.from_redis.assert_called_once_with(mock_redis, "task_123")
    mock_talent.from_redis.assert_not_called()

@patch("domain.services.matching.Talent")
@patch("domain.services.matching.Task")
@patch("domain.services.matching.get_redis")
def test_get_next_available_success(mock_get_redis, mock_task, mock_talent):
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis

    # Mock Task
    mock_task_instance = MagicMock()
    mock_task_instance.matches = {"talent_1": 90, "talent_2": 80}
    mock_task.from_redis.return_value = mock_task_instance

    # Mock Talent
    mock_talent_instance = MagicMock()
    mock_talent_instance.available = True
    mock_talent.from_redis.side_effect = lambda redis, talent_id: mock_talent_instance if talent_id == "talent_1" else None

    # Act
    result = MatchingService.get_next_available("task_123")

    # Assert
    assert result == "talent_1"
    mock_task.from_redis.assert_called_once_with(mock_redis, "task_123")
    mock_talent.from_redis.assert_any_call(mock_redis, "talent_1")