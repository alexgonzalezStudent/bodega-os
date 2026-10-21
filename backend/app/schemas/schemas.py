from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# 1. Esquema Base: Lo que comparten todas las acciones de Categoría
class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None # Optional significa que puede estar vacío

# 2. Esquema para CREAR: Lo que el sistema espera recibir cuando tú escribes una nueva categoría
class CategoriaCreate(CategoriaBase):
    pass # No añadimos nada extra por ahora, hereda de CategoriaBase

# 3. Esquema para LEER: Lo que el sistema te devuelve (incluye el ID que genera la base de datos)
class Categoria(CategoriaBase):
    id: int

    class Config:
        # Esto es vital: le dice a Pydantic que sepa leer los datos desde SQLAlchemy (tu base de datos)
        from_attributes = True

# --- ESQUEMAS PARA PRODUCTOS ---

class ProductoBase(BaseModel):
    nombre: str
    # Opcional porque cosas como el Jojoto o el Ocumo que pesas no traen código de barras
    codigo_barras: Optional[str] = None 
    tipo_unidad: str = "unidad" # Puede ser "kg", "gr", "litro"
    activo: bool = True
    # Esta es la llave que conecta al producto con su categoría
    categoria_id: int 

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int

    class Config:
        from_attributes = True        

# --- ESQUEMAS PARA TASA DE CAMBIO ---
class TasaCambioBase(BaseModel):
    moneda: str = "USD"
    tasa: float

class TasaCambioCreate(TasaCambioBase):
    pass

class TasaCambio(TasaCambioBase):
    id: int
    fecha: datetime
    activa: bool

    class Config:
        from_attributes = True

# --- ESQUEMAS PARA LOTES DE INVENTARIO ---
class LoteInventarioBase(BaseModel):
    producto_id: int
    cantidad_inicial: float
    costo_unitario: float
    fecha_vencimiento: Optional[datetime] = None

class LoteInventarioCreate(LoteInventarioBase):
    pass

class LoteInventario(LoteInventarioBase):
    id: int
    cantidad_actual: float
    fecha_ingreso: datetime

    class Config:
        from_attributes = True        

# --- ESQUEMAS PARA VENTAS (POS) ---

# 1. Esto es lo que nos enviará el cajero desde la interfaz (El Carrito)
class ItemCarrito(BaseModel):
    producto_id: int
    cantidad: float

class CrearVenta(BaseModel):
    items: list[ItemCarrito] # Una lista de productos y sus cantidades

# 2. Esto es lo que el sistema devuelve (El Ticket de Compra final)
class DetalleVentaOut(BaseModel):
    producto_id: int
    cantidad: float
    precio_unitario_usd: float
    precio_unitario_local: float

    class Config:
        from_attributes = True

class VentaOut(BaseModel):
    id: int
    fecha: datetime
    total_usd: float
    total_local: float
    tasa_usada: float
    detalles: list[DetalleVentaOut]

    class Config:
        from_attributes = True        