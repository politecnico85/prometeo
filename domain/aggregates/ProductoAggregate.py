# domain/aggregates/producto_aggregate.py
from domain.entities.producto import Producto
from domain.entities.inventario import Inventario  # Entity similar para stock

class ProductoAggregate:
    def __init__(self, producto: Producto, inventarios: list[Inventario]):
        self.root = producto
        self.inventarios = inventarios  # Lista de inventarios por bodega

    def ajustar_stock(self, bodega_id: int, cantidad: int):
        inventario = next((inv for inv in self.inventarios if inv.id_bodega == bodega_id), None)
        if not inventario:
            raise ValueError("Bodega no encontrada.")
        inventario.cantidad_stock += cantidad