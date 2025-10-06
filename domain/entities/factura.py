# domain/entities/factura.py (extendido)
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from decimal import Decimal
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.forma_pago import FormaPago
from domain.entities.linea_factura import LineaFactura
from domain.entities.totales_factura import TotalesFactura

@dataclass
class Factura:
    id_factura: Optional[int] = None  # None para nuevas facturas
    id_sucursal: int
    id_bodega: Optional[int] = None
    ruc_emisor: RUC = field(default_factory=lambda: RUC("0000000000000"))  # Placeholder
    identificacion_adquiriente: str
    razon_social_emisor: str
    direccion_matriz: Direccion
    fecha_emision: date = field(default_factory=date.today)
    forma_pago: FormaPago = field(default_factory=lambda: FormaPago("Efectivo", Decimal('0.00')))
    lineas: List[LineaFactura] = field(default_factory=list)
    totales: Optional[TotalesFactura] = None  # Se crea en aggregate

    def agregar_linea(self, linea: LineaFactura):
        self.lineas.append(linea)
        self._actualizar_totales()

    def _actualizar_totales(self):
        if not self.totales:
            self.totales = TotalesFactura(self.id_factura or 0)  # Temporal ID
        self.totales.actualizar_desde_lineas(self.lineas)

    def validar_emision(self):
        if not self.lineas:
            raise ValueError("Factura debe tener al menos una línea.")
        if self.totales.valor_total <= 0:
            raise ValueError("Total de factura inválido.")
        # Aquí: Chequear stock en bodega vía service (no en entity)