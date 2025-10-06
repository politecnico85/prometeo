# infrastructure/persistence/sql_repository.py
from sqlalchemy import create_engine, Column, Integer, String, Decimal, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from domain.aggregates.producto_aggregate import ProductoAggregate
from domain.entities.producto import Producto
# ... Mapea otras entities con SQLAlchemy

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://user:pass@localhost/db_name')
Session = sessionmaker(bind=engine)

# Ejemplo de mapping para Producto
class ProductoDB(Base):
    __tablename__ = 'Productos'
    id_producto = Column(Integer, primary_key=True)
    nombre_producto = Column(String(100))
    # ... otros campos

class ProductoRepositorySQL(ProductoRepository):
    def obtener_por_id(self, id: int) -> ProductoAggregate:
        session = Session()
        db_producto = session.query(ProductoDB).filter_by(id_producto=id).first()
        if not db_producto:
            return None
        # Mapear a domain model (usar un mapper)
        producto = Producto(id_producto=db_producto.id_producto, nombre=db_producto.nombre_producto, ...)
        # Cargar inventarios...
        return ProductoAggregate(producto, [])

    def guardar(self, aggregate: ProductoAggregate):
        session = Session()
        # Mapear de vuelta y commit
        session.commit()