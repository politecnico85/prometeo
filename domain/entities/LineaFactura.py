# domain/entities/linea_factura.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class LineaFactura:
    id_linea_factura: int
    descripcion: str
    cantidad: int
    precio_unitario: Decimal
    valor_total: Decimal = field(init=False)
    id_producto: int
    id_descuento: Optional[int] = None

    def __post_init__(self):
        self.valor_total = self.cantidad * self.precio_unitario