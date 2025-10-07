from domain.events.domain_event import DomainEvent

class FacturaEmitida(DomainEvent):
       def __init__(self, aggregate_id: int, factura_data: dict):
           super().__init__(aggregate_id, "FacturaEmitida", factura_data)

class StockReducido(DomainEvent):
       def __init__(self, aggregate_id: int, producto_id: int, bodega_id: int, cantidad: int, costo_unitario: float):
           data = {
               "producto_id": producto_id,
               "bodega_id": bodega_id,
               "cantidad": cantidad,
               "costo_unitario": float(costo_unitario)
           }
           super().__init__(aggregate_id, "StockReducido", data)