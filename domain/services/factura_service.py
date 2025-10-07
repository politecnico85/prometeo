from decimal import Decimal
from datetime import date
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.repositories.factura_repository import FacturaRepository
from domain.repositories.event_store import EventStore
from domain.services.inventario_service import InventarioService
from domain.services.event_handler import EventHandler
from domain.services.event_publisher import EventPublisher
from infrastructure.persistence.projection_sql import ProjectionRepository
from domain.entities.linea_factura import LineaFactura
from domain.value_objects.precio import Precio


### python -m unittest discover tests
class FacturaService:
    def __init__(self, factura_repo: FacturaRepository, inventario_service: InventarioService, 
                 event_store: EventStore, event_publisher: EventPublisher, projection_repository: ProjectionRepository):
        self.factura_repo = factura_repo
        self.inventario_service = inventario_service
        self.event_store = event_store
        self.event_handler = EventHandler(inventario_service, projection_repository)
        self.event_publisher = event_publisher
        self.projection_repository = projection_repository

    def crear_y_emitir_factura(self, datos: dict) -> FacturaAggregate:
        aggregate = FacturaAggregate.crear_nueva(
            id_sucursal=datos['id_sucursal'],
            id_bodega=datos['id_bodega'],
            ruc_emisor=datos['ruc_emisor'],
            adquiriente=datos['identificacion_adquiriente'],
            direccion=datos['direccion_matriz'],
            razon_social=datos['razon_social_emisor'],
            forma_pago=datos['forma_pago'],
            fecha_emision=datos.get('fecha_emision', date.today()),
            fecha_caducidad=datos.get('fecha_caducidad'),
            fecha_autorizacion=datos.get('fecha_autorizacion', date.today())
        )

        # Ejemplo: Agregar línea
        linea = LineaFactura(
            id_producto=1,
            descripcion="Producto 1",
            cantidad=2,
            precio_unitario=Precio(Decimal('10.00'))
        )
        aggregate.agregar_linea(linea)

        # Emitir factura y obtener eventos
        events = aggregate.emitir(self.inventario_service)
        for event in events:
            self.event_store.append(event)
            self.event_handler.handle(event)
            self.event_publisher.publish(event)

        self.factura_repo.guardar(aggregate)
        return aggregate