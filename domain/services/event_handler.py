from domain.events.domain_event import DomainEvent
from domain.services.inventario_service import InventarioService
from decimal import Decimal

class EventHandler:
       def __init__(self, inventario_service: InventarioService):
           self.inventario_service = inventario_service

       def handle(self, event: DomainEvent):
           if event.event_type == "StockReducido":
               self.inventario_service.registrar_salida_fifo(
                   producto_id=event.data["producto_id"],
                   bodega_id=event.data["bodega_id"],
                   cantidad=event.data["cantidad"],
                   factura_id=event.aggregate_id
               )
           elif event.event_type == "StockIncrementado":
               self.inventario_service.registrar_entrada(
                   producto_id=event.data["producto_id"],
                   bodega_id=event.data["bodega_id"],
                   cantidad=event.data["cantidad"],
                   costo_unitario=Decimal(event.data["costo_unitario"]),
                   nota_credito_id=event.aggregate_id
               )