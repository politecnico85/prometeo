from datetime import datetime
from decimal import Decimal
from typing import Optional

class MovimientoInventario:
    def __init__(
        self,
        id_producto: int,
        id_bodega: int,
        fecha_movimiento: datetime,
        stock_post_movimiento: int,
        id_movimiento: Optional[int] = None,
        id_orden_compra: Optional[int] = None,
        id_lote: Optional[int] = None,
        tipo_movimiento: Optional[str] = None,  # 'ENTRADA' o 'SALIDA'
        cantidad: Optional[int] = None,
        costo_unitario_aplicado: Optional[Decimal] = None,
        id_factura: Optional[int] = None,
        observaciones: Optional[str] = None
    ):
        self.id_movimiento = id_movimiento
        self.id_producto = id_producto
        self.id_bodega = id_bodega
        self.id_orden_compra = id_orden_compra
        self.id_lote = id_lote
        self.tipo_movimiento = tipo_movimiento  # 'ENTRADA' o 'SALIDA'
        self.cantidad = cantidad
        self.costo_unitario_aplicado = costo_unitario_aplicado
        self.id_factura = id_factura
        self.fecha_movimiento = fecha_movimiento
        self.stock_post_movimiento = stock_post_movimiento
        self.observaciones = observaciones

    def __repr__(self):
        return (
            f"<MovimientoInventario producto={self.id_producto} bodega={self.id_bodega} "
            f"tipo={self.tipo_movimiento} cantidad={self.cantidad} costo={self.costo_unitario_aplicado}>"
        )
    

 