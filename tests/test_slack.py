from integrations.mock.slack import mock_slack

def test_task_assignment():
    # Setup
    mock_slack.clear_messages()
    
    # Execute
    from integrations.mock.slack import send_task_assignment

    send_task_assignment("task_123", "general")
    
    # Verify
    last_msg = mock_slack.get_message("general")
    assert "task_123" in last_msg.text
    assert len(mock_slack.messages) == 1