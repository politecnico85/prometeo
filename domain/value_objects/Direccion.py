# domain/value_objects/direccion.py
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Direccion:
    calle: str
    ciudad: str
    pais: str = "Ecuador"  # Asumiendo contexto ecuatoriano por RUC en el esquema
    codigo_postal: str = field(default="")

    def __eq__(self, other):
        if not isinstance(other, Direccion):
            return False
        return (self.calle == other.calle and self.ciudad == other.ciudad and
                self.pais == other.pais and self.codigo_postal == other.codigo_postal)