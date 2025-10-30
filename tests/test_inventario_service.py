import unittest
from unittest.mock import Mock
from datetime import date, datetime
from decimal import Decimal
from domain.services.inventario_service import InventarioService
from domain.entities.inventario import Inventario
from domain.entities.lote import Lote
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.repositories.inventario_repository import InventarioRepository
from domain.repositories.lote_repository import LoteRepository

class TestInventarioService(unittest.TestCase):
    def setUp(self):
        self.inventario_repo = Mock(spec=InventarioRepository)
        self.lote_repo = Mock(spec=LoteRepository)
        self.service = InventarioService(self.inventario_repo, self.lote_repo)

    def test_registrar_salida_fifo_suficiente(self):
        # Arrange
        inventarios = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=10)
        ]
        lotes = [
            Lote(id_lote=1, id_producto=1, id_bodega=1, fecha_compra=date.today(), 
                 cantidad_inicial=10, cantidad_restante=10, costo_unitario=Decimal('8.00'))
        ]
        self.inventario_repo.obtener_por_bodega.return_value = inventarios
        self.lote_repo.obtener_lotes_antiguos.return_value = lotes

        # Act
        movimientos = self.service.registrar_salida_fifo(
            producto_id=1, bodega_id=1, cantidad=5, factura_id=1
        )

        # Assert
        self.assertEqual(len(movimientos), 1)
        self.assertEqual(movimientos[0].cantidad, 5)
        self.assertEqual(movimientos[0].tipo_movimiento, 'SALIDA')
        self.assertEqual(movimientos[0].stock_post_movimiento, 5)
        self.lote_repo.actualizar.assert_called_once()
        self.inventario_repo.actualizar.assert_called_once()

    def test_registrar_salida_fifo_insuficiente(self):
        # Arrange
        inventarios = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=3)
        ]
        lotes = [
            Lote(id_lote=1, id_producto=1, id_bodega=1, fecha_compra=date.today(), 
                 cantidad_inicial=3, cantidad_restante=3, costo_unitario=Decimal('8.00'))
        ]
        self.inventario_repo.obtener_por_bodega.return_value = inventarios
        self.lote_repo.obtener_lotes_antiguos.return_value = lotes

        # Act & Assert
        with self.assertRaises(ValueError) as cm:
            self.service.registrar_salida_fifo(
                producto_id=1, bodega_id=1, cantidad=5, factura_id=1
            )
        self.assertEqual(str(cm.exception), "Stock insuficiente en FIFO.")

    def test_registrar_entrada(self):
        # Arrange
        inventarios = [
            Inventario(id_inventario=1, id_producto=1, id_bodega=1, cantidad_stock=10)
        ]
        self.inventario_repo.obtener_por_bodega.return_value = inventarios
        self.lote_repo.guardar = Mock()

        # Act
        movimientos = self.service.registrar_entrada(
            producto_id=1, bodega_id=1, cantidad=5, costo_unitario=Decimal('10.00'), nota_credito_id=1
        )

        # Assert
        self.assertEqual(len(movimientos), 1)
        self.assertEqual(movimientos[0].cantidad, 5)
        self.assertEqual(movimientos[0].tipo_movimiento, 'ENTRADA')
        self.assertEqual(movimientos[0].stock_post_movimiento, 15)
        self.inventario_repo.actualizar.assert_called_once()
        self.lote_repo.guardar.assert_called_once()

    def test_registrar_entrada_no_inventario(self):
        # Arrange
        self.inventario_repo.obtener_por_bodega.return_value = []

        # Act & Assert
        with self.assertRaises(ValueError) as cm:
            self.service.registrar_entrada(
                producto_id=1, bodega_id=1, cantidad=5, costo_unitario=Decimal('10.00'), nota_credito_id=1
            )
        self.assertEqual(str(cm.exception), "Inventario no encontrado.")