from domain.events.domain_event import DomainEvent

class NotaCreditoEmitida(DomainEvent):
       def __init__(self, aggregate_id: int, nota_credito_data: dict):
           super().__init__(aggregate_id, "NotaCreditoEmitida", nota_credito_data)

class StockIncrementado(DomainEvent):
       def __init__(self, aggregate_id: int, producto_id: int, bodega_id: int, cantidad: int, costo_unitario: float):
           data = {
               "producto_id": producto_id,
               "bodega_id": bodega_id,
               "cantidad": cantidad,
               "costo_unitario": float(costo_unitario)
           }
           super().__init__(aggregate_id, "StockIncrementado", data)