# domain/services/nota_credito_service.py
from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from domain.repositories.nota_credito_repository import NotaCreditoRepository
from domain.repositories.factura_repository import FacturaRepository
from domain.services.inventario_service import InventarioService
from domain.aggregates.nota_credito_aggregate import LineaNotaCredito
from decimal import Decimal

class NotaCreditoService:
    def __init__(self, nc_repo: NotaCreditoRepository, factura_repo: FacturaRepository, inventario_service: InventarioService):
        self.nc_repo = nc_repo
        self.factura_repo = factura_repo
        self.inventario_service = inventario_service

    def crear_y_emitir_nota_credito(self, datos: dict) -> NotaCreditoAggregate:
        # Validar contra factura original
        factura_agg = self.factura_repo.obtener_por_id(datos['id_factura_modificada'])
        if not factura_agg:
            raise ValueError("Factura no existe.")
        # Agregar lógica: chequear lineas propuestas <= lineas de factura

        aggregate = NotaCreditoAggregate.crear_nueva(**datos)
        # Agregar líneas (validando contra factura)
        aggregate.agregar_linea(LineaNotaCredito(id_producto=1, descripcion="Devolución Prod1", cantidad=2, valor_item_cobrado=Decimal('10.00')))
        movimientos = aggregate.emitir(self.inventario_service, bodega_id=factura_agg.root.id_bodega)  # Obtener bodega de factura
        self.nc_repo.guardar(aggregate)
        # Publicar evento
        return aggregate