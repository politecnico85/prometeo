# domain/services/inventario_service.py
from decimal import Decimal
from typing import List
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.entities.lote import Lote
from domain.repositories.lote_repository import LoteRepository  # Definido abajo

class InventarioService:
    def __init__(self, lote_repo: LoteRepository):
        self.lote_repo = lote_repo

    def registrar_salida_fifo(self, producto_id: int, bodega_id: int, cantidad: int, factura_id: int) -> List[MovimientoInventario]:
        movimientos = []
        cantidad_pendiente = cantidad
        lotes = self.lote_repo.obtener_lotes_antiguos(producto_id, bodega_id)

        for lote in lotes:
            if cantidad_pendiente <= 0:
                break
            despacho = min(lote.cantidad_restante, cantidad_pendiente)
            lote.cantidad_restante -= despacho
            self.lote_repo.actualizar(lote)

            movimiento = MovimientoInventario(
                id_producto=producto_id,
                id_bodega=bodega_id,
                tipo_movimiento='SALIDA',
                cantidad=despacho,
                costo_unitario_aplicado=lote.costo_unitario,
                id_factura=factura_id,
                # ... otros campos
            )
            movimientos.append(movimiento)
            cantidad_pendiente -= despacho

        if cantidad_pendiente > 0:
            raise ValueError("Stock insuficiente en FIFO.")
        return movimientos