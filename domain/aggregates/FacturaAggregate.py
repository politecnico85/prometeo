# domain/aggregates/factura_aggregate.py
from domain.entities.factura import Factura
from domain.entities.totales_factura import TotalesFactura  # Entity para totales

class FacturaAggregate:
    def __init__(self, factura: Factura, totales: TotalesFactura):
        self.root = factura
        self.totales = totales

    def aplicar_descuento_global(self, porcentaje: Decimal):
        for linea in self.root.lineas:
            linea.precio_unitario *= (1 - porcentaje / 100)
            linea.valor_total = linea.cantidad * linea.precio_unitario
        self.root._calcular_totales()
        self.totales.valor_subtotal = self.root.subtotal
        # Actualizar otros campos...