# domain/repositories/producto_repository.py
from abc import ABC, abstractmethod
from domain.aggregates.producto_aggregate import ProductoAggregate

class ProductoRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: int) -> ProductoAggregate:
        pass

    @abstractmethod
    def guardar(self, aggregate: ProductoAggregate):
        pass