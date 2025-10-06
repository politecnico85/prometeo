# domain/value_objects/motivo_modificacion.py
from dataclasses import dataclass

@dataclass(frozen=True)
class MotivoModificacion:
    descripcion: str

    def __post_init__(self):
        if not self.descripcion.strip():
            raise ValueError("Motivo de modificación no puede estar vacío.")