from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

@dataclass
class MockSlackMessage:
    channel: str
    text: str
    timestamp: str
    reactions: List[str]

class MockSlackClient:
    def __init__(self):
        self.messages: List[MockSlackMessage] = []
        self._message_id = 1
    
    def post_message(self, channel: str, text: str) -> Dict:
        """Simulate sending a Slack message"""
        msg = MockSlackMessage(
            channel=channel,
            text=text,
            timestamp=str(datetime.now().timestamp()),
            reactions=[]
        )
        self.messages.append(msg)
        return {
            "ok": True,
            "message": {
                "ts": msg.timestamp,
                "text": text,
                "channel": channel
            }
        }
    
    def add_reaction(self, channel: str, timestamp: str, emoji: str) -> Dict:
        """Simulate adding a reaction"""
        for msg in self.messages:
            if msg.channel == channel and msg.timestamp == timestamp:
                msg.reactions.append(emoji)
                return {"ok": True}
        return {"ok": False, "error": "message_not_found"}
    
    def get_message(self, channel: str, lookback: int = 1) -> Optional[MockSlackMessage]:
        """Get the nth most recent message in a channel"""
        channel_msgs = [m for m in self.messages if m.channel == channel]
        try:
            return channel_msgs[-lookback]
        except IndexError:
            return None

    def clear_messages(self):
        """Clear all stored messages"""
        self.messages = []

# Singleton instance for testing
mock_slack = MockSlackClient()
def send_task_assignment(task_id: str, channel: str):
    """Simulate sending a task assignment message to a Slack channel."""
    text = f"Task {task_id} has been assigned."
    mock_slack.post_message(channel, text)