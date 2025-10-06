from decimal import Decimal
from typing import Optional

class MovimientoInventario:
    def __init__(
        self,
        id_producto: int,
        id_bodega: int,
        tipo_movimiento: str,
        cantidad: int,
        costo_unitario_aplicado: Decimal,
        id_factura: Optional[int] = None,
        fecha: Optional[str] = None,
        observaciones: Optional[str] = None
    ):
        self.id_producto = id_producto
        self.id_bodega = id_bodega
        self.tipo_movimiento = tipo_movimiento  # 'ENTRADA' o 'SALIDA'
        self.cantidad = cantidad
        self.costo_unitario_aplicado = costo_unitario_aplicado
        self.id_factura = id_factura
        self.fecha = fecha
        self.observaciones = observaciones

    def __repr__(self):
        return (
            f"<MovimientoInventario producto={self.id_producto} bodega={self.id_bodega} "
            f"tipo={self.tipo_movimiento} cantidad={self.cantidad} costo={self.costo_unitario_aplicado}>"
        )