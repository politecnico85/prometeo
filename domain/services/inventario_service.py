from typing import List
from decimal import Decimal
from datetime import datetime, date
from domain.entities.inventario import Inventario
from domain.entities.lote import Lote
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.repositories.inventario_repository import InventarioRepository
from domain.repositories.lote_repository import LoteRepository

class InventarioService:
    def __init__(self, inventario_repo: InventarioRepository, lote_repo: LoteRepository):
        self.inventario_repo = inventario_repo
        self.lote_repo = lote_repo

    def obtener_inventarios_por_bodega(self, id_bodega: int) -> List[Inventario]:
        return self.inventario_repo.obtener_por_bodega(id_bodega)

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

            inventario = next((inv for inv in self.inventario_repo.obtener_por_bodega(bodega_id) 
                               if inv.id_producto == producto_id), None)
            if not inventario:
                raise ValueError("Inventario no encontrado.")
            inventario.cantidad_stock -= despacho
            self.inventario_repo.actualizar(inventario)

            movimiento = MovimientoInventario(
                id_producto=producto_id,
                id_bodega=bodega_id,
                id_factura=factura_id,
                tipo_movimiento='SALIDA',
                cantidad=despacho,
                costo_unitario_aplicado=lote.costo_unitario,
                fecha_movimiento=datetime.now(),
                stock_post_movimiento=inventario.cantidad_stock,
                id_lote=lote.id_lote
            )
            movimientos.append(movimiento)
            cantidad_pendiente -= despacho

        if cantidad_pendiente > 0:
            raise ValueError("Stock insuficiente en FIFO.")
        return movimientos

    def registrar_entrada(self, producto_id: int, bodega_id: int, cantidad: int, 
                          costo_unitario: Decimal, nota_credito_id: int = None) -> List[MovimientoInventario]:
        inventario = next((inv for inv in self.inventario_repo.obtener_por_bodega(bodega_id) 
                           if inv.id_producto == producto_id), None)
        if not inventario:
            raise ValueError("Inventario no encontrado.")
        inventario.cantidad_stock += cantidad
        inventario.fecha_actualizacion = date.today()
        self.inventario_repo.actualizar(inventario)

        lote = Lote(
            id_producto=producto_id,
            id_bodega=bodega_id,
            fecha_compra=date.today(),
            cantidad_inicial=cantidad,
            cantidad_restante=cantidad,
            costo_unitario=costo_unitario
        )
        self.lote_repo.guardar(lote)

        movimiento = MovimientoInventario(
            id_producto=producto_id,
            id_bodega=bodega_id,
            id_factura=None,
            id_orden_compra=None,
            id_lote=lote.id_lote,
            tipo_movimiento='ENTRADA',
            costo_unitario_aplicado=costo_unitario,
            cantidad=cantidad,
            fecha_movimiento=datetime.now(),
            stock_post_movimiento=inventario.cantidad_stock
        )
        return [movimiento]