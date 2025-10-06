# domain/specifications/factura_specifications.py
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from decimal import Decimal
from domain.entities.factura import Factura
from domain.entities.linea_factura import LineaFactura
from domain.value_objects.forma_pago import FormaPago

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

class FacturaTieneLineas(Specification):
    def is_satisfied_by(self, factura: Factura) -> bool:
        return len(factura.lineas) > 0

class FacturaTotalValido(Specification):
    def is_satisfied_by(self, factura: Factura) -> bool:
        return factura.totales.valor_total > 0

class FormaPagoValida(Specification):
    def is_satisfied_by(self, factura: Factura) -> bool:
        return factura.forma_pago.valor >= factura.totales.valor_total

class FechaEmisionValida(Specification):
    def is_satisfied_by(self, factura: Factura) -> bool:
        today = date.today()
        return factura.fecha_emision >= today

class FechaCaducidadValida(Specification):
    def is_satisfied_by(self, factura: Factura) -> bool:
        if factura.fecha_caducidad is None:
            return True  # Opcional
        return factura.fecha_caducidad > factura.fecha_emision

class FechaAutorizacionValida(Specification):
    def is_satisfied_by(self, factura: Factura) -> bool:
        today = date.today()
        return factura.fecha_autorizacion <= factura.fecha_emision and factura.fecha_autorizacion <= today

