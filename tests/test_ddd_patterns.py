
#### 6. Unit Tests for DDD Patterns
#### Add tests to verify enhanced DDD patterns.


# tests/test_ddd_patterns.py
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
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.forma_pago import FormaPago
from domain.value_objects.motivo_modificacion import MotivoModificacion
from domain.value_objects.precio import Precio
from domain.services.inventario_service import InventarioService
from domain.services.validation_service import ValidationService
from domain.events.factura_events import FacturaEmitida, StockReducido
from domain.events.nota_credito_events import NotaCreditoEmitida, StockIncrementado

class TestDDDPpatterns(unittest.TestCase):
    def setUp(self):
        self.direccion = Direccion("Calle Falsa 123", "Quito")
        self.ruc = RUC("1234567890001")
        self.forma_pago = FormaPago("Efectivo", Decimal('100.00'))
        self.inventario_service = Mock(spec=InventarioService)
        self.validation_service = ValidationService(self.inventario_service)

    def test_factura_aggregate_invariant(self):
        # Arrange
        aggregate = FacturaAggregate.crear_nueva(
            id_sucursal=1, id_bodega=1, ruc_emisor="1234567890001",
            adquiriente="0987654321", direccion="Calle Falsa 123",
            razon_social="Empresa XYZ", forma_pago="Efectivo",
            fecha_emision=date.today()
        )
        linea = LineaFactura(id_producto=1, descripcion="Producto 1", cantidad=0, precio_unitario=Precio(Decimal('10.00')))

        # Act & Assert
        with self.assertRaises(ValueError, msg="La cantidad debe ser mayor a cero"):
            aggregate.agregar_linea(linea)

    def test_nota_credito_aggregate_invariant(self):
        # Arrange
        aggregate = NotaCreditoAggregate.crear_nueva(
            id_sucursal=1, ruc_emisor="1234567890001", id_factura_modificada=1,
            adquiriente="0987654321", direccion="Calle Falsa 123",
            razon_social="Empresa XYZ", motivo="Devolución",
            fecha_emision=date.today()
        )
        linea = LineaNotaCredito(id_producto=1, descripcion="Devolución Producto 1", cantidad=0, valor_item_cobrado=Decimal('10.00'))

        # Act & Assert
        with self.assertRaises(ValueError, msg="La cantidad debe ser mayor a cero"):
            aggregate.agregar_linea(linea)

    def test_ruc_validation(self):
        # Act & Assert
        with self.assertRaises(ValueError, msg="RUC inválido"):
            RUC("1234567890002")  # Invalid check digit

    def test_validation_service_factura(self):
        # Arrange
        aggregate = FacturaAggregate.crear_nueva(
            id_sucursal=1, id_bodega=1, ruc_emisor="1234567890001",
            adquiriente="0987654321", direccion="Calle Falsa 123",
            razon_social="Empresa XYZ", forma_pago="Efectivo",
            fecha_emision=date.today()
        )
        self.inventario_service.obtener_inventarios_por_bodega.return_value = []

        # Act
        errors = self.validation_service.validate_factura(aggregate)

        # Assert
        self.assertTrue(len(errors) > 0)
        self.assertIn("Validación fallida: StockSuficienteParaFactura", errors)

    def test_validation_service_nota_credito(self):
        # Arrange
        factura_agg = Mock()
        factura_agg.root.id_bodega = 1
        aggregate = NotaCreditoAggregate.crear_nueva(
            id_sucursal=1, ruc_emisor="1234567890001", id_factura_modificada=1,
            adquiriente="0987654321", direccion="Calle Falsa 123",
            razon_social="Empresa XYZ", motivo="Devolución",
            fecha_emision=date.today()
        )
        self.inventario_service.obtener_inventarios_por_bodega.return_value = []

        # Act
        errors = self.validation_service.validate_nota_credito(aggregate, factura_agg)

        # Assert
        self.assertTrue(len(errors) > 0)
        self.assertIn("Validación fallida: InventarioExisteParaNotaCredito", errors)

    def test_factura_event_versioning(self):
        # Arrange
        aggregate = FacturaAggregate.crear_nueva(
            id_sucursal=1, id_bodega=1, ruc_emisor="1234567890001",
            adquiriente="0987654321", direccion="Calle Falsa 123",
            razon_social="Empresa XYZ", forma_pago="Efectivo",
            fecha_emision=date.today()
        )
        self.inventario_service.obtener_inventarios_por_bodega.return_value = [
            Mock(cantidad=10, id_producto=1)
        ]

        # Act
        events = aggregate.emitir(self.inventario_service)

        # Assert
        self.assertEqual(events[0].event_version, 1)
        self.assertEqual(events[1].event_version, 1)
