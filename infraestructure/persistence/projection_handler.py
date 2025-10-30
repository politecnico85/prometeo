import pika
import json
import logging
from domain.events.domain_event import DomainEvent
from infrastructure.persistence.projection_sql import ProjectionRepository
from datetime import datetime

class ProjectionHandler:
    def __init__(self, host: str, exchange: str, projection_repository: ProjectionRepository, 
                 username: str = "guest", password: str = "guest"):
        self.host = host
        self.exchange = exchange
        self.projection_repository = projection_repository
        self.credentials = pika.PlainCredentials(username, password)
        self.connection = None
        self.channel = None

    def start_consuming(self):
        self._connect()
        self.channel.basic_consume(queue=self.queue, on_message_callback=self._callback, auto_ack=True)
        logging.info("Starting projection handler consumption")
        self.channel.start_consuming()

    def _connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, credentials=self.credentials)
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
            result = self.channel.queue_declare(queue="", exclusive=True)
            self.queue = result.method.queue
            self.channel.queue_bind(exchange=self.exchange, queue=self.queue, routing_key="facturacion.*")
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def _callback(self, ch, method, properties, body):
        try:
            event_data = json.loads(body.decode())
            event = DomainEvent(
                aggregate_id=event_data["aggregate_id"],
                event_type=event_data["event_type"],
                data=event_data["data"],
                occurred_on=datetime.fromisoformat(event_data["occurred_on"])
            )
            self._handle_event(event)
            logging.info(f"Processed event {event.event_type}")
        except Exception as e:
            logging.error(f"Failed to process event: {e}")

    def _handle_event(self, event: DomainEvent):
        if event.event_type == "StockReducido":
            current_stock = self.projection_repository.get_stock(
                event.data["producto_id"], event.data["bodega_id"]
            )
            new_stock = max(0.0, current_stock - event.data["cantidad"])
            self.projection_repository.update_stock(
                event.data["producto_id"], event.data["bodega_id"], new_stock
            )
        elif event.event_type == "StockIncrementado":
            current_stock = self.projection_repository.get_stock(
                event.data["producto_id"], event.data["bodega_id"]
            )
            new_stock = current_stock + event.data["cantidad"]
            self.projection_repository.update_stock(
                event.data["producto_id"], event.data["bodega_id"], new_stock
            )
        elif event.event_type == "FacturaEmitida":
            self.projection_repository.save_factura(event.data)
        elif event.event_type == "NotaCreditoEmitida":
            self.projection_repository.save_nota_credito(event.data)

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()