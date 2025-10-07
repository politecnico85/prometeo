from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from infrastructure.persistence.event_store_sql import EventStore
from infrastructure.persistence.snapshot_sql import SnapshotRepository
from domain.events.domain_event import DomainEvent

class NotaCreditoRepository:
    def __init__(self, event_store: EventStore, snapshot_repository: SnapshotRepository, snapshot_frequency: int = 10):
        self.event_store = event_store
        self.snapshot_repository = snapshot_repository
        self.snapshot_frequency = snapshot_frequency

    def guardar(self, aggregate: NotaCreditoAggregate):
        events = aggregate.get_pending_events()
        for event in events:
            event.aggregate_type = "NotaCredito"
            self.event_store.append(event)
        
        # Save snapshot if event count exceeds frequency
        if aggregate._version >= self.snapshot_frequency:
            snapshot = aggregate.to_snapshot()
            self.snapshot_repository.save_snapshot(
                aggregate_id=aggregate.root.id_nota_credito,
                aggregate_type="NotaCredito",
                version=aggregate._version,
                state=snapshot
            )
        
        aggregate.clear_pending_events()

    def obtener_por_id(self, id_nota_credito: int) -> NotaCreditoAggregate:
        snapshot, version = self.snapshot_repository.get_snapshot(id_nota_credito, "NotaCredito")
        events = self.event_store.get_events(id_nota_credito, "NotaCredito", after_version=version)
        
        if snapshot:
            aggregate = NotaCreditoAggregate.from_snapshot(snapshot, events)
        else:
            aggregate = NotaCreditoAggregate.from_events(events)
        
        return aggregate