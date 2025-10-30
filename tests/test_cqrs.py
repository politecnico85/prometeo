import unittest
from unittest.mock import Mock
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
from domain.services.event_handler import EventHandler
from domain.services.query_service import QueryService
from infrastructure.persistence.projection_sql import ProjectionRepository
from domain.events.factura_events import FacturaEmitida, StockReducido
from domain.events.nota_credito_events import NotaCreditoEmitida, StockIncrementado

class TestCQRS(unittest.TestCase):
    def setUp(self):
        self.direccion = Direccion("Calle Falsa 123", "Quito")
        self.ruc = RUC("1234567890001")
        self.forma_pago = FormaPago("Efectivo", Decimal('100.00'))
        self.inventario_service = Mock(spec=InventarioService)
        self.projection_repository = Mock(spec=ProjectionRepository)
        self.event_handler = EventHandler(self.inventario_service, self.projection_repository)
        self.query_service = QueryService(self.projection_repository)

    def test_stock_projection_updated_on_stock_reducido(self):
        # Arrange
        event = StockReducido(
            aggregate_id=1,
            producto_id=1,
            bodega_id=1,
            cantidad=5,
            costo_unitario=10.0
        )
        self.projection_repository.get_stock.return_value = 10.0

        # Act
        self.event_handler.handle(event)

        # Assert
        self.projection_repository.update_stock.assert_called_once_with(1, 1, 5.0)
        self.inventario_service.registrar_salida_fifo.assert_called_once_with(
            producto_id=1, bodega_id=1, cantidad=5, factura_id=1
        )

    def test_stock_projection_updated_on_stock_incrementado(self):
        # Arrange
        event = StockIncrementado(
            aggregate_id=1,
            producto_id=1,
            bodega_id=1,
            cantidad=3,
            costo_unitario=10.0
        )
        self.projection_repository.get_stock.return_value = 10.0

        # Act
        self.event_handler.handle(event)

        # Assert
        self.projection_repository.update_stock.assert_called_once_with(1, 1, 13.0)
        self.inventario_service.registrar_entrada.assert_called_once_with(
            producto_id=1, bodega_id=1, cantidad=3, costo_unitario=Decimal('10.0'), nota_credito_id=1
        )

    def test_factura_projection_updated(self):
        # Arrange
        event = FacturaEmitida(1, {
            "id_factura": 1,
            "id_sucursal": 1,
            "id_bodega": 1,
            "ruc_emisor": "1234567890001",
            "identificacion_adquiriente": "0987654321",
            "razon_social_emisor": "Empresa XYZ",
            "fecha_emision": date.today().isoformat(),
            "total": 20.0
        })

        # Act
        self.event_handler.handle(event)

        # Assert
        self.projection_repository.save_factura.assert_called_once_with(event.data)

    def test_nota_credito_projection_updated(self):
        # Arrange
        event = NotaCreditoEmitida(1, {
            "id_nota_credito": 1,
            "id_sucursal": 1,
            "id_factura_modificada": 1,
            "motivo": "Devolución",
            "fecha_emision": date.today().isoformat(),
            "total": 10.0
        })

        # Act
        self.event_handler.handle(event)

        # Assert
        self.projection_repository.save_nota_credito.assert_called_once_with(event.data)

    def test_query_service_get_stock(self):
        # Arrange
        self.projection_repository.get_stock.return_value = 15.0

        # Act
        stock = self.query_service.get_stock(producto_id=1, bodega_id=1)

        # Assert
        self.assertEqual(stock, 15.0)
        self.projection_repository.get_stock.assert_called_once_with(1, 1)

    def test_query_service_get_factura(self):
        # Arrange
        factura_data = {
            "id_factura": 1,
            "id_sucursal": 1,
            "id_bodega": 1,
            "ruc_emisor": "1234567890001",
            "identificacion_adquiriente": "0987654321",
            "razon_social_emisor": "Empresa XYZ",
            "fecha_emision": date.today().isoformat(),
            "total": 20.0
        }
        self.projection_repository.get_factura.return_value = factura_data

        # Act
        result = self.query_service.get_factura(id_factura=1)

        # Assert
        self.assertEqual(result, factura_data)
        self.projection_repository.get_factura.assert_called_once_with(1)

    def test_query_service_get_nota_credito(self):
        # Arrange
        nota_credito_data = {
            "id_nota_credito": 1,
            "id_sucursal": 1,
            "id_factura_modificada": 1,
            "motivo": "Devolución",
            "fecha_emision": date.today().isoformat(),
            "total": 10.0
        }
        self.projection_repository.get_nota_credito.return_value = nota_credito_data

        # Act
        result = self.query_service.get_nota_credito(id_nota_credito=1)

        # Assert
        self.assertEqual(result, nota_credito_data)
        self.projection_repository.get_nota_credito.assert_called_once_with(1)