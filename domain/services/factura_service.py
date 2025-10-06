from decimal import Decimal
from datetime import date
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.repositories.factura_repository import FacturaRepository
from domain.services.inventario_service import InventarioService
from domain.entities.linea_factura import LineaFactura
from domain.value_objects.precio import Precio

class FacturaService:
    def __init__(self, factura_repo: FacturaRepository, inventario_service: InventarioService):
        self.factura_repo = factura_repo
        self.inventario_service = inventario_service

    def crear_y_emitir_factura(self, datos: dict) -> FacturaAggregate:
        fecha_emision = datos.get('fecha_emision', date.today())
        fecha_caducidad = datos.get('fecha_caducidad')
        fecha_autorizacion = datos.get('fecha_autorizacion', date.today())

        aggregate = FacturaAggregate.crear_nueva(
            id_sucursal=datos['id_sucursal'],
            ruc_emisor=datos['ruc_emisor'],
            adquiriente=datos['identificacion_adquiriente'],
            direccion=datos['direccion_matriz'],
            razon_social=datos['razon_social_emisor'],
            fecha_emision=fecha_emision,
            fecha_caducidad=fecha_caducidad,
            fecha_autorizacion=fecha_autorizacion
        )

        # Ejemplo: Agregar línea
        linea = LineaFactura(
            id_producto=1,
            descripcion="Prod1",
            cantidad=5,
            precio_unitario=Precio(Decimal('10.00'))
        )
        aggregate.agregar_linea(linea)

        movimientos = aggregate.emitir(self.inventario_service)
        self.factura_repo.guardar(aggregate)
        return aggregate