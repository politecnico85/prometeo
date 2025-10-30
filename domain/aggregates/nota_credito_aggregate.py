from domain.entities.nota_credito import NotaCredito
from domain.entities.totales_nota_credito import TotalesNotaCredito
from domain.entities.linea_nota_credito import LineaNotaCredito
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.motivo_modificacion import MotivoModificacion
from domain.specifications.nota_credito_specifications import InventarioExisteParaNotaCredito
from domain.services.inventario_service import InventarioService
from domain.events.nota_credito_events import NotaCreditoEmitida, StockIncrementado
from domain.events.domain_event import DomainEvent
from decimal import Decimal
from datetime import date

class NotaCreditoAggregate:
    def __init__(self, nota_credito: NotaCredito, totales: TotalesNotaCredito):
        self.root = nota_credito
        self.totales = totales
        self._version = 0
        self._pending_events = []

    @classmethod
    def crear_nueva(cls, id_sucursal: int, ruc_emisor: str, id_factura_modificada: int, 
                    adquiriente: str, direccion: str, razon_social: str, motivo: str, 
                    fecha_emision: date, fecha_caducidad: date = None, fecha_autorizacion: date = None):
        nota_credito = NotaCredito(
            id_nota_credito=None,
            id_sucursal=id_sucursal,
            ruc_emisor=RUC(ruc_emisor),
            id_factura_modificada=id_factura_modificada,
            identificacion_adquiriente=adquiriente,
            razon_social_emisor=razon_social,
            direccion_matriz=Direccion(direccion, "Quito"),
            motivo_modificacion=MotivoModificacion(motivo),
            fecha_emision=fecha_emision,
            fecha_caducidad=fecha_caducidad,
            fecha_autorizacion=fecha_autorizacion
        )
        totales = TotalesNotaCredito(id_nota_credito=None)
        return cls(nota_credito, totales)

    def agregar_linea(self, linea: LineaNotaCredito):
        if linea.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        self.root.lineas.append(linea)
        self.totales.calcular_totales(self.root.lineas)

    def emitir(self, inventario_service: InventarioService, bodega_id: int, factura_agg) -> list:
        spec = InventarioExisteParaNotaCredito(inventario_service, factura_agg)
        if not spec.is_satisfied_by(self):
            raise ValueError("Inventario no disponible para la nota de crédito")

        self.root.id_nota_credito = self._generate_id()  # Simulate ID generation
        self._pending_events.append(NotaCreditoEmitida(self.root.id_nota_credito, {
            "id_nota_credito": self.root.id_nota_credito,
            "id_sucursal": self.root.id_sucursal,
            "id_factura_modificada": self.root.id_factura_modificada,
            "motivo": self.root.motivo_modificacion.motivo,
            "fecha_emision": self.root.fecha_emision.isoformat(),
            "total": float(self.totales.total_con_impuestos),
            "event_version": 1
        }))

        for linea in self.root.lineas:
            self._pending_events.append(StockIncrementado(
                aggregate_id=self.root.id_nota_credito,
                producto_id=linea.id_producto,
                bodega_id=bodega_id,
                cantidad=linea.cantidad,
                costo_unitario=float(linea.valor_item_cobrado),
                event_version=1
            ))
        self._version += len(self._pending_events)
        return self._pending_events

    def get_pending_events(self) -> list:
        return self._pending_events

    def clear_pending_events(self):
        self._pending_events = []

    def to_snapshot(self) -> dict:
        return {
            "nota_credito": {
                "id_nota_credito": self.root.id_nota_credito,
                "id_sucursal": self.root.id_sucursal,
                "ruc_emisor": str(self.root.ruc_emisor),
                "id_factura_modificada": self.root.id_factura_modificada,
                "identificacion_adquiriente": self.root.identificacion_adquiriente,
                "razon_social_emisor": self.root.razon_social_emisor,
                "direccion_matriz": {
                    "calle": self.root.direccion_matriz.calle,
                    "ciudad": self.root.direccion_matriz.ciudad
                },
                "motivo_modificacion": self.root.motivo_modificacion.motivo,
                "fecha_emision": self.root.fecha_emision.isoformat(),
                "fecha_caducidad": self.root.fecha_caducidad.isoformat() if self.root.fecha_caducidad else None,
                "fecha_autorizacion": self.root.fecha_autorizacion.isoformat() if self.root.fecha_autorizacion else None,
                "lineas": [
                    {
                        "id_producto": linea.id_producto,
                        "descripcion": linea.descripcion,
                        "cantidad": linea.cantidad,
                        "valor_item_cobrado": float(linea.valor_item_cobrado)
                    } for linea in self.root.lineas
                ]
            },
            "totales": {
                "subtotal": float(self.totales.subtotal),
                "total_con_impuestos": float(self.totales.total_con_impuestos)
            },
            "version": self._version
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict, events: list[DomainEvent]):
        nota_credito_data = snapshot["nota_credito"]
        nota_credito = NotaCredito(
            id_nota_credito=nota_credito_data["id_nota_credito"],
            id_sucursal=nota_credito_data["id_sucursal"],
            ruc_emisor=RUC(nota_credito_data["ruc_emisor"]),
            id_factura_modificada=nota_credito_data["id_factura_modificada"],
            identificacion_adquiriente=nota_credito_data["identificacion_adquiriente"],
            razon_social_emisor=nota_credito_data["razon_social_emisor"],
            direccion_matriz=Direccion(
                nota_credito_data["direccion_matriz"]["calle"],
                nota_credito_data["direccion_matriz"]["ciudad"]
            ),
            motivo_modificacion=MotivoModificacion(nota_credito_data["motivo_modificacion"]),
            fecha_emision=date.fromisoformat(nota_credito_data["fecha_emision"]),
            fecha_caducidad=date.fromisoformat(nota_credito_data["fecha_caducidad"]) if nota_credito_data["fecha_caducidad"] else None,
            fecha_autorizacion=date.fromisoformat(nota_credito_data["fecha_autorizacion"]) if nota_credito_data["fecha_autorizacion"] else None
        )
        for linea_data in nota_credito_data["lineas"]:
            nota_credito.lineas.append(LineaNotaCredito(
                id_producto=linea_data["id_producto"],
                descripcion=linea_data["descripcion"],
                cantidad=linea_data["cantidad"],
                valor_item_cobrado=Decimal(str(linea_data["valor_item_cobrado"]))
            ))
        totales = TotalesNotaCredito(
            id_nota_credito=nota_credito_data["id_nota_credito"],
            subtotal=Decimal(str(snapshot["totales"]["subtotal"])),
            total_con_impuestos=Decimal(str(snapshot["totales"]["total_con_impuestos"]))
        )
        aggregate = cls(nota_credito, totales)
        aggregate._version = snapshot["version"]
        for event in events:
            aggregate._apply_event(event)
        return aggregate

    def _apply_event(self, event: DomainEvent):
        self._version += 1

    def _generate_id(self) -> int:
        return 1  # Simulate ID generation (replace with actual logic, e.g., database sequence)