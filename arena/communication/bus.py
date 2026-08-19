from typing import List
from arena.communication.messages import Message

class MessageBus:
    def __init__(self) -> None:
        self._messages: List[Message] = []

    def publish(self, message: Message) -> None:
        self._messages.append(message)

    def get_all(self) -> List[Message]:
        return self._messages
