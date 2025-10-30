import pika
import json
import logging
from domain.services.event_publisher import EventPublisher
from domain.events.domain_event import DomainEvent

class RabbitMQPublisher(EventPublisher):
    def __init__(self, host: str, exchange: str, username: str = "guest", password: str = "guest"):
        self.host = host
        self.exchange = exchange
        self.credentials = pika.PlainCredentials(username, password)
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, credentials=self.credentials)
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, event: DomainEvent):
        if not self.connection or self.connection.is_closed:
            self._connect()
        try:
            message = json.dumps({
                "event_id": event.event_id,
                "aggregate_id": event.aggregate_id,
                "event_type": event.event_type,
                "data": event.data,
                "occurred_on": event.occurred_on.isoformat()
            })
            routing_key = f"facturacion.{event.event_type.lower()}"
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message
            )
            logging.info(f"Published event {event.event_type} with routing key {routing_key}")
        except Exception as e:
            logging.error(f"Failed to publish event {event.event_type}: {e}")
            raise

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()