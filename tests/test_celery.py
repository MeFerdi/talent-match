from domain.utils.security import validate_task_payload
from config.celery import validate_and_process_task

def test_validate_task_payload_valid():
    payload = {
        "task_id": "12345",
        "data": {"key": "value"}
    }
    assert validate_task_payload(payload) is True

def test_validate_task_payload_invalid():
    payload = {
        "task_id": 12345,
        "data": "invalid_data"
    }
    assert validate_task_payload(payload) is False

def test_validate_and_process_task(mocker):
    mocker.patch("domain.utils.security.validate_task_payload", return_value=True)

    payload = {
        "task_id": "12345",
        "data": {"key": "value"}
    }

    validate_and_process_task(payload)