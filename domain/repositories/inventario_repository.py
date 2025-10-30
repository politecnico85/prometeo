from sqlalchemy import create_engine, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from domain.repositories.inventario_repository import InventarioRepository
from domain.entities.inventario import Inventario
from datetime import date

Base = declarative_base()

class InventarioDB(Base):
    __tablename__ = 'inventario'
    id_inventario = Column(Integer, primary_key=True)
    id_producto = Column(Integer, ForeignKey('productos.id_producto'))
    id_bodega = Column(Integer, ForeignKey('bodegas.id_bodega'))
    cantidad_stock = Column(Integer)
    cantidad_minima = Column(Integer)
    fecha_actualizacion = Column(Date)

class InventarioRepositorySQL(InventarioRepository):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def obtener_por_bodega(self, id_bodega: int) -> list[Inventario]:
        session = self.Session()
        try:
            db_inventarios = session.query(InventarioDB).filter_by(id_bodega=id_bodega).all()
            return [Inventario(
                id_inventario=i.id_inventario,
                id_producto=i.id_producto,
                id_bodega=i.id_bodega,
                cantidad_stock=i.cantidad_stock,
                cantidad_minima=i.cantidad_minima,
                fecha_actualizacion=i.fecha_actualizacion
            ) for i in db_inventarios]
        finally:
            session.close()

    def actualizar(self, inventario: Inventario):
        session = self.Session()
        try:
            db_inventario = session.query(InventarioDB).filter_by(id_inventario=inventario.id_inventario).first()
            if db_inventario:
                db_inventario.cantidad_stock = inventario.cantidad_stock
                db_inventario.cantidad_minima = inventario.cantidad_minima
                db_inventario.fecha_actualizacion = inventario.fecha_actualizacion
                session.commit()
        finally:
            session.close()