# domain/specifications/nota_credito_specifications.py
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List
from decimal import Decimal
from domain.entities.nota_credito import NotaCredito
from domain.entities.inventario import Inventario
from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.entities.linea_nota_credito import LineaNotaCredito

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool:
        pass

    def __and__(self, other: 'Specification') -> 'CompositeSpecification':
        return CompositeSpecification(self, other, lambda x, y: x and y)

class CompositeSpecification(Specification):
    def __init__(self, left: Specification, right: Specification, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def is_satisfied_by(self, candidate) -> bool:
        return self.operator(self.left.is_satisfied_by(candidate), self.right.is_satisfied_by(candidate))

class NotaCreditoTieneLineas(Specification):
    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        return len(nota_credito.lineas) > 0

class NotaCreditoTotalValido(Specification):
    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        return nota_credito.totales.valor_total > 0

class MotivoModificacionValido(Specification):
    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        return bool(nota_credito.motivo_modificacion.descripcion.strip())

class LineasValidasContraFactura(Specification):
    def __init__(self, factura_agg: Optional[FacturaAggregate]):
        self.factura_agg = factura_agg

    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        if not self.factura_agg:
            return False
        factura = self.factura_agg.root
        factura_cantidades = {linea.id_producto: linea.cantidad for linea in factura.lineas}
        for linea_nota in nota_credito.lineas:
            cantidad_max = factura_cantidades.get(linea_nota.id_producto, 0)
            if linea_nota.cantidad > cantidad_max:
                return False
        return True

class InventarioExisteParaNotaCredito(Specification):
    def __init__(self, inventarios: List[Inventario], bodega_id: int):
        self.inventarios = {inv.id_producto: inv for inv in inventarios}
        self.bodega_id = bodega_id

    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        for linea in nota_credito.lineas:
            inventario = self.inventarios.get(linea.id_producto)
            if not inventario or inventario.id_bodega != self.bodega_id:
                return False
        return True

class FechaEmisionValida(Specification):
    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        today = date.today()
        return nota_credito.fecha_emision >= today

class FechaCaducidadValida(Specification):
    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        if nota_credito.fecha_caducidad is None:
            return True
        return nota_credito.fecha_caducidad > nota_credito.fecha_emision

class FechaAutorizacionValida(Specification):
    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        today = date.today()
        return nota_credito.fecha_autorizacion <= nota_credito.fecha_emision and nota_credito.fecha_autorizacion <= today

class FechaEmisionPosteriorFactura(Specification):
    def __init__(self, factura_agg: Optional[FacturaAggregate]):
        self.factura_agg = factura_agg

    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        if not self.factura_agg:
            return False
        return nota_credito.fecha_emision > self.factura_agg.root.fecha_emision

class PlazoNotaCreditoValido(Specification):
    def __init__(self, factura_agg: Optional[FacturaAggregate], max_dias: int = 30):
        self.factura_agg = factura_agg
        self.max_dias = max_dias

    def is_satisfied_by(self, nota_credito: NotaCredito) -> bool:
        if not self.factura_agg:
            return False
        delta = (nota_credito.fecha_emision - self.factura_agg.root.fecha_emision).days
        return delta <= self.max_dias



