
#### 6. Unit Tests for Snapshots
####Add tests to verify snapshot creation, storage, and aggregate reconstruction.


# tests/test_snapshots.py
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
from infrastructure.persistence.event_store_sql import EventStore
from infrastructure.persistence.snapshot_sql import SnapshotRepository
from domain.events.factura_events import FacturaEmitida, StockReducido
from domain.events.nota_credito_events import NotaCreditoEmitida, StockIncrementado
import json

class TestSnapshots(unittest.TestCase):
    def setUp(self):
        self.direccion = Direccion("Calle Falsa 123", "Quito")
        self.ruc = RUC("1234567890001")
        self.forma_pago = FormaPago("Efectivo", Decimal('100.00'))
        self.inventario_service = Mock(spec=InventarioService)
        self.event_store = Mock(spec=EventStore)
        self.snapshot_repository = Mock(spec=SnapshotRepository)

    def test_factura_aggregate_snapshot_creation(self):
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
            cantidad=2,
            precio_unitario=Precio(Decimal('10.00'))
        )
        aggregate.agregar_linea(linea)
        self.inventario_service.obtener_inventarios_por_bodega.return_value = []
        aggregate.emitir(self.inventario_service)  # Generates events
        aggregate._version = 11  # Simulate enough events for snapshot

        # Act
        snapshot = aggregate.to_snapshot()

        # Assert
        self.assertEqual(snapshot["factura"]["id_factura"], 1)
        self.assertEqual(snapshot["factura"]["lineas"][0]["cantidad"], 2)
        self.assertEqual(snapshot["version"], 11)

    def test_nota_credito_aggregate_snapshot_creation(self):
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
        factura_agg = Mock()
        self.inventario_service.obtener_inventarios_por_bodega.return_value = []
        aggregate.emitir(self.inventario_service, 1, factura_agg)
        aggregate._version = 11  # Simulate enough events for snapshot

        # Act
        snapshot = aggregate.to_snapshot()

        # Assert
        self.assertEqual(snapshot["nota_credito"]["id_nota_credito"], 1)
        self.assertEqual(snapshot["nota_credito"]["lineas"][0]["cantidad"], 2)
        self.assertEqual(snapshot["version"], 11)

    def test_factura_repository_saves_snapshot(self):
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
        aggregate._version = 11  # Simulate enough events
        events = [FacturaEmitida(1, {}), StockReducido(1, 1, 1, 2, 10.0)]
        aggregate._pending_events = events
        repository = FacturaRepository(self.event_store, self.snapshot_repository, snapshot_frequency=10)

        # Act
        repository.guardar(aggregate)

        # Assert
        self.snapshot_repository.save_snapshot.assert_called_once()
        args = self.snapshot_repository.save_snapshot.call_args[0]
        self.assertEqual(args[0], 1)  # aggregate_id
        self.assertEqual(args[1], "Factura")  # aggregate_type
        self.assertEqual(args[2], 11)  # version

    def test_factura_repository_loads_from_snapshot(self):
        # Arrange
        snapshot = {
            "factura": {
                "id_factura": 1,
                "id_sucursal": 1,
                "id_bodega": 1,
                "ruc_emisor": "1234567890001",
                "identificacion_adquiriente": "0987654321",
                "razon_social_emisor": "Empresa XYZ",
                "direccion_matriz": {"calle": "Calle Falsa 123", "ciudad": "Quito"},
                "fecha_emision": date.today().isoformat(),
                "fecha_caducidad": date.today().isoformat(),
                "fecha_autorizacion": date.today().isoformat(),
                "forma_pago": {"metodo": "Efectivo", "monto": 100.0},
                "lineas": [
                    {"id_producto": 1, "descripcion": "Producto 1", "cantidad": 2, "precio_unitario": 10.0}
                ]
            },
            "totales": {"subtotal": 20.0, "total_con_impuestos": 22.4},
            "version": 10
        }
        self.snapshot_repository.get_snapshot.return_value = (snapshot, 10)
        self.event_store.get_events.return_value = [FacturaEmitida(1, {})]
        repository = FacturaRepository(self.event_store, self.snapshot_repository)

        # Act
        aggregate = repository.obtener_por_id(1)

        # Assert
        self.assertEqual(aggregate.root.id_factura, 1)
        self.assertEqual(aggregate._version, 11)  # 10 from snapshot + 1 event
        self.assertEqual(len(aggregate.root.lineas), 1)
        self.assertEqual(aggregate.root.lineas[0].cantidad, 2)

    def test_nota_credito_repository_saves_snapshot(self):
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
        aggregate._version = 11
        events = [NotaCreditoEmitida(1, {}), StockIncrementado(1, 1, 1, 2, 10.0)]
        aggregate._pending_events = events
        repository = NotaCreditoRepository(self.event_store, self.snapshot_repository, snapshot_frequency=10)

        # Act
        repository.guardar(aggregate)

        # Assert
        self.snapshot_repository.save_snapshot.assert_called_once()
        args = self.snapshot_repository.save_snapshot.call_args[0]
        self.assertEqual(args[0], 1)  # aggregate_id
        self.assertEqual(args[1], "NotaCredito")  # aggregate_type
        self.assertEqual(args[2], 11)  # version

    def test_nota_credito_repository_loads_from_snapshot(self):
        # Arrange
        snapshot = {
            "nota_credito": {
                "id_nota_credito": 1,
                "id_sucursal": 1,
                "ruc_emisor": "1234567890001",
                "id_factura_modificada": 1,
                "identificacion_adquiriente": "0987654321",
                "razon_social_emisor": "Empresa XYZ",
                "direccion_matriz": {"calle": "Calle Falsa 123", "ciudad": "Quito"},
                "motivo_modificacion": "Devolución",
                "fecha_emision": date.today().isoformat(),
                "fecha_caducidad": date.today().isoformat(),
                "fecha_autorizacion": date.today().isoformat(),
                "lineas": [
                    {"id_producto": 1, "descripcion": "Devolución Producto 1", "cantidad": 2, "valor_item_cobrado": 10.0}
                ]
            },
            "totales": {"subtotal": 20.0, "total_con_impuestos": 22.4},
            "version": 10
        }
        self.snapshot_repository.get_snapshot.return_value = (snapshot, 10)
        self.event_store.get_events.return_value = [NotaCreditoEmitida(1, {})]
        repository = NotaCreditoRepository(self.event_store, self.snapshot_repository)

        # Act
        aggregate = repository.obtener_por_id(1)

        # Assert
        self.assertEqual(aggregate.root.id_nota_credito, 1)
        self.assertEqual(aggregate._version, 11)  # 10 from snapshot + 1 event
        self.assertEqual(len(aggregate.root.lineas), 1)
        self.assertEqual(aggregate.root.lineas[0].cantidad, 2)
