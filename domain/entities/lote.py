from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

@dataclass
class Lote:
    id_lote: Optional[int] = None
    id_producto: int
    id_bodega: int
    id_orden_compra: Optional[int] = None
    fecha_compra: date
    cantidad_inicial: int
    cantidad_restante: int
    costo_unitario: Decimal