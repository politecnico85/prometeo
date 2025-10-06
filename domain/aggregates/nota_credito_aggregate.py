# domain/aggregates/nota_credito_aggregate.py
from typing import List
from domain.entities.nota_credito import NotaCredito
from domain.entities.totales_nota_credito import TotalesNotaCredito
from domain.services.inventario_service import InventarioService  # Para ajustes de stock (entradas)
from domain.entities.linea_nota_credito import LineaNotaCredito  # Importar la clase faltante
from domain.entities.motivo_modificacion import MotivoModificacion  # Importar la clase MotivoModificacion
from domain.value_objects.ruc import RUC  # Importar la clase RUC
from domain.entities.movimiento_inventario import MovimientoInventario  # Importar la clase MovimientoInventario
from domain.value_objects.direccion import Direccion  # Importar la clase Direccion

class NotaCreditoAggregate:
    def __init__(self, nota_credito: NotaCredito, totales: TotalesNotaCredito):
        self.root = nota_credito
        self.root.totales = totales  # Asegurar asociación
        self._invariantes = []  # Lista para invariantes

    def agregar_linea(self, linea: LineaNotaCredito):
        self.root.agregar_linea(linea)
        self._verificar_invariantes()

    def emitir(self, inventario_service: InventarioService, bodega_id: int) -> List['MovimientoInventario']:
        self.root.validar_emision()
        movimientos = []
        for linea in self.root.lineas:
            # Registrar entrada (reverso de salida) - Asumir lógica similar a FIFO pero para entradas
            # Para simplicidad, usa un método de service para entradas; ajusta FIFO si aplica
            movs = inventario_service.registrar_entrada(
                producto_id=linea.id_producto,
                bodega_id=bodega_id,  # Asumir de factura original
                cantidad=linea.cantidad,
                costo_unitario=linea.valor_item_cobrado,  # O recuperar de lote original
                nota_credito_id=self.root.id_nota_credito
            )
            movimientos.extend(movs)
        # Disparar evento: NotaCreditoEmitida(self.root.id_nota_credito, movimientos)
        # Actualizar factura original? (e.g., marcar como modificada vía event)
        return movimientos

    def _verificar_invariantes(self):
        if self.root.totales.valor_total != sum(linea.valor_total for linea in self.root.lineas) + self.root.totales.valor_iva:
            raise ValueError("Invariante violado: Totales inconsistentes.")
        # Más: e.g., total <= total de factura original (validar en service)

    @classmethod
    def crear_nueva(cls, id_sucursal: int, ruc_emisor: str, id_factura_modificada: int, adquiriente: str, direccion: Direccion, razon_social: str, motivo: str):
        nota_credito = NotaCredito(
            id_sucursal=id_sucursal,
            ruc_emisor=RUC(ruc_emisor),
            id_factura_modificada=id_factura_modificada,
            identificacion_adquiriente=adquiriente,
            razon_social_emisor=razon_social,
            direccion_matriz=direccion,
            motivo_modificacion=MotivoModificacion(motivo)
        )
        totales = TotalesNotaCredito(0)  # ID temporal
        return cls(nota_credito, totales)