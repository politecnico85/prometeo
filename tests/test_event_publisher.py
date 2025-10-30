import unittest
from unittest.mock import Mock, patch
from datetime import date, datetime
from decimal import Decimal
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from domain.entities.factura import Factura
from domain.entities.linea_factura import LineaFactura
from domain.entities.totales_factura import TotalesFactura
from domain.entities.nota_credito import NotaCredito
from domain.entities.linea_nota_credito import LineaNotaCredito
from domain.entities.totales_nota_credito import TotalesNotaCredito
from domain.entities.inventario import Inventario
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.forma_pago import FormaPago
from domain.value_objects.motivo_modificacion import MotivoModificacion
from domain.value_objects.precio import Precio
from domain.services.inventario_service import InventarioService
from domain.services.event_publisher import EventPublisher
from infrastructure.persistence.rabbitmq_publisher import RabbitMQPublisher
from domain.events.factura_events import FacturaEmitida, StockReducido
from domain.events.nota_credito_events import NotaCreditoEmitida, StockIncrementado
import json

#### 5. Unit Tests for Event Publishing
#### Add tests to verify that events are published correctly to RabbitMQ.

class TestEventPublisher(unittest.TestCase):
    def setUp(self):
        self.direccion = Direccion("Calle Falsa 123", "Quito")
        self.ruc = RUC("1234567890001")
        self.forma_pago = FormaPago("Efectivo", Decimal('100.00'))
        self.inventario_service = Mock(spec=InventarioService)
        self.rabbitmq_publisher = Mock(spec=RabbitMQPublisher)

    @patch('pika.BlockingConnection')
    def test_publish_factura_events(self, mock_pika):
        # Arrange
        factura = Factura(
            id_factura=1,
            id_sucursal=1,
            id_bodega=1,
            ruc_emisor=self.ruc,
            identificacion_adquiriente="0987654321",
            razon_social_emisor="Empresa XYZ",
            direccion_matriz=self.direccion,
            fecha_emision=date.today(),
            fecha_caducidad=date.today(),
            fecha_autorizacion=date.today(),
            forma_pago=self.forma_pago
        )
        totales = TotalesFactura(id_factura=1)
        aggregate = FacturaAggregate(factura, totales)
        linea = LineaFactura(
            id_producto=1,
            descripcion="Producto 1",
            cantidad=5,
            precio_unitario=Precio(Decimal('10.00'))
        )
        aggregate.agregar_linea(linea)
        self.inventario_service.obtener_inventarios_por_bodega.return_value = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=10)
        ]

        # Act
        events = aggregate.emitir(self.inventario_service)
        for event in events:
            self.rabbitmq_publisher.publish(event)

        # Assert
        self.assertEqual(self.rabbitmq_publisher.publish.call_count, 2)
        calls = self.rabbitmq_publisher.publish.call_args_list
        self.assertEqual(calls[0][0][0].event_type, "FacturaEmitida")
        self.assertEqual(calls[1][0][0].event_type, "StockReducido")
        self.assertEqual(calls[1][0][0].data["cantidad"], 5)

    @patch('pika.BlockingConnection')
    def test_publish_nota_credito_events(self, mock_pika):
        # Arrange
        nota_credito = NotaCredito(
            id_nota_credito=1,
            id_sucursal=1,
            ruc_emisor=self.ruc,
            id_factura_modificada=1,
            identificacion_adquiriente="0987654321",
            razon_social_emisor="Empresa XYZ",
            direccion_matriz=self.direccion,
            motivo_modificacion=MotivoModificacion("Devolución"),
            fecha_emision=date.today(),
            fecha_caducidad=date.today(),
            fecha_autorizacion=date.today()
        )
        totales = TotalesNotaCredito(id_nota_credito=1)
        aggregate = NotaCreditoAggregate(nota_credito, totales)
        linea = LineaNotaCredito(
            id_producto=1,
            descripcion="Devolución Producto 1",
            cantidad=2,
            valor_item_cobrado=Decimal('10.00')
        )
        aggregate.agregar_linea(linea)
        self.inventario_service.obtener_inventarios_por_bodega.return_value = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=10)
        ]
        factura_agg = Mock()
        factura_agg.root.id_bodega = 1

        # Act
        events = aggregate.emitir(self.inventario_service, bodega_id=1, factura_agg=factura_agg)
        for event in events:
            self.rabbitmq_publisher.publish(event)

        # Assert
        self.assertEqual(self.rabbitmq_publisher.publish.call_count, 2)
        calls = self.rabbitmq_publisher.publish.call_args_list
        self.assertEqual(calls[0][0][0].event_type, "NotaCreditoEmitida")
        self.assertEqual(calls[1][0][0].event_type, "StockIncrementado")
        self.assertEqual(calls[1][0][0].data["cantidad"], 2)

    @patch('pika.BlockingConnection')
    def test_rabbitmq_publisher_sends_message(self, mock_pika):
        # Arrange
        publisher = RabbitMQPublisher(host="localhost", exchange="facturacion")
        mock_channel = Mock()
        mock_pika.return_value.channel.return_value = mock_channel
        event = FacturaEmitida(1, {
            "id_factura": 1,
            "id_sucursal": 1,
            "id_bodega": 1,
            "fecha_emision": date.today().isoformat()
        })

        # Act
        publisher.publish(event)

        # Assert
        mock_channel.basic_publish.assert_called_once()
        args, kwargs = mock_channel.basic_publish.call_args
        self.assertEqual(kwargs['exchange'], "facturacion")
        self.assertEqual(kwargs['routing_key'], "facturacion.facturaemitida")
        self.assertIn('"event_type": "FacturaEmitida"', kwargs['body'].decode())