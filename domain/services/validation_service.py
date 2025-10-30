from domain.aggregates.factura_aggregate import FacturaAggregate
from domain.aggregates.nota_credito_aggregate import NotaCreditoAggregate
from domain.specifications.factura_specifications import StockSuficienteParaFactura
from domain.specifications.inventario_specifications import InventarioDisponibleParaFactura
from domain.specifications.nota_credito_specifications import (
    InventarioExisteParaNotaCredito, LineasValidasContraFactura, FechaEmisionPosteriorFactura, PlazoNotaCreditoValido
)
from domain.services.inventario_service import InventarioService

class ValidationService:
    def __init__(self, inventario_service: InventarioService):
        self.inventario_service = inventario_service

    def validate_factura(self, factura_agg: FacturaAggregate) -> list[str]:
        errors = []
        specs = [
            StockSuficienteParaFactura(self.inventario_service),
            InventarioDisponibleParaFactura(self.inventario_service)
        ]
        for spec in specs:
            if not spec.is_satisfied_by(factura_agg):
                errors.append(f"Validación fallida: {spec.__class__.__name__}")
        return errors

    def validate_nota_credito(self, nota_credito_agg: NotaCreditoAggregate, factura_agg: FacturaAggregate) -> list[str]:
        errors = []
        specs = [
            InventarioExisteParaNotaCredito(self.inventario_service, factura_agg),
            LineasValidasContraFactura(factura_agg),
            FechaEmisionPosteriorFactura(factura_agg),
            PlazoNotaCreditoValido(factura_agg, max_dias=30)
        ]
        for spec in specs:
            if not spec.is_satisfied_by(nota_credito_agg):
                errors.append(f"Validación fallida: {spec.__class__.__name__}")
        return errors