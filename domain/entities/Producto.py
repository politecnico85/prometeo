# domain/entities/producto.py
from dataclasses import dataclass, field
from typing import Optional
from domain.value_objects.precio import Precio

@dataclass
class Producto:
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Precio = field(default_factory=lambda: Precio(Decimal('0.00')))
    codigo_barras: Optional[str] = None
    marca: Optional[str] = None
    # Relaciones (IDs para referencias, pero no cargamos objetos completos aquí para evitar ciclos)
    id_linea: int
    id_categoria: int

    def actualizar_precio(self, nuevo_precio: Precio):
        if nuevo_precio.valor <= 0:
            raise ValueError("Precio inválido.")
        self.precio_base = nuevo_precio