# application/main.py
from domain.services.inventario_service import InventarioService
from infrastructure.persistence.sql_repository import ProductoRepositorySQL, LoteRepositorySQL

producto_repo = ProductoRepositorySQL()
lote_repo = LoteRepositorySQL()
service = InventarioService(lote_repo)

# Registrar salida FIFO
try:
    movimientos = service.registrar_salida_fifo(producto_id=1, bodega_id=1, cantidad=10, factura_id=100)
    print("Movimientos registrados:", movimientos)
except ValueError as e:
    print(e)