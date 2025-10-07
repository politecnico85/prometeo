from decimal import Decimal
from datetime import date
from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from domain.repositories.nota_credito_repository import NotaCreditoRepository
from domain.repositories.factura_repository import FacturaRepository
from domain.repositories.event_store import EventStore
from domain.services.inventario_service import InventarioService
from domain.services.event_handler import EventHandler
from domain.services.event_publisher import EventPublisher
from infrastructure.persistence.projection_sql import ProjectionRepository
from domain.specifications.nota_credito_specifications import (
    LineasValidasContraFactura, FechaEmisionPosteriorFactura, PlazoNotaCreditoValido
)
from domain.entities.linea_nota_credito import LineaNotaCredito

class NotaCreditoService:
    def __init__(self, nc_repo: NotaCreditoRepository, factura_repo: FacturaRepository, 
                 inventario_service: InventarioService, event_store: EventStore, 
                 event_publisher: EventPublisher, projection_repository: ProjectionRepository):
        self.nc_repo = nc_repo
        self.factura_repo = factura_repo
        self.inventario_service = inventario_service
        self.event_store = event_store
        self.event_handler = EventHandler(inventario_service, projection_repository)
        self.event_publisher = event_publisher
        self.projection_repository = projection_repository

    def crear_y_emitir_nota_credito(self, datos: dict) -> NotaCreditoAggregate:
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
            id_producto=1,
            descripcion="Devolución Prod1",
            cantidad=2,
            valor_item_cobrado=Decimal('10.00')
        )
        aggregate.agregar_linea(linea)

        # Validaciones externas
        validaciones_externas = [
            LineasValidasContraFactura(factura_agg),
            FechaEmisionPosteriorFactura(factura_agg),
            PlazoNotaCreditoValido(factura_agg, max_dias=30)
        ]
        errors = []
        for spec in validaciones_externas:
            if not spec.is_satisfied_by(aggregate.root):
                errors.append(f"Validación externa fallida: {spec.__class__.__name__}")
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