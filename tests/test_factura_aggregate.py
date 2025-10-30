import unittest
from unittest.mock import Mock
from datetime import date, datetime
from decimal import Decimal
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.entities.factura import Factura
from domain.entities.linea_factura import LineaFactura
from domain.entities.totales_factura import TotalesFactura
from domain.entities.inventario import Inventario
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.forma_pago import FormaPago
from domain.value_objects.precio import Precio
from domain.services.inventario_service import InventarioService
from domain.specifications.inventario_specifications import StockSuficienteParaFactura

class TestFacturaAggregate(unittest.TestCase):
    def setUp(self):
        self.direccion = Direccion("Calle Falsa 123", "Quito")
        self.ruc = RUC("1234567890001")
        self.forma_pago = FormaPago("Efectivo", Decimal('100.00'))
        self.factura = Factura(
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
        self.totales = TotalesFactura(id_factura=0)
        self.aggregate = FacturaAggregate(self.factura, self.totales)
        self.inventario_service = Mock(spec=InventarioService)

    def test_stock_suficiente_para_factura(self):
        # Arrange
        linea = LineaFactura(
            id_producto=1,
            descripcion="Producto 1",
            cantidad=5,
            precio_unitario=Precio(Decimal('10.00'))
        )
        self.aggregate.agregar_linea(linea)
        inventarios = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=10)
        ]
        self.inventario_service.obtener_inventarios_por_bodega.return_value = inventarios
        self.inventario_service.registrar_salida_fifo.return_value = [
            MovimientoInventario(
                id_producto=1,
                id_bodega=1,
                id_factura=1,
                tipo_movimiento='SALIDA',
                cantidad=5,
                costo_unitario_aplicado=Decimal('8.00'),
                fecha_movimiento=datetime.now(),
                stock_post_movimiento=5
            )
        ]

        # Act
        movimientos = self.aggregate.emitir(self.inventario_service)

        # Assert
        self.assertEqual(len(movimientos), 1)
        self.inventario_service.obtener_inventarios_por_bodega.assert_called_with(1)
        self.inventario_service.registrar_salida_fifo.assert_called_with(
            producto_id=1, bodega_id=1, cantidad=5, factura_id=None
        )

    def test_stock_insuficiente_raises_error(self):
        # Arrange
        linea = LineaFactura(
            id_producto=1,
            descripcion="Producto 1",
            cantidad=10,
            precio_unitario=Precio(Decimal('10.00'))
        )
        self.aggregate.agregar_linea(linea)
        inventarios = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=5)
        ]
        self.inventario_service.obtener_inventarios_por_bodega.return_value = inventarios

        # Act & Assert
        with self.assertRaises(ValueError) as cm:
            self.aggregate.emitir(self.inventario_service)
        self.assertEqual(str(cm.exception), "Stock insuficiente para emitir la factura.")

    def test_no_inventario_raises_error(self):
        # Arrange
        linea = LineaFactura(
            id_producto=1,
            descripcion="Producto 1",
            cantidad=5,
            precio_unitario=Precio(Decimal('10.00'))
        )
        self.aggregate.agregar_linea(linea)
        self.inventario_service.obtener_inventarios_por_bodega.return_value = []

        # Act & Assert
        with self.assertRaises(ValueError) as cm:
            self.aggregate.emitir(self.inventario_service)
        self.assertEqual(str(cm.exception), "Stock insuficiente para emitir la factura.")