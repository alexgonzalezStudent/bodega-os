from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import models
from app.schemas import schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/lotes/", response_model=schemas.LoteInventario)
def registrar_lote(lote: schemas.LoteInventarioCreate, db: Session = Depends(get_db)):
    # 1. Verificar si el producto maestro existe
    producto = db.query(models.Producto).filter(models.Producto.id == lote.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="El producto indicado no existe en el catálogo")
        
    # 2. Registrar el lote
    nuevo_lote = models.LoteInventario(
        producto_id=lote.producto_id,
        cantidad_inicial=lote.cantidad_inicial,
        cantidad_actual=lote.cantidad_inicial, # Al ingresar, lo actual es igual a lo inicial
        costo_unitario=lote.costo_unitario,
        fecha_vencimiento=lote.fecha_vencimiento
    )
    db.add(nuevo_lote)
    db.commit()
    db.refresh(nuevo_lote)
    return nuevo_lote
# Ruta para LEER todos los lotes de inventario (GET)
@router.get("/lotes/", response_model=list[schemas.LoteInventario])
def obtener_lotes(db: Session = Depends(get_db)):
    lotes = db.query(models.LoteInventario).all()
    return lotes