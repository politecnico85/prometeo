# domain/value_objects/ruc.py (Value Object para validación de RUC ecuatoriano, asumiendo contexto)
from dataclasses import dataclass

@dataclass(frozen=True)
class RUC:
    numero: str

    def __post_init__(self):
        if len(self.numero) != 13 or not self.numero.isdigit():
            raise ValueError("RUC inválido: debe ser 13 dígitos.")