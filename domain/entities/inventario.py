from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Inventario:
    id_inventario: Optional[int] = None
    id_producto: int
    id_bodega: int
    cantidad_stock: int = 0
    cantidad_minima: int = 0
    fecha_actualizacion: Optional[date] = None