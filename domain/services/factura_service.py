# domain/services/factura_service.py
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.repositories.factura_repository import FacturaRepository
from domain.services.inventario_service import InventarioService
from domain.aggregates.linea_factura import LineaFactura  # Import LineaFactura
from domain.value_objects.precio import Precio  # Import Precio
from decimal import Decimal  # Import Decimal if not already imported

class FacturaService:
    def __init__(self, factura_repo: FacturaRepository, inventario_service: InventarioService):
        self.factura_repo = factura_repo
        self.inventario_service = inventario_service

    def crear_y_emitir_factura(self, datos: dict) -> FacturaAggregate:
        aggregate = FacturaAggregate.crear_nueva(**datos)
        # Agregar líneas vía métodos
        aggregate.agregar_linea(LineaFactura(id_producto=1, descripcion="Prod1", cantidad=5, precio_unitario=Precio(Decimal('10.00'))))
        movimientos = aggregate.emitir(self.inventario_service)
        self.factura_repo.guardar(aggregate)
        # Manejar eventos: e.g., publicar FacturaEmitida
        return aggregate