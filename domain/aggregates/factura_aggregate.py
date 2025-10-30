# domain/aggregates/factura_aggregate.py
from domain.entities.factura import Factura
from domain.entities.totales_factura import TotalesFactura
from domain.entities.linea_factura import LineaFactura
from domain.value_objects.direccion import Direccion
from domain.value_objects.ruc import RUC
from domain.value_objects.forma_pago import FormaPago
from domain.value_objects.precio import Precio
from domain.specifications.factura_specifications import StockSuficienteParaFactura
from domain.specifications.inventario_specifications import InventarioDisponibleParaFactura
from domain.services.inventario_service import InventarioService
from domain.events.factura_events import FacturaEmitida, StockReducido
from domain.events.domain_event import DomainEvent
from decimal import Decimal
from datetime import date

class FacturaAggregate:
    def __init__(self, factura: Factura, totales: TotalesFactura):
        self.root = factura
        self.totales = totales
        self._version = 0
        self._pending_events = []

    @classmethod
    def crear_nueva(cls, id_sucursal: int, id_bodega: int, ruc_emisor: str, adquiriente: str, 
                    direccion: str, razon_social: str, forma_pago: str, fecha_emision: date, 
                    fecha_caducidad: date = None, fecha_autorizacion: date = None):
        factura = Factura(
            id_factura=None,
            id_sucursal=id_sucursal,
            id_bodega=id_bodega,
            ruc_emisor=RUC(ruc_emisor),
            identificacion_adquiriente=adquiriente,
            razon_social_emisor=razon_social,
            direccion_matriz=Direccion(direccion, "Quito"),
            fecha_emision=fecha_emision,
            fecha_caducidad=fecha_caducidad,
            fecha_autorizacion=fecha_autorizacion,
            forma_pago=FormaPago(forma_pago, Decimal('0.00'))
        )
        totales = TotalesFactura(id_factura=None)
        return cls(factura, totales)

    def agregar_linea(self, linea: LineaFactura):
        if linea.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        self.root.lineas.append(linea)
        self.totales.calcular_totales(self.root.lineas)

    def emitir(self, inventario_service: InventarioService) -> list:
        spec = StockSuficienteParaFactura(inventario_service)
        spec_inventario = InventarioDisponibleParaFactura(inventario_service)
        if not spec.is_satisfied_by(self):
            raise ValueError("Stock insuficiente para emitir la factura")
        if not spec_inventario.is_satisfied_by(self):
            raise ValueError("Inventario no disponible para la factura")

        self.root.id_factura = self._generate_id()  # Simulate ID generation
        self._pending_events.append(FacturaEmitida(self.root.id_factura, {
            "id_factura": self.root.id_factura,
            "id_sucursal": self.root.id_sucursal,
            "id_bodega": self.root.id_bodega,
            "ruc_emisor": str(self.root.ruc_emisor),
            "identificacion_adquiriente": self.root.identificacion_adquiriente,
            "razon_social_emisor": self.root.razon_social_emisor,
            "fecha_emision": self.root.fecha_emision.isoformat(),
            "total": float(self.totales.total_con_impuestos),
            "event_version": 1
        }))

        for linea in self.root.lineas:
            self._pending_events.append(StockReducido(
                aggregate_id=self.root.id_factura,
                producto_id=linea.id_producto,
                bodega_id=self.root.id_bodega,
                cantidad=linea.cantidad,
                costo_unitario=float(linea.precio_unitario.valor),
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
            "factura": {
                "id_factura": self.root.id_factura,
                "id_sucursal": self.root.id_sucursal,
                "id_bodega": self.root.id_bodega,
                "ruc_emisor": str(self.root.ruc_emisor),
                "identificacion_adquiriente": self.root.identificacion_adquiriente,
                "razon_social_emisor": self.root.razon_social_emisor,
                "direccion_matriz": {
                    "calle": self.root.direccion_matriz.calle,
                    "ciudad": self.root.direccion_matriz.ciudad
                },
                "fecha_emision": self.root.fecha_emision.isoformat(),
                "fecha_caducidad": self.root.fecha_caducidad.isoformat() if self.root.fecha_caducidad else None,
                "fecha_autorizacion": self.root.fecha_autorizacion.isoformat() if self.root.fecha_autorizacion else None,
                "forma_pago": {
                    "metodo": self.root.forma_pago.metodo,
                    "monto": float(self.root.forma_pago.monto)
                },
                "lineas": [
                    {
                        "id_producto": linea.id_producto,
                        "descripcion": linea.descripcion,
                        "cantidad": linea.cantidad,
                        "precio_unitario": float(linea.precio_unitario.valor)
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
        factura_data = snapshot["factura"]
        factura = Factura(
            id_factura=factura_data["id_factura"],
            id_sucursal=factura_data["id_sucursal"],
            id_bodega=factura_data["id_bodega"],
            ruc_emisor=RUC(factura_data["ruc_emisor"]),
            identificacion_adquiriente=factura_data["identificacion_adquiriente"],
            razon_social_emisor=factura_data["razon_social_emisor"],
            direccion_matriz=Direccion(
                factura_data["direccion_matriz"]["calle"],
                factura_data["direccion_matriz"]["ciudad"]
            ),
            fecha_emision=date.fromisoformat(factura_data["fecha_emision"]),
            fecha_caducidad=date.fromisoformat(factura_data["fecha_caducidad"]) if factura_data["fecha_caducidad"] else None,
            fecha_autorizacion=date.fromisoformat(factura_data["fecha_autorizacion"]) if factura_data["fecha_autorizacion"] else None,
            forma_pago=FormaPago(
                factura_data["forma_pago"]["metodo"],
                Decimal(str(factura_data["forma_pago"]["monto"]))
            )
        )
        for linea_data in factura_data["lineas"]:
            factura.lineas.append(LineaFactura(
                id_producto=linea_data["id_producto"],
                descripcion=linea_data["descripcion"],
                cantidad=linea_data["cantidad"],
                precio_unitario=Precio(Decimal(str(linea_data["precio_unitario"])))
            ))
        totales = TotalesFactura(
            id_factura=factura_data["id_factura"],
            subtotal=Decimal(str(snapshot["totales"]["subtotal"])),
            total_con_impuestos=Decimal(str(snapshot["totales"]["total_con_impuestos"]))
        )
        aggregate = cls(factura, totales)
        aggregate._version = snapshot["version"]
        for event in events:
            aggregate._apply_event(event)
        return aggregate

    def _apply_event(self, event: DomainEvent):
        self._version += 1

    def _generate_id(self) -> int:
        return 1  # Simulate ID generation (replace with actual logic, e.g., database sequence)

