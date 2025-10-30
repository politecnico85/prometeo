from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from domain.value_objects.precio import Precio

@dataclass
class LineaFactura:
    id_linea_factura: Optional[int] = None
    id_producto: int
    descripcion: str
    cantidad: int
    precio_unitario: Precio
    id_descuento: Optional[int] = None
    valor_total: Decimal = field(init=False)

    def __post_init__(self):
        if self.cantidad <= 0:
            raise ValueError("Cantidad debe ser positiva.")
        self.valor_total = self.cantidad * self.precio_unitario.valor

    def aplicar_descuento(self, descuento_valor: Decimal):
        if descuento_valor < 0 or descuento_valor > 100:
            raise ValueError("Descuento inválido.")
        self.precio_unitario = self.precio_unitario.aplicar_descuento(descuento_valor)
        self.valor_total = self.cantidad * self.precio_unitario.valor