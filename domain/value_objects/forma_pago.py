from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class FormaPago:
    tipo: str
    valor: Decimal

    def __post_init__(self):
        if self.valor < 0:
            raise ValueError("Valor de pago no puede ser negativo.")