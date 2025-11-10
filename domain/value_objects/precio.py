# domain/value_objects/precio.py
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Precio:
    valor: Decimal
    moneda: str = "USD"

    def __post_init__(self):
        if self.valor < 0:
            raise ValueError("El precio no puede ser negativo.")

    def aplicar_descuento(self, porcentaje: Decimal) -> 'Precio':
        nuevo_valor = self.valor * (1 - porcentaje / 100)
        return Precio(nuevo_valor, self.moneda)