# tests/test_cqrs_integration.py
import unittest
from datetime import date
from domain.events.factura_events import FacturaEmitida, StockReducido
from infrastructure.persistence.projection_sql import ProjectionRepository
from infrastructure.persistence.rabbitmq_publisher import RabbitMQPublisher
from infrastructure.persistence.projection_handler import ProjectionHandler
import time

class TestCQRSIntegration(unittest.TestCase):
    def setUp(self):
        self.projection_repo = ProjectionRepository("sqlite:///test_projections.db")
        self.publisher = RabbitMQPublisher("localhost", "facturacion")
        self.handler = ProjectionHandler("localhost", "facturacion", self.projection_repo)
        self.handler_process = None

    def tearDown(self):
        self.publisher.close()
        self.handler.close()

    def test_projection_updated_via_rabbitmq(self):
        # Arrange
        event = StockReducido(1, 1, 1, 5, 10.0)
        self.projection_repo.update_stock(1, 1, 10.0)  # Initial stock

        # Start handler in a separate thread
        from threading import Thread
        self.handler_process = Thread(target=self.handler.start_consuming)
        self.handler_process.daemon = True
        self.handler_process.start()
        time.sleep(1)  # Allow handler to start

        # Act
        self.publisher.publish(event)
        time.sleep(1)  # Allow event to be processed

        # Assert
        stock = self.projection_repo.get_stock(1, 1)
        self.assertEqual(stock, 5.0)