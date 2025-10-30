# infrastructure/persistence/projection_sql.py
from sqlalchemy import Column, Integer, String, Float, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date

Base = declarative_base()

class StockProjection(Base):
    __tablename__ = 'stock_projections'
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, index=True)
    bodega_id = Column(Integer, index=True)
    cantidad = Column(Float)

class FacturaProjection(Base):
    __tablename__ = 'factura_projections'
    id = Column(Integer, primary_key=True)
    id_factura = Column(Integer, unique=True)
    id_sucursal = Column(Integer)
    id_bodega = Column(Integer)
    ruc_emisor = Column(String)
    identificacion_adquiriente = Column(String)
    razon_social_emisor = Column(String)
    fecha_emision = Column(Date)
    total = Column(Float)

class NotaCreditoProjection(Base):
    __tablename__ = 'nota_credito_projections'
    id = Column(Integer, primary_key=True)
    id_nota_credito = Column(Integer, unique=True)
    id_sucursal = Column(Integer)
    id_factura_modificada = Column(Integer)
    motivo = Column(String)
    fecha_emision = Column(Date)
    total = Column(Float)

class ProjectionRepository:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def update_stock(self, producto_id: int, bodega_id: int, cantidad: float):
        session = self.Session()
        try:
            projection = session.query(StockProjection).filter_by(
                producto_id=producto_id, bodega_id=bodega_id
            ).first()
            if projection:
                projection.cantidad = cantidad
            else:
                projection = StockProjection(
                    producto_id=producto_id,
                    bodega_id=bodega_id,
                    cantidad=cantidad
                )
                session.add(projection)
            session.commit()
        finally:
            session.close()

    def get_stock(self, producto_id: int, bodega_id: int) -> float:
        session = self.Session()
        try:
            projection = session.query(StockProjection).filter_by(
                producto_id=producto_id, bodega_id=bodega_id
            ).first()
            return projection.cantidad if projection else 0.0
        finally:
            session.close()

    def save_factura(self, factura_data: dict):
        session = self.Session()
        try:
            projection = FacturaProjection(
                id_factura=factura_data['id_factura'],
                id_sucursal=factura_data['id_sucursal'],
                id_bodega=factura_data['id_bodega'],
                ruc_emisor=factura_data['ruc_emisor'],
                identificacion_adquiriente=factura_data['identificacion_adquiriente'],
                razon_social_emisor=factura_data['razon_social_emisor'],
                fecha_emision=date.fromisoformat(factura_data['fecha_emision']),
                total=factura_data.get('total', 0.0)
            )
            session.merge(projection)
            session.commit()
        finally:
            session.close()

    def save_nota_credito(self, nota_credito_data: dict):
        session = self.Session()
        try:
            projection = NotaCreditoProjection(
                id_nota_credito=nota_credito_data['id_nota_credito'],
                id_sucursal=nota_credito_data['id_sucursal'],
                id_factura_modificada=nota_credito_data['id_factura_modificada'],
                motivo=nota_credito_data.get('motivo', ''),
                fecha_emision=date.fromisoformat(nota_credito_data['fecha_emision']),
                total=nota_credito_data.get('total', 0.0)
            )
            session.merge(projection)
            session.commit()
        finally:
            session.close()

    def get_factura(self, id_factura: int) -> dict:
        session = self.Session()
        try:
            projection = session.query(FacturaProjection).filter_by(id_factura=id_factura).first()
            if not projection:
                return None
            return {
                'id_factura': projection.id_factura,
                'id_sucursal': projection.id_sucursal,
                'id_bodega': projection.id_bodega,
                'ruc_emisor': projection.ruc_emisor,
                'identificacion_adquiriente': projection.identificacion_adquiriente,
                'razon_social_emisor': projection.razon_social_emisor,
                'fecha_emision': projection.fecha_emision.isoformat(),
                'total': projection.total
            }
        finally:
            session.close()

    def get_nota_credito(self, id_nota_credito: int) -> dict:
        session = self.Session()
        try:
            projection = session.query(NotaCreditoProjection).filter_by(id_nota_credito=id_nota_credito).first()
            if not projection:
                return None
            return {
                'id_nota_credito': projection.id_nota_credito,
                'id_sucursal': projection.id_sucursal,
                'id_factura_modificada': projection.id_factura_modificada,
                'motivo': projection.motivo,
                'fecha_emision': projection.fecha_emision.isoformat(),
                'total': projection.total
            }
        finally:
            session.close()

