# domain/services/inventario_service.py
from domain.repositories.inventario_repository import InventarioRepository
from domain.repositories.lote_repository import LoteRepository
from domain.repositories.movimiento_inventario_repository import MovimientoInventarioRepository
from domain.entities.inventario import Inventario
from domain.entities.lote import Lote
from domain.entities.movimiento_inventario import MovimientoInventario
from datetime import datetime, date
from decimal import Decimal

class InventarioService:
    def __init__(self, inventario_repo: InventarioRepository, lote_repo: LoteRepository, 
                 movimiento_repo: MovimientoInventarioRepository):
        self.inventario_repo = inventario_repo
        self.lote_repo = lote_repo
        self.movimiento_repo = movimiento_repo

    def registrar_entrada(self, id_producto: int, id_bodega: int, id_orden_compra: int, 
                          cantidad: int, costo_unitario: float, fecha_compra: date) -> None:
        # Create new Lote
        lote = Lote(
            id_lote=None,
            id_producto=id_producto,
            id_bodega=id_bodega,
            id_orden_compra=id_orden_compra,
            fecha_compra=fecha_compra,
            cantidad_inicial=cantidad,
            cantidad_restante=cantidad,
            costo_unitario=Decimal(str(costo_unitario))
        )
        self.lote_repo.guardar(lote)

        # Update Inventario
        inventario = self.inventario_repo.obtener_por_bodega(id_bodega)
        inventario = next((i for i in inventario if i.id_producto == id_producto), None)
        if inventario:
            inventario.cantidad_stock += cantidad
            inventario.fecha_actualizacion = date.today()
            self.inventario_repo.actualizar(inventario)
        else:
            inventario = Inventario(
                id_inventario=None,
                id_producto=id_producto,
                id_bodega=id_bodega,
                cantidad_stock=cantidad,
                cantidad_minima=0,
                fecha_actualizacion=date.today()
            )
            self.inventario_repo.guardar(inventario)

        # Record MovimientoInventario
        movimiento = MovimientoInventario(
            id_movimiento=None,
            id_producto=id_producto,
            id_bodega=id_bodega,
            id_factura=None,
            id_orden_compra=id_orden_compra,
            id_lote=lote.id_lote,
            tipo_movimiento="ENTRADA",
            costo_unitario_aplicado=costo_unitario,
            cantidad=cantidad,
            fecha_movimiento=datetime.now(),
            stock_post_movimiento=inventario.cantidad_stock
        )
        self.movimiento_repo.guardar(movimiento)

    def registrar_salida_fifo(self, id_producto: int, id_bodega: int, id_factura: int, 
                             cantidad: int) -> list[dict]:
        lotes = self.lote_repo.obtener_lotes_antiguos(id_producto, id_bodega)
        cantidad_restante = cantidad
        movimientos = []
        inventario = next((i for i in self.inventario_repo.obtener_por_bodega(id_bodega) 
                           if i.id_producto == id_producto), None)
        if not inventario or inventario.cantidad_stock < cantidad:
            raise ValueError("Stock insuficiente")

        for lote in lotes:
            if cantidad_restante <= 0:
                break
            if lote.cantidad_restante > 0:
                cantidad_a_usar = min(cantidad_restante, lote.cantidad_restante)
                lote.cantidad_restante -= cantidad_a_usar
                self.lote_repo.actualizar(lote)
                inventario.cantidad_stock -= cantidad_a_usar
                movimiento = MovimientoInventario(
                    id_movimiento=None,
                    id_producto=id_producto,
                    id_bodega=id_bodega,
                    id_factura=id_factura,
                    id_orden_compra=None,
                    id_lote=lote.id_lote,
                    tipo_movimiento="SALIDA",
                    costo_unitario_aplicado=float(lote.costo_unitario),
                    cantidad=cantidad_a_usar,
                    fecha_movimiento=datetime.now(),
                    stock_post_movimiento=inventario.cantidad_stock
                )
                self.movimiento_repo.guardar(movimiento)
                movimientos.append({
                    "id_lote": lote.id_lote,
                    "cantidad": cantidad_a_usar,
                    "costo_unitario": float(lote.costo_unitario)
                })
                cantidad_restante -= cantidad_a_usar

        if cantidad_restante > 0:
            raise ValueError("No hay suficientes lotes para cubrir la salida")
        
        inventario.fecha_actualizacion = date.today()
        self.inventario_repo.actualizar(inventario)
        return movimientos

    def registrar_entrada_por_nota_credito(self, id_producto: int, id_bodega: int, 
                                          cantidad: int, costo_unitario: float) -> None:
        # Create new Lote for return
        lote = Lote(
            id_lote=None,
            id_producto=id_producto,
            id_bodega=id_bodega,
            id_orden_compra=None,
            fecha_compra=date.today(),
            cantidad_inicial=cantidad,
            cantidad_restante=cantidad,
            costo_unitario=Decimal(str(costo_unitario))
        )
        self.lote_repo.guardar(lote)

        # Update Inventario
        inventario = next((i for i in self.inventario_repo.obtener_por_bodega(id_bodega) 
                           if i.id_producto == id_producto), None)
        if inventario:
            inventario.cantidad_stock += cantidad
            inventario.fecha_actualizacion = date.today()
            self.inventario_repo.actualizar(inventario)
        else:
            inventario = Inventario(
                id_inventario=None,
                id_producto=id_producto,
                id_bodega=id_bodega,
                cantidad_stock=cantidad,
                cantidad_minima=0,
                fecha_actualizacion=date.today()
            )
            self.inventario_repo.guardar(inventario)

        # Record MovimientoInventario
        movimiento = MovimientoInventario(
            id_movimiento=None,
            id_producto=id_producto,
            id_bodega=id_bodega,
            id_factura=None,
            id_orden_compra=None,
            id_lote=lote.id_lote,
            tipo_movimiento="ENTRADA",
            costo_unitario_aplicado=costo_unitario,
            cantidad=cantidad,
            fecha_movimiento=datetime.now(),
            stock_post_movimiento=inventario.cantidad_stock
        )
        self.movimiento_repo.guardar(movimiento)

    def obtener_valor_inventario_fifo(self, id_producto: int, id_bodega: int) -> Decimal:
        lotes = self.lote_repo.obtener_lotes_antiguos(id_producto, id_bodega)
        return sum(Decimal(str(lote.cantidad_restante)) * lote.costo_unitario 
                   for lote in lotes if lote.cantidad_restante > 0)

