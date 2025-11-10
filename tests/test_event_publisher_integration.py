# tests/test_event_publisher_integration.py
import unittest
from domain.events.factura_events import FacturaEmitida
from infrastructure.persistence.rabbitmq_publisher import RabbitMQPublisher
import pika
import json

class TestEventPublisherIntegration(unittest.TestCase):
    def setUp(self):
        self.publisher = RabbitMQPublisher(host="localhost", exchange="facturacion")
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange="facturacion", exchange_type="topic")
        self.queue = self.channel.queue_declare(queue="", exclusive=True).method.queue
        self.channel.queue_bind(exchange="facturacion", queue=self.queue, routing_key="facturacion.facturaemitida")

    def tearDown(self):
        self.publisher.close()
        self.connection.close()

    def test_publish_factura_event(self):
        # Arrange
        event = FacturaEmitida(1, {"id_factura": 1, "fecha_emision": date.today().isoformat()})
        messages = []

        def callback(ch, method, properties, body):
            messages.append(json.loads(body.decode()))

        self.channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=True)

        # Act
        self.publisher.publish(event)
        self.channel.start_consuming()
        self.channel.stop_consuming()

        # Assert
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["event_type"], "FacturaEmitida")