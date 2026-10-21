from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship

# Esta es la base de SQLAlchemy que convertirá nuestras clases de Python en tablas de base de datos.
Base = declarative_base()

class Categoria(Base):
    __tablename__ = "categorias"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    
    # AGREGAMOS ESTA LÍNEA QUE FALTABA
    descripcion = Column(String, nullable=True) 
    
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    
    # Puede ser nulo (nullable=True) porque el tomate o la carne a granel no traen código de barras
    codigo_barras = Column(String, unique=True, index=True, nullable=True) 
    
    nombre = Column(String, nullable=False)
    
    # Para saber si lo pesas o lo cuentas: 'unidad', 'kg', 'gr'
    tipo_unidad = Column(String, default="unidad", nullable=False) 
    
    # Regla de oro: NUNCA borramos productos, solo los desactivamos. 
    # Si borras un producto, rompes el historial de facturas viejas.
    activo = Column(Boolean, default=True)
    
    # Esto conecta cada producto con su categoría
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    categoria = relationship("Categoria", back_populates="productos")

class TasaCambio(Base):
    __tablename__ = "tasas_cambio"
    
    id = Column(Integer, primary_key=True, index=True)
    moneda = Column(String, default="USD", nullable=False)
    tasa = Column(Float, nullable=False) # El valor del día
    # Registra automáticamente la fecha y hora del sistema
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    activa = Column(Boolean, default=True)

class LoteInventario(Base):
    __tablename__ = "lotes_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    
    # Usamos Float porque podrías ingresar 3.5 Kg de carne
    cantidad_inicial = Column(Float, nullable=False) 
    cantidad_actual = Column(Float, nullable=False) 
    
    # El costo al que le compraste al proveedor (idealmente en una moneda estable para calcular márgenes)
    costo_unitario = Column(Float, nullable=False) 
    
    fecha_ingreso = Column(DateTime(timezone=True), server_default=func.now())
    # Opcional, pero vital para aplicar el método FIFO y que sepas qué vender primero
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=True) 
    
    # Relación bidireccional con el producto
    producto = relationship("Producto", backref="lotes")   

class Venta(Base):
    __tablename__ = "ventas"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    total_usd = Column(Float, nullable=False, default=0.0)
    total_local = Column(Float, nullable=False, default=0.0)
    tasa_usada = Column(Float, nullable=False) # Guardamos a cómo estaba el dólar ESE día, por temas de auditoría
    
    # Relación: Una venta tiene muchos productos dentro
    detalles = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = "detalles_venta"
    
    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    
    cantidad = Column(Float, nullable=False) # Float por si vendes 0.5 kg de queso
    precio_unitario_usd = Column(Float, nullable=False)
    precio_unitario_local = Column(Float, nullable=False)
    
    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto")     