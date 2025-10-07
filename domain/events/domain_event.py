# domain/events/domain_event.py
from datetime import datetime
from typing import Any
from uuid import uuid4

class DomainEvent:
    def __init__(self, aggregate_id: int, event_type: str, data: dict, occurred_on: datetime = None):
        self.event_id = str(uuid4())
        self.aggregate_id = aggregate_id
        self.event_type = event_type
        self.data = data
        self.occurred_on = occurred_on or datetime.utcnow()
