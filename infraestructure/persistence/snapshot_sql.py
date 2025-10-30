from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()

class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    aggregate_id = Column(Integer, index=True)
    aggregate_type = Column(String)
    version = Column(Integer)
    state = Column(Text)

class SnapshotRepository:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_snapshot(self, aggregate_id: int, aggregate_type: str, version: int, state: dict):
        session = self.Session()
        try:
            snapshot = Snapshot(
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                version=version,
                state=json.dumps(state)
            )
            session.merge(snapshot)
            session.commit()
        finally:
            session.close()

    def get_snapshot(self, aggregate_id: int, aggregate_type: str) -> tuple[dict, int]:
        session = self.Session()
        try:
            snapshot = session.query(Snapshot).filter_by(
                aggregate_id=aggregate_id, aggregate_type=aggregate_type
            ).order_by(Snapshot.version.desc()).first()
            if snapshot:
                return json.loads(snapshot.state), snapshot.version
            return None, 0
        finally:
            session.close()