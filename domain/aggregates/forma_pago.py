# domain/value_objects/forma_pago.py
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class FormaPago:
    tipo: str  # e.g., 'Efectivo', 'Tarjeta'
    valor: Decimal

    def __post_init__(self):
        if self.valor < 0:
            raise ValueError("Valor de pago no puede ser negativo.")