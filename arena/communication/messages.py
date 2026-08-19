from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime

class Message(BaseModel):
    message_id: str
    sender: str
    recipient: str
    timestamp: datetime
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
