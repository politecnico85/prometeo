from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from domain.events.domain_event import DomainEvent
from datetime import datetime
import json

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    aggregate_id = Column(Integer, index=True)
    aggregate_type = Column(String)
    event_type = Column(String)
    data = Column(Text)
    occurred_on = Column(DateTime)
    version = Column(Integer)

class EventStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def append(self, event: DomainEvent):
        session = self.Session()
        try:
            version = self._get_next_version(event.aggregate_id, event.aggregate_type)
            db_event = Event(
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                event_type=event.event_type,
                data=json.dumps(event.data),
                occurred_on=event.occurred_on,
                version=version
            )
            session.add(db_event)
            session.commit()
        finally:
            session.close()

    def get_events(self, aggregate_id: int, aggregate_type: str, after_version: int = 0) -> list[DomainEvent]:
        session = self.Session()
        try:
            events = session.query(Event).filter_by(
                aggregate_id=aggregate_id, aggregate_type=aggregate_type
            ).filter(Event.version > after_version).order_by(Event.version).all()
            return [
                DomainEvent(
                    aggregate_id=e.aggregate_id,
                    aggregate_type=e.aggregate_type,
                    event_type=e.event_type,
                    data=json.loads(e.data),
                    occurred_on=e.occurred_on
                ) for e in events
            ]
        finally:
            session.close()

    def _get_next_version(self, aggregate_id: int, aggregate_type: str) -> int:
        session = self.Session()
        try:
            last_event = session.query(Event).filter_by(
                aggregate_id=aggregate_id, aggregate_type=aggregate_type
            ).order_by(Event.version.desc()).first()
            return last_event.version + 1 if last_event else 1
        finally:
            session.close()