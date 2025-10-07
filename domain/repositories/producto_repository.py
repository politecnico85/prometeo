from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from domain.repositories.producto_repository import ProductoRepository
from domain.entities.producto import Producto
from domain.value_objects.precio import Precio
from decimal import Decimal

Base = declarative_base()

class ProductoDB(Base):
    __tablename__ = 'productos'
    id_producto = Column(Integer, primary_key=True)
    nombre = Column(String)
    descripcion = Column(String)
    precio_base = Column(Float)
    # Other fields as per schema

class ProductoRepositorySQL(ProductoRepository):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def obtener_por_id(self, id: int) -> Producto:
        session = self.Session()
        try:
            db_producto = session.query(ProductoDB).filter_by(id_producto=id).first()
            if not db_producto:
                return None
            return Producto(
                id_producto=db_producto.id_producto,
                nombre=db_producto.nombre,
                descripcion=db_producto.descripcion,
                precio_base=Precio(Decimal(str(db_producto.precio_base)))
                # Map other fields
            )
        finally:
            session.close()

    def guardar(self, producto: Producto):
        session = self.Session()
        try:
            db_producto = ProductoDB(
                id_producto=producto.id_producto,
                nombre=producto.nombre,
                descripcion=producto.descripcion,
                precio_base=float(producto.precio_base.valor)
                # Map other fields
            )
            session.merge(db_producto)
            session.commit()
        finally:
            session.close()