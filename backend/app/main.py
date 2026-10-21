from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- NUEVA IMPORTACIÓN
from app.models.models import Base
from app.db.database import engine
from app.api import categorias, productos, tasas, inventario, ventas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bodega OS API", description="Sistema de gestión para bodega")

# <-- NUEVO BLOQUE DE PERMISOS CORS -->
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que cualquier frontend se conecte (ideal para desarrollo)
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# Conexión de rutas
app.include_router(categorias.router, prefix="/categorias", tags=["Categorías"])
app.include_router(productos.router, prefix="/productos", tags=["Productos"])
app.include_router(tasas.router, prefix="/tasas", tags=["Tasas de Cambio"])
app.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
app.include_router(ventas.router, prefix="/ventas", tags=["Punto de Venta"])

@app.get("/")
def ruta_de_prueba():
    return {"mensaje": "¡El servidor de la bodega está funcionando a la perfección!"}