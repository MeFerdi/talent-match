import pytest
from unittest.mock import MagicMock, patch
from domain.models.talent import Talent


@patch("domain.models.talent.redis.Redis")
def test_from_redis_success(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis_instance.hgetall.return_value = {
        "available": "true",
        "rating": "4.5"
    }
    mock_redis.return_value = mock_redis_instance

    talent = Talent.from_redis(mock_redis_instance, "talent_123")
    assert talent is not None
    assert talent.talent_id == "talent_123"
    assert talent.available is True
    assert talent.rating == 4.5


@patch("domain.models.talent.redis.Redis")
def test_from_redis_no_data(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis_instance.hgetall.return_value = {}
    mock_redis.return_value = mock_redis_instance

    talent = Talent.from_redis(mock_redis_instance, "talent_123")
    assert talent is None


@patch("domain.models.talent.redis.Redis")
def test_to_redis_success(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis.return_value = mock_redis_instance

    talent = Talent(talent_id="talent_123", available=True, rating=4.5)
    result = talent.to_redis(mock_redis_instance)
    assert result is True
    mock_redis_instance.hset.assert_called_once_with(
        "talent:talent_123",
        mapping={"available": "True", "rating": "4.5"}
    )


@patch("domain.models.talent.redis.Redis")
def test_bulk_save_success(mock_redis):
    mock_redis_instance = MagicMock()
    mock_redis_instance.pipeline.return_value.__enter__.return_value.execute.return_value = [1, 1, 1]
    mock_redis.return_value = mock_redis_instance

    talents = [
        Talent(talent_id="talent_1", available=True, rating=4.5),
        Talent(talent_id="talent_2", available=False, rating=3.8),
        Talent(talent_id="talent_3", available=True, rating=5.0)
    ]
    result = Talent.bulk_save(mock_redis_instance, talents)
    assert result == 3
    mock_redis_instance.pipeline.return_value.__enter__.return_value.hset.assert_called()