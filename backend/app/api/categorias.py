from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import models
from app.schemas import schemas

# Creamos un "Router", que es como un mini-FastAPI solo para las rutas de categorías
router = APIRouter()

# Esta función abre una conexión a la base de datos cada vez que alguien hace una petición, 
# y la cierra automáticamente al terminar.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ruta para CREAR una categoría (POST)
@router.post("/", response_model=schemas.Categoria)
def crear_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    # 1. Verificamos que no exista ya una categoría con ese nombre exacto
    db_categoria = db.query(models.Categoria).filter(models.Categoria.nombre == categoria.nombre).first()
    if db_categoria:
        raise HTTPException(status_code=400, detail="Esa categoría ya existe en la bodega")
    
    # 2. Creamos la categoría y la guardamos físicamente
    nueva_categoria = models.Categoria(nombre=categoria.nombre, descripcion=categoria.descripcion)
    db.add(nueva_categoria)
    db.commit() # Guarda los cambios
    db.refresh(nueva_categoria) # Refresca para obtener el ID que le asignó SQLite
    
    return nueva_categoria

# Ruta para LEER todas las categorías (GET)
@router.get("/", response_model=list[schemas.Categoria])
def obtener_categorias(db: Session = Depends(get_db)):
    # Simplemente le pedimos a la base de datos que devuelva todo lo que hay en la tabla
    categorias = db.query(models.Categoria).all()
    return categorias