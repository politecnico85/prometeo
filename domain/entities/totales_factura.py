# domain/entities/totales_factura.py
from dataclasses import dataclass
from decimal import Decimal
from .linea_factura import LineaFactura

@dataclass
class TotalesFactura:
    id_factura: int  # Referencia a root
    base_imponible_12: Decimal = Decimal('0.00')
    base_imponible_0: Decimal = Decimal('0.00')
    descuento_comercial: Decimal = Decimal('0.00')
    valor_subtotal: Decimal = Decimal('0.00')
    valor_iva: Decimal = Decimal('0.00')
    valor_ice: Decimal = Decimal('0.00')
    valor_total: Decimal = Decimal('0.00')

    def actualizar_desde_lineas(self, lineas: list['LineaFactura'], iva_porcentaje: Decimal = Decimal('12')):
        self.valor_subtotal = sum(linea.valor_total for linea in lineas)
        self.descuento_comercial = sum(linea.valor_total * (Decimal('0.00')) for linea in lineas)  # Lógica de descuentos globales
        base_iva = self.valor_subtotal - self.descuento_comercial  # Asumir todo grava 12%
        self.valor_iva = base_iva * (iva_porcentaje / 100)
        self.valor_total = self.valor_subtotal - self.descuento_comercial + self.valor_iva + self.valor_ice