# domain/repositories/factura_repository.py
from abc import ABC, abstractmethod
from domain.aggregates.factura_aggregate import FacturaAggregate

class FacturaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: int) -> FacturaAggregate:
        pass

    @abstractmethod
    def guardar(self, aggregate: FacturaAggregate):
        pass  # Guardar en transacción: factura, líneas, totales


    # Service: Un FacturaService orquesta creación/emisión, inyectando dependencies como InventarioService y repository.