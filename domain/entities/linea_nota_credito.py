# domain/entities/linea_nota_credito.py
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

@dataclass
class LineaNotaCredito:
    id_linea_nota_credito: Optional[int] = None  # None para nuevas
    id_producto: int
    descripcion: str
    cantidad: int
    valor_item_cobrado: Decimal  # Valor original cobrado en factura
    valor_total: Decimal = field(init=False)

    def __post_init__(self):
        if self.cantidad <= 0:
            raise ValueError("Cantidad debe ser positiva.")
        self.valor_total = self.cantidad * self.valor_item_cobrado  # Ajustar lógica si hay descuentos/IVA

    def ajustar_valor(self, nuevo_valor: Decimal):
        if nuevo_valor <= 0:
            raise ValueError("Valor inválido.")
        self.valor_item_cobrado = nuevo_valor
        self.valor_total = self.cantidad * self.valor_item_cobrado