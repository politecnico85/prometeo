# domain/entities/factura.py
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from decimal import Decimal
from domain.value_objects.direccion import Direccion
from domain.entities.linea_factura import LineaFactura  # Definida más abajo

@dataclass
class Factura:
    id_factura: int
    fecha_emision: date
    ruc_emisor: str
    identificacion_adquiriente: str
    direccion_matriz: Direccion
    lineas: List[LineaFactura] = field(default_factory=list)
    subtotal: Decimal = Decimal('0.00')
    iva: Decimal = Decimal('0.00')
    total: Decimal = Decimal('0.00')
    # Otras campos del esquema...

    def agregar_linea(self, linea: LineaFactura):
        self.lineas.append(linea)
        self._calcular_totales()

    def _calcular_totales(self):
        self.subtotal = sum(linea.valor_total for linea in self.lineas)
        self.iva = self.subtotal * Decimal('0.12')  # IVA 12% asumido
        self.total = self.subtotal + self.iva