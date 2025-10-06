# domain/entities/nota_credito.py
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional
from domain.value_objects.ruc import RUC
from domain.value_objects.direccion import Direccion
from domain.value_objects.motivo_modificacion import MotivoModificacion
from domain.entities.linea_nota_credito import LineaNotaCredito
from domain.entities.totales_nota_credito import TotalesNotaCredito

@dataclass
class NotaCredito:
    id_nota_credito: Optional[int] = None  # None para nuevas
    id_sucursal: int
    ruc_emisor: RUC = field(default_factory=lambda: RUC("0000000000000"))  # Placeholder
    fecha_emision: date = field(default_factory=date.today)
    fecha_caducidad: Optional[date] = field(default_factory=lambda: date.today() + timedelta(days=30))
    fecha_autorizacion: date = field(default_factory=date.today)
    id_factura_modificada: int
    identificacion_adquiriente: str
    razon_social_emisor: str
    direccion_matriz: Direccion
    motivo_modificacion: MotivoModificacion = field(default_factory=lambda: MotivoModificacion(""))
    lineas: List[LineaNotaCredito] = field(default_factory=list)
    totales: Optional[TotalesNotaCredito] = None  # Se crea en aggregate

    def agregar_linea(self, linea: LineaNotaCredito):
        self.lineas.append(linea)
        self._actualizar_totales()

    def _actualizar_totales(self):
        if not self.totales:
            self.totales = TotalesNotaCredito(self.id_nota_credito or 0)  # Temporal ID
        self.totales.actualizar_desde_lineas(self.lineas)

    def validar_emision(self):
        if not self.lineas:
            raise ValueError("Nota de crédito debe tener al menos una línea.")
        if self.totales.valor_total <= 0:
            raise ValueError("Total de nota de crédito inválido.")
        if not self.motivo_modificacion.descripcion:
            raise ValueError("Motivo requerido.")
        # Aquí: Validar contra factura original vía service (e.g., cantidades <= originales)