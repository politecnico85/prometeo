import unittest
from unittest.mock import Mock
from datetime import date, datetime, timedelta
from decimal import Decimal
from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.entities.nota_credito import NotaCredito
from domain.entities.linea_nota_credito import LineaNotaCredito
from domain.entities.totales_nota_credito import TotalesNotaCredito
from domain.entities.factura import Factura
from domain.entities.linea_factura import LineaFactura
from domain.entities.totales_factura import TotalesFactura
from domain.entities.inventario import Inventario
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.motivo_modificacion import MotivoModificacion
from domain.value_objects.forma_pago import FormaPago
from domain.value_objects.precio import Precio
from domain.services.inventario_service import InventarioService
from domain.specifications.nota_credito_specifications import InventarioExisteParaNotaCredito, LineasValidasContraFactura

class TestNotaCreditoAggregate(unittest.TestCase):
    def setUp(self):
        self.direccion = Direccion("Calle Falsa 123", "Quito")
        self.ruc = RUC("1234567890001")
        self.forma_pago = FormaPago("Efectivo", Decimal('100.00'))
        self.factura = Factura(
            id_factura=1,
            id_sucursal=1,
            id_bodega=1,
            ruc_emisor=self.ruc,
            identificacion_adquiriente="0987654321",
            razon_social_emisor="Empresa XYZ",
            direccion_matriz=self.direccion,
            fecha_emision=date.today() - timedelta(days=10),
            fecha_caducidad=date.today(),
            fecha_autorizacion=date.today(),
            forma_pago=self.forma_pago
        )
        self.factura.lineas = [
            LineaFactura(id_producto=1, descripcion="Producto 1", cantidad=10, precio_unitario=Precio(Decimal('10.00')))
        ]
        self.factura_agg = FacturaAggregate(self.factura, TotalesFactura(id_factura=1))
        self.nota_credito = NotaCredito(
            id_sucursal=1,
            ruc_emisor=self.ruc,
            id_factura_modificada=1,
            identificacion_adquiriente="0987654321",
            razon_social_emisor="Empresa XYZ",
            direccion_matriz=self.direccion,
            motivo_modificacion=MotivoModificacion("Devolución por error"),
            fecha_emision=date.today(),
            fecha_caducidad=date.today(),
            fecha_autorizacion=date.today()
        )
        self.totales = TotalesNotaCredito(id_nota_credito=0)
        self.aggregate = NotaCreditoAggregate(self.nota_credito, self.totales)
        self.inventario_service = Mock(spec=InventarioService)

    def test_inventario_existe_para_nota_credito(self):
        # Arrange
        linea = LineaNotaCredito(
            id_producto=1,
            descripcion="Devolución Producto 1",
            cantidad=5,
            valor_item_cobrado=Decimal('10.00')
        )
        self.aggregate.agregar_linea(linea)
        inventarios = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=10)
        ]
        self.inventario_service.obtener_inventarios_por_bodega.return_value = inventarios
        self.inventario_service.registrar_entrada.return_value = [
            MovimientoInventario(
                id_producto=1,
                id_bodega=1,
                id_factura=None,
                tipo_movimiento='ENTRADA',
                cantidad=5,
                costo_unitario_aplicado=Decimal('10.00'),
                fecha_movimiento=datetime.now(),
                stock_post_movimiento=15
            )
        ]

        # Act
        movimientos = self.aggregate.emitir(self.inventario_service, bodega_id=1, factura_agg=self.factura_agg)

        # Assert
        self.assertEqual(len(movimientos), 1)
        self.inventario_service.obtener_inventarios_por_bodega.assert_called_with(1)
        self.inventario_service.registrar_entrada.assert_called_with(
            producto_id=1, bodega_id=1, cantidad=5, costo_unitario=Decimal('10.00'), nota_credito_id=None
        )

    def test_inventario_no_existe_raises_error(self):
        # Arrange
        linea = LineaNotaCredito(
            id_producto=1,
            descripcion="Devolución Producto 1",
            cantidad=5,
            valor_item_cobrado=Decimal('10.00')
        )
        self.aggregate.agregar_linea(linea)
        self.inventario_service.obtener_inventarios_por_bodega.return_value = []

        # Act & Assert
        with self.assertRaises(ValueError) as cm:
            self.aggregate.emitir(self.inventario_service, bodega_id=1, factura_agg=self.factura_agg)
        self.assertEqual(str(cm.exception), "Inventario no encontrado para los productos en la bodega especificada.")

    def test_lineas_validas_contra_factura(self):
        # Arrange
        linea = LineaNotaCredito(
            id_producto=1,
            descripcion="Devolución Producto 1",
            cantidad=5,
            valor_item_cobrado=Decimal('10.00')
        )
        self.aggregate.agregar_linea(linea)
        spec = LineasValidasContraFactura(self.factura_agg)

        # Act
        result = spec.is_satisfied_by(self.nota_credito)

        # Assert
        self.assertTrue(result)

    def test_lineas_invalidas_contra_factura_raises_error(self):
        # Arrange
        linea = LineaNotaCredito(
            id_producto=1,
            descripcion="Devolución Producto 1",
            cantidad=15,  # Exceeds factura quantity
            valor_item_cobrado=Decimal('10.00')
        )
        self.aggregate.agregar_linea(linea)
        spec = LineasValidasContraFactura(self.factura_agg)

        # Act & Assert
        self.assertFalse(spec.is_satisfied_by(self.nota_credito))