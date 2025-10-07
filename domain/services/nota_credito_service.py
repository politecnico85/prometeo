from decimal import Decimal
from datetime import date
from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from domain.repositories.nota_credito_repository import NotaCreditoRepository
from domain.repositories.factura_repository import FacturaRepository
from domain.repositories.event_store import EventStore
from domain.services.inventario_service import InventarioService
from domain.services.validation_service import ValidationService
from domain.services.event_handler import EventHandler
from domain.services.event_publisher import EventPublisher
from infrastructure.persistence.projection_sql import ProjectionRepository
from infrastructure.persistence.snapshot_sql import SnapshotRepository
from domain.entities.linea_nota_credito import LineaNotaCredito

class NotaCreditoService:
    def __init__(self, nc_repo: NotaCreditoRepository, factura_repo: FacturaRepository, 
                 inventario_service: InventarioService, event_store: EventStore, 
                 event_publisher: EventPublisher, projection_repository: ProjectionRepository, 
                 snapshot_repository: SnapshotRepository):
        self.nc_repo = nc_repo
        self.factura_repo = factura_repo
        self.inventario_service = inventario_service
        self.event_store = event_store
        self.validation_service = ValidationService(inventario_service)
        self.event_handler = EventHandler(inventario_service, projection_repository)
        self.event_publisher = event_publisher
        self.projection_repository = projection_repository
        self.snapshot_repository = snapshot_repository

    def crear_y_emitir_nota_credito(self, datos: dict) -> NotaCreditoAggregate:
        # Input validation
        required_fields = ['id_sucursal', 'ruc_emisor', 'id_factura_modificada', 'identificacion_adquiriente', 
                          'direccion_matriz', 'razon_social_emisor', 'motivo']
        if not all(field in datos for field in required_fields):
            raise ValueError("Faltan campos obligatorios")

        factura_agg = self.factura_repo.obtener_por_id(datos['id_factura_modificada'])
        if not factura_agg:
            raise ValueError("Factura no existe.")

        fecha_emision = datos.get('fecha_emision', date.today())
        fecha_caducidad = datos.get('fecha_caducidad')
        fecha_autorizacion = datos.get('fecha_autorizacion', date.today())

        aggregate = NotaCreditoAggregate.crear_nueva(
            id_sucursal=datos['id_sucursal'],
            ruc_emisor=datos['ruc_emisor'],
            id_factura_modificada=datos['id_factura_modificada'],
            adquiriente=datos['identificacion_adquiriente'],
            direccion=datos['direccion_matriz'],
            razon_social=datos['razon_social_emisor'],
            motivo=datos['motivo'],
            fecha_emision=fecha_emision,
            fecha_caducidad=fecha_caducidad,
            fecha_autorizacion=fecha_autorizacion
        )

        # Ejemplo: Agregar línea
        linea = LineaNotaCredito(
            id_producto=datos.get('id_producto', 1),
            descripcion=datos.get('descripcion', "Devolución Producto 1"),
            cantidad=datos.get('cantidad', 2),
            valor_item_cobrado=Decimal(str(datos.get('valor_item_cobrado', '10.00')))
        )
        aggregate.agregar_linea(linea)

        # Validar nota de crédito
        errors = self.validation_service.validate_nota_credito(aggregate, factura_agg)
        if errors:
            raise ValueError("; ".join(errors))

        # Emitir nota de crédito y obtener eventos
        events = aggregate.emitir(self.inventario_service, factura_agg.root.id_bodega, factura_agg)
        for event in events:
            self.event_store.append(event)
            self.event_handler.handle(event)
            self.event_publisher.publish(event)

        self.nc_repo.guardar(aggregate)
        return aggregate