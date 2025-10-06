# domain/aggregates/factura_aggregate.py
from typing import List
from decimal import Decimal
from domain.entities.factura import Factura
from domain.entities.totales_factura import TotalesFactura
from domain.services.inventario_service import InventarioService  # Para FIFO
from domain.entities.movimiento_inventario import MovimientoInventario  # Importar clase faltante
from domain.entities.linea_factura import LineaFactura  # Importar clase faltante
from domain.entities.direccion import Direccion  # Importar clase Direccion
from domain.entities.ruc import RUC  # Importar clase RUC

class FacturaAggregate:
    def __init__(self, factura: Factura, totales: TotalesFactura):
        self.root = factura
        self.root.totales = totales  # Asegurar asociación
        self._invariantes = []  # Lista para registrar invariantes personalizados

    def agregar_linea(self, linea: LineaFactura):
        self.root.agregar_linea(linea)
        self._verificar_invariantes()

    def aplicar_descuento_global(self, porcentaje: Decimal):
        for linea in self.root.lineas:
            linea.aplicar_descuento(porcentaje)
        self.root._actualizar_totales()
        self._verificar_invariantes()

    def emitir(self, inventario_service: InventarioService) -> List['MovimientoInventario']:
        self.root.validar_emision()
        movimientos = []
        for linea in self.root.lineas:
            # Registrar salida FIFO por cada producto
            movs = inventario_service.registrar_salida_fifo(
                producto_id=linea.id_producto,
                bodega_id=self.root.id_bodega,
                cantidad=linea.cantidad,
                factura_id=self.root.id_factura
            )
            movimientos.extend(movs)
        # Disparar evento: FacturaEmitida(self.root.id_factura, movimientos)
        return movimientos

    def _verificar_invariantes(self):
        if self.root.totales.valor_total != sum(linea.valor_total for linea in self.root.lineas) + self.root.totales.valor_iva:
            raise ValueError("Invariante violado: Totales inconsistentes.")
        # Agregar más: e.g., forma_pago.valor == totales.valor_total

    @classmethod
    def crear_nueva(cls, id_sucursal: int, ruc_emisor: str, adquiriente: str, direccion: Direccion, razon_social: str):
        factura = Factura(
            id_sucursal=id_sucursal,
            ruc_emisor=RUC(ruc_emisor),
            identificacion_adquiriente=adquiriente,
            razon_social_emisor=razon_social,
            direccion_matriz=direccion
        )
        totales = TotalesFactura(0)  # ID temporal
        return cls(factura, totales)