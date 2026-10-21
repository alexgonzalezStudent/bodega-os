from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import models
from app.schemas import schemas
from app.services.precios import calcular_precios
from datetime import datetime, time

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.VentaOut)
def procesar_venta(carrito: schemas.CrearVenta, margen: float = 0.30, db: Session = Depends(get_db)):
    # 1. Obtener a cómo está el dólar hoy
    tasa = db.query(models.TasaCambio).filter(models.TasaCambio.activa == True).first()
    if not tasa:
        raise HTTPException(status_code=400, detail="No hay tasa de cambio activa. Imposible vender.")

    # 2. Crear el ticket de venta en blanco
    nueva_venta = models.Venta(tasa_usada=tasa.tasa, total_usd=0.0, total_local=0.0)
    db.add(nueva_venta)
    # ATENCIÓN AQUÍ: flush() guarda temporalmente la venta para que SQLite le asigne un ID (ej. Ticket #1), 
    # pero NO lo hace definitivo aún. Lo necesitamos para enlazar los productos a este ticket.
    db.flush() 

    total_usd_venta = 0.0
    total_local_venta = 0.0

    # 3. Recorrer la lista de productos que el cliente quiere comprar
    for item in carrito.items:
        producto = db.query(models.Producto).filter(models.Producto.id == item.producto_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto ID {item.producto_id} no encontrado.")

        # Buscar todos los lotes de este producto que tengan cantidad disponible, ordenados del más viejo al más nuevo (FIFO)
        lotes_disponibles = db.query(models.LoteInventario).filter(
            models.LoteInventario.producto_id == item.producto_id,
            models.LoteInventario.cantidad_actual > 0
        ).order_by(models.LoteInventario.fecha_ingreso.asc()).all()

        # Verificar si hay suficiente mercancía en toda la bodega para cubrir lo que pide el cliente
        inventario_total = sum(lote.cantidad_actual for lote in lotes_disponibles)
        if inventario_total < item.cantidad:
            raise HTTPException(
                status_code=400, 
                detail=f"Inventario insuficiente para {producto.nombre}. Solo quedan {inventario_total}."
            )

        # Calcular el precio de venta basándonos en el lote más reciente (para no perder dinero por inflación)
        ultimo_lote = db.query(models.LoteInventario).filter(
            models.LoteInventario.producto_id == item.producto_id
        ).order_by(models.LoteInventario.fecha_ingreso.desc()).first()
        
        precios = calcular_precios(ultimo_lote.costo_unitario, margen, tasa.tasa)
        precio_unit_usd = precios["precio_usd"]
        precio_unit_local = precios["precio_local"]

        # ALGORITMO FIFO: Descontar la mercancía caja por caja
        cantidad_por_descontar = item.cantidad
        for lote in lotes_disponibles:
            if cantidad_por_descontar <= 0:
                break # Ya descontamos todo lo que el cliente pidió
            
            if lote.cantidad_actual >= cantidad_por_descontar:
                # Si esta caja tiene suficiente, lo restamos todo de aquí
                lote.cantidad_actual -= cantidad_por_descontar
                cantidad_por_descontar = 0
            else:
                # Si la caja tiene menos de lo que pide, la vaciamos y seguimos buscando en la siguiente caja
                cantidad_por_descontar -= lote.cantidad_actual
                lote.cantidad_actual = 0

        # Crear el registro del producto en el ticket de venta
        detalle = models.DetalleVenta(
            venta_id=nueva_venta.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario_usd=precio_unit_usd,
            precio_unitario_local=precio_unit_local
        )
        db.add(detalle)

        # Sumar el dinero a la caja registradora virtual
        total_usd_venta += (precio_unit_usd * item.cantidad)
        total_local_venta += (precio_unit_local * item.cantidad)

    # 4. Finalizar el ticket con los totales exactos
    nueva_venta.total_usd = round(total_usd_venta, 2)
    nueva_venta.total_local = round(total_local_venta, 2)
    
    # commit() ahora sí hace que todo el proceso sea definitivo e irreversible en la base de datos
    db.commit()
    db.refresh(nueva_venta)

    return nueva_venta

@router.get("/reporte/diario")
def reporte_diario(db: Session = Depends(get_db)):
    # 1. Calculamos el rango de horas de hoy (desde las 00:00 hasta las 23:59)
    hoy = datetime.now().date()
    inicio_dia = datetime.combine(hoy, time.min)
    fin_dia = datetime.combine(hoy, time.max)

    # 2. Buscamos todas las ventas que ocurrieron en ese rango de tiempo
    ventas_hoy = db.query(models.Venta).filter(
        models.Venta.fecha >= inicio_dia,
        models.Venta.fecha <= fin_dia
    ).all()

    # 3. Sumamos los totales
    total_usd = sum(venta.total_usd for venta in ventas_hoy)
    total_local = sum(venta.total_local for venta in ventas_hoy)
    cantidad_tickets = len(ventas_hoy)

    return {
        "fecha": hoy.strftime("%d/%m/%Y"),
        "cantidad_tickets": cantidad_tickets,
        "total_usd": round(total_usd, 2),
        "total_local": round(total_local, 2)
    }    