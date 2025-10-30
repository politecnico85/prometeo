from infrastructure.persistence.projection_sql import ProjectionRepository

class QueryService:
    def __init__(self, projection_repository: ProjectionRepository):
        self.projection_repository = projection_repository

    def get_stock(self, producto_id: int, bodega_id: int) -> float:
        return self.projection_repository.get_stock(producto_id, bodega_id)

    def get_factura(self, id_factura: int) -> dict:
        return self.projection_repository.get_factura(id_factura)

    def get_nota_credito(self, id_nota_credito: int) -> dict:
        return self.projection_repository.get_nota_credito(id_nota_credito)