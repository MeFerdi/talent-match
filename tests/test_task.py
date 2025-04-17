import pytest
from unittest.mock import MagicMock, patch
from domain.models.task import Task
from datetime import datetime, timedelta


@patch("domain.models.task.redis.Redis")
def test_from_redis_success(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis_instance.hgetall.return_value = {
        "task_id": "task_123",
        "assigned_to": "talent_1",
        "claimed_at": datetime.now().isoformat(),
        "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
        "status": "assigned",
        "extensions": "[]",
        "matches": '{"talent_1": 0.9, "talent_2": 0.8}'
    }
    mock_redis.return_value = mock_redis_instance

    task = Task.from_redis(mock_redis_instance, "task_123")
    assert task is not None
    assert task.task_id == "task_123"
    assert task.assigned_to == "talent_1"
    assert task.status == "assigned"
    assert task.matches == {"talent_1": 0.9, "talent_2": 0.8}


@patch("domain.models.task.redis.Redis")
def test_from_redis_no_data(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis_instance.hgetall.return_value = {}
    mock_redis.return_value = mock_redis_instance

    task = Task.from_redis(mock_redis_instance, "task_123")
    assert task is None


@patch("domain.models.task.redis.Redis")
def test_to_redis_success(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis.return_value = mock_redis_instance

    task = Task(
        task_id="task_123",
        assigned_to="talent_1",
        claimed_at=datetime.now(),
        deadline=datetime.now() + timedelta(days=1),
        status="assigned",
        matches={"talent_1": 0.9, "talent_2": 0.8}
    )
    result = task.to_redis(mock_redis_instance)
    assert result is True
    mock_redis_instance.hset.assert_called_once()


def test_is_overdue():
    task = Task(
        task_id="task_123",
        deadline=datetime.now() - timedelta(days=1)
    )
    assert task.is_overdue() is True

    task.deadline = datetime.now() + timedelta(days=1)
    assert task.is_overdue() is False


def test_add_extension():
    task = Task(task_id="task_123")
    task.add_extension("Need more time")
    assert len(task.extensions) == 1
    assert task.extensions[0]["reason"] == "Need more time"
    assert task.extensions[0]["approved"] is None