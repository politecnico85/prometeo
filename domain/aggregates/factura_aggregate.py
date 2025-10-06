# domain/aggregates/factura_aggregate.py
from datetime import date
from typing import List
from domain.entities.factura import Factura
from domain.entities.totales_factura import TotalesFactura
from domain.entities.linea_factura import LineaFactura
from domain.entities.direccion import Direccion
from domain.services.inventario_service import InventarioService
from domain.entities.movimiento_inventario import MovimientoInventario
from domain.specifications.factura_specifications import (
    FacturaTieneLineas, FacturaTotalValido, FormaPagoValida,
    FechaEmisionValida, FechaCaducidadValida, FechaAutorizacionValida
)

class FacturaAggregate:
    def __init__(self, factura: Factura, totales: TotalesFactura):
        self.root = factura
        self.root.totales = totales
        self._validaciones = [
            FacturaTieneLineas(),
            FacturaTotalValido(),
            FormaPagoValida(),
            FechaEmisionValida(),
            FechaCaducidadValida(),
            FechaAutorizacionValida()
        ]

    def agregar_linea(self, linea: LineaFactura):
        self.root.agregar_linea(linea)
        self._verificar_invariantes()

    def aplicar_descuento_global(self, porcentaje: Decimal):
        for linea in self.root.lineas:
            linea.aplicar_descuento(porcentaje)
        self.root._actualizar_totales()
        self._verificar_invariantes()

    def emitir(self, inventario_service: InventarioService) -> List['MovimientoInventario']:
        self._verificar_invariantes()
        movimientos = []
        for linea in self.root.lineas:
            movs = inventario_service.registrar_salida_fifo(
                producto_id=linea.id_producto,
                bodega_id=self.root.id_bodega,
                cantidad=linea.cantidad,
                factura_id=self.root.id_factura
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
    def crear_nueva(cls, id_sucursal: int, ruc_emisor: str, adquiriente: str, direccion: Direccion, 
                    razon_social: str, fecha_emision: date = None, fecha_caducidad: date = None, 
                    fecha_autorizacion: date = None):
        factura = Factura(
            id_sucursal=id_sucursal,
            ruc_emisor=RUC(ruc_emisor),
            identificacion_adquiriente=adquiriente,
            razon_social_emisor=razon_social,
            direccion_matriz=direccion,
            fecha_emision=fecha_emision or date.today(),
            fecha_caducidad=fecha_caducidad,
            fecha_autorizacion=fecha_autorizacion or date.today()
        )
        totales = TotalesFactura(0)
        aggregate = cls(factura, totales)
        aggregate._verificar_invariantes()
        return aggregate
