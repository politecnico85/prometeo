from abc import ABC, abstractmethod
from typing import List
from domain.entities.factura import Factura
from domain.entities.inventario import Inventario

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool:
        pass

class StockSuficienteParaFactura(Specification):
    def __init__(self, inventarios: List[Inventario]):
        self.inventarios = {inv.id_producto: inv.cantidad_stock for inv in inventarios}

    def is_satisfied_by(self, factura: Factura) -> bool:
        for linea in factura.lineas:
            stock_disponible = self.inventarios.get(linea.id_producto, 0)
            if linea.cantidad > stock_disponible:
                return False
        return True