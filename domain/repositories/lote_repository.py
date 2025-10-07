from sqlalchemy import create_engine, Column, Integer, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from domain.repositories.lote_repository import LoteRepository
from domain.entities.lote import Lote
from datetime import date
from decimal import Decimal

Base = declarative_base()

class LoteDB(Base):
    __tablename__ = 'lotes'
    id_lote = Column(Integer, primary_key=True)
    id_producto = Column(Integer, ForeignKey('productos.id_producto'))
    id_bodega = Column(Integer, ForeignKey('bodegas.id_bodega'))
    id_orden_compra = Column(Integer)
    fecha_compra = Column(Date)
    cantidad_inicial = Column(Integer)
    cantidad_restante = Column(Integer)
    costo_unitario = Column(Float)

class LoteRepositorySQL(LoteRepository):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def obtener_lotes_antiguos(self, id_producto: int, id_bodega: int) -> list[Lote]:
        session = self.Session()
        try:
            db_lotes = session.query(LoteDB).filter_by(id_producto=id_producto, id_bodega=id_bodega).order_by(LoteDB.fecha_compra).all()
            return [Lote(
                id_lote=l.id_lote,
                id_producto=l.id_producto,
                id_bodega=l.id_bodega,
                id_orden_compra=l.id_orden_compra,
                fecha_compra=l.fecha_compra,
                cantidad_inicial=l.cantidad_inicial,
                cantidad_restante=l.cantidad_restante,
                costo_unitario=Decimal(str(l.costo_unitario))
            ) for l in db_lotes]
        finally:
            session.close()

    def actualizar(self, lote: Lote):
        session = self.Session()
        try:
            db_lote = session.query(LoteDB).filter_by(id_lote=lote.id_lote).first()
            if db_lote:
                db_lote.cantidad_restante = lote.cantidad_restante
                session.commit()
        finally:
            session.close()

    def guardar(self, lote: Lote):
        session = self.Session()
        try:
            db_lote = LoteDB(
                id_producto=lote.id_producto,
                id_bodega=lote.id_bodega,
                id_orden_compra=lote.id_orden_compra,
                fecha_compra=lote.fecha_compra,
                cantidad_inicial=lote.cantidad_inicial,
                cantidad_restante=lote.cantidad_restante,
                costo_unitario=float(lote.costo_unitario)
            )
            session.add(db_lote)
            session.commit()
            lote.id_lote = db_lote.id_lote
        finally:
            session.close()