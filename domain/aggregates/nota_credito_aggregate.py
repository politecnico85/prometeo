# domain/aggregates/nota_credito_aggregate.py
from typing import List
from uuid import uuid4
from datetime import date
from domain.entities.nota_credito import NotaCredito
from domain.entities.totales_nota_credito import TotalesNotaCredito
from domain.entities.linea_nota_credito import LineaNotaCredito
from domain.entities.motivo_modificacion import MotivoModificacion
from domain.entities.direccion import Direccion
from domain.services.inventario_service import InventarioService
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.specifications.nota_credito_specifications import (
    NotaCreditoTieneLineas, NotaCreditoTotalValido, MotivoModificacionValido,
    FechaEmisionValida, FechaCaducidadValida, FechaAutorizacionValida
)

class NotaCreditoAggregate:
    def __init__(self, nota_credito: NotaCredito, totales: TotalesNotaCredito):
        self.root = nota_credito
        self.root.totales = totales
        self._validaciones = [
            NotaCreditoTieneLineas(),
            NotaCreditoTotalValido(),
            MotivoModificacionValido(),
            FechaEmisionValida(),
            FechaCaducidadValida(),
            FechaAutorizacionValida()
        ]

    def agregar_linea(self, linea: LineaNotaCredito):
        self.root.agregar_linea(linea)
        self._verificar_invariantes()

    def emitir(self, inventario_service: InventarioService, bodega_id: int, factura_agg: 'FacturaAggregate') -> List['MovimientoInventario']:
        self._verificar_invariantes()
        movimientos = []
        for linea in self.root.lineas:
            movs = inventario_service.registrar_entrada(
                producto_id=linea.id_producto,
                bodega_id=bodega_id,
                cantidad=linea.cantidad,
                costo_unitario=linea.valor_item_cobrado,
                nota_credito_id=self.root.id_nota_credito
            )
            movimientos.extend(movs)
        return movimientos

    def _verificar_invariantes(self):
        errors = []
        for spec in self._validaciones:
            if not spec.is_satisfied_by(self.root):
                errors.append(f"Validación fallida: {spec.__class__.__name__}")
        if errors:
            raise ValueError("; ".join(errors))

    @classmethod
    def crear_nueva(cls, id_sucursal: int, ruc_emisor: str, id_factura_modificada: int, adquiriente: str, 
                    direccion: 'Direccion', razon_social: str, motivo: str, 
                    fecha_emision: date = None, fecha_caducidad: date = None, fecha_autorizacion: date = None):
        nota_credito = NotaCredito(
            id_sucursal=id_sucursal,
            ruc_emisor=RUC(ruc_emisor),
            id_factura_modificada=id_factura_modificada,
            identificacion_adquiriente=adquiriente,
            razon_social_emisor=razon_social,
            direccion_matriz=direccion,
            motivo_modificacion=MotivoModificacion(motivo),
            fecha_emision=fecha_emision or date.today(),
            fecha_caducidad=fecha_caducidad,
            fecha_autorizacion=fecha_autorizacion or date.today()
        )
        totales = TotalesNotaCredito(0)
        aggregate = cls(nota_credito, totales)
        aggregate._verificar_invariantes()  # Validar al crear
        return aggregate
