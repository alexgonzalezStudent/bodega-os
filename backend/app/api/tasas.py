from fastapi import APIRouter, Depends
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

@router.post("/", response_model=schemas.TasaCambio)
def registrar_tasa(tasa: schemas.TasaCambioCreate, db: Session = Depends(get_db)):
    # 1. Desactivamos cualquier tasa que estuviera activa
    db.query(models.TasaCambio).filter(models.TasaCambio.activa == True).update({"activa": False})
    
    # 2. Registramos la nueva
    nueva_tasa = models.TasaCambio(moneda=tasa.moneda, tasa=tasa.tasa)
    db.add(nueva_tasa)
    db.commit()
    db.refresh(nueva_tasa)
    return nueva_tasa

@router.get("/actual", response_model=schemas.TasaCambio)
def obtener_tasa_actual(db: Session = Depends(get_db)):
    # Busca la única tasa que tiene activa=True
    tasa = db.query(models.TasaCambio).filter(models.TasaCambio.activa == True).first()
    return tasa