from app.services.precios import calcular_precios
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import models
from app.schemas import schemas
from fastapi.responses import FileResponse
from app.services.etiquetas import generar_etiqueta_pdf
from fastapi import UploadFile, File, Query
import csv
import io

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ruta para CREAR un producto (POST)
@router.post("/", response_model=schemas.Producto)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    
    # 1. Validar que la categoría que indicó el usuario realmente exista
    categoria_db = db.query(models.Categoria).filter(models.Categoria.id == producto.categoria_id).first()
    if not categoria_db:
        raise HTTPException(status_code=404, detail="La categoría indicada no existe")

    # 2. Validar que no estemos duplicando un código de barras (solo si trae código)
    if producto.codigo_barras:
        prod_existente = db.query(models.Producto).filter(models.Producto.codigo_barras == producto.codigo_barras).first()
        if prod_existente:
            raise HTTPException(status_code=400, detail="Ya existe un producto con este código de barras")

    # 3. Guardar el producto
    nuevo_producto = models.Producto(
        nombre=producto.nombre,
        codigo_barras=producto.codigo_barras,
        tipo_unidad=producto.tipo_unidad,
        activo=producto.activo,
        categoria_id=producto.categoria_id
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    
    return nuevo_producto

# Ruta para LEER todos los productos y sumar su STOCK (GET)
# Ruta para LEER todos los productos y sumar su STOCK (GET)
@router.get("/")
def obtener_productos(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()
    lista_productos = []
    
    for p in productos:
        # Busca todos los lotes de este producto y suma lo que queda disponible
        lotes = db.query(models.LoteInventario).filter(models.LoteInventario.producto_id == p.id).all()
        stock_total = sum(lote.cantidad_actual for lote in lotes)
        
        # Enviamos la información a React
        lista_productos.append({
            "id": p.id,
            "nombre": p.nombre,
            "tipo_unidad": p.tipo_unidad,
            "categoria_id": p.categoria_id,
            "stock": stock_total,
            "activo": p.activo # <-- ESTA ES LA LÍNEA MÁGICA QUE FALTABA
        })
        
    return lista_productos

# Ruta para OBTENER EL PRECIO CALCULADO de un producto (GET)
@router.get("/{producto_id}/precio")
def obtener_precio_producto(producto_id: int, margen: float = 0.30, db: Session = Depends(get_db)):
    
    # 1. Buscar el último lote de este producto para saber a cómo lo compraste
    # Filtramos para que solo busque lotes que aún tengan cantidad > 0, 
    # ordenados del más reciente al más antiguo.
    ultimo_lote = db.query(models.LoteInventario).filter(
        models.LoteInventario.producto_id == producto_id,
        models.LoteInventario.cantidad_actual > 0
    ).order_by(models.LoteInventario.fecha_ingreso.desc()).first()

    if not ultimo_lote:
        raise HTTPException(status_code=404, detail="No hay inventario disponible para este producto")

    # 2. Buscar la tasa de cambio activa del día
    tasa = db.query(models.TasaCambio).filter(models.TasaCambio.activa == True).first()
    if not tasa:
        raise HTTPException(status_code=400, detail="No hay una tasa de cambio activa registrada")

    # 3. Calcular el precio final usando nuestro servicio matemático
    precios_calculados = calcular_precios(
        costo_base=ultimo_lote.costo_unitario,
        margen=margen,
        tasa_activa=tasa.tasa
    )

    return {
        "producto_id": producto_id,
        "costo_registrado_usd": ultimo_lote.costo_unitario,
        "margen_aplicado": margen,
        "tasa_usada": tasa.tasa,
        "precio_venta_usd": precios_calculados["precio_usd"],
        "precio_venta_local": precios_calculados["precio_local"]
    }

# Ruta para DESCARGAR la etiqueta en PDF lista para el anaquel
@router.get("/{producto_id}/etiqueta")
def descargar_etiqueta(producto_id: int, margen: float = 0.30, db: Session = Depends(get_db)):
    # 1. Buscamos el nombre del producto
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # 2. Buscamos el costo en el inventario y la tasa actual
    ultimo_lote = db.query(models.LoteInventario).filter(
        models.LoteInventario.producto_id == producto_id,
        models.LoteInventario.cantidad_actual > 0
    ).order_by(models.LoteInventario.fecha_ingreso.desc()).first()
    
    tasa = db.query(models.TasaCambio).filter(models.TasaCambio.activa == True).first()
    
    if not ultimo_lote or not tasa:
        raise HTTPException(status_code=400, detail="Falta inventario o tasa para calcular la etiqueta")

    # 3. Calculamos los precios (reutilizando tu motor financiero)
    precios = calcular_precios(ultimo_lote.costo_unitario, margen, tasa.tasa)
    
    # 4. Dibujamos el PDF
    ruta_pdf = generar_etiqueta_pdf(
        nombre_producto=producto.nombre, 
        precio_usd=precios["precio_usd"], 
        precio_local=precios["precio_local"], 
        id_producto=producto_id
    )
    
    # 5. FileResponse le dice al navegador "descarga este archivo" en lugar de mostrar texto
    return FileResponse(ruta_pdf, media_type="application/pdf", filename=f"{producto.nombre}_etiqueta.pdf")

import csv
import io
from fastapi import UploadFile, File, Query

# RUTA 1: Imprimir varias etiquetas en una sola hoja
@router.get("/imprimir/masivo")
def imprimir_etiquetas_masivas(ids: str = Query(...), margen: float = 0.30, db: Session = Depends(get_db)):
    from app.services.etiquetas import generar_etiquetas_masivas_pdf
    
    lista_ids = [int(id.strip()) for id in ids.split(",")]
    lista_etiquetas = []
    
    for prod_id in lista_ids:
        producto = db.query(models.Producto).filter(models.Producto.id == prod_id).first()
        if not producto: continue
        
        ultimo_lote = db.query(models.LoteInventario).filter(
            models.LoteInventario.producto_id == prod_id,
            models.LoteInventario.cantidad_actual > 0
        ).order_by(models.LoteInventario.fecha_ingreso.desc()).first()
        
        if ultimo_lote:
            # Calculamos el precio real como lo definimos antes
            precio_usd = round(ultimo_lote.costo_unitario / (1 - margen), 2)
            lista_etiquetas.append({"nombre": producto.nombre, "precio_usd": precio_usd})
    
    if not lista_etiquetas:
        raise HTTPException(status_code=400, detail="No hay inventario para los productos seleccionados")
        
    ruta_pdf = generar_etiquetas_masivas_pdf(lista_etiquetas)
    return FileResponse(ruta_pdf, media_type="application/pdf", filename="Etiquetas_Anaquel.pdf")

@router.post("/importar-csv/")
async def importar_factura_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    
    # FIX 1: 'utf-8-sig' destruye el caracter invisible (BOM) que pone Excel
    try:
        decoded = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        decoded = content.decode('latin-1') # Por si el Excel está en español antiguo
        
    delimitador = ';' if ';' in decoded.split('\n')[0] else ','
    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimitador)
    
    prod_creados, lotes_creados = 0, 0
    
    for row in reader:
        # FIX 2: Limpiamos espacios fantasmas en los nombres de las columnas
        row_limpia = {str(k).strip(): v for k, v in row.items() if k is not None}
        
        nombre = row_limpia.get('nombre', '').strip()
        if not nombre: 
            continue
            
        try:
            cat_id = int(row_limpia.get('categoria_id', 1))
            tipo = row_limpia.get('tipo_unidad', 'unidad').strip()
            cantidad = int(row_limpia.get('cantidad', 0))
            
            # FIX 3: Si Excel guardó el dólar con coma (ej: 1,13), lo forzamos a punto (1.13)
            costo_str = str(row_limpia.get('costo_usd', '0')).replace(',', '.')
            costo_usd = float(costo_str)
        except ValueError:
            # Si hay letras donde van números, salta la fila y sigue con la otra
            continue
            
        if cantidad <= 0 or costo_usd <= 0: 
            continue
        
        # Guardado en Base de Datos
        producto = db.query(models.Producto).filter(models.Producto.nombre == nombre).first()
        if not producto:
            producto = models.Producto(nombre=nombre, categoria_id=cat_id, tipo_unidad=tipo)
            db.add(producto)
            db.commit()
            db.refresh(producto)
            prod_creados += 1
            
        nuevo_lote = models.LoteInventario(
            producto_id=producto.id, 
            cantidad_inicial=cantidad, 
            cantidad_actual=cantidad, 
            costo_unitario=costo_usd
        )
        db.add(nuevo_lote)
        db.commit()
        lotes_creados += 1
        
    return {"mensaje": f"¡Éxito! {prod_creados} productos nuevos creados y {lotes_creados} lotes ingresados."}

# NUEVA RUTA PARA SUSPENDER O ACTIVAR UN PRODUCTO
@router.put("/{producto_id}/suspender")
def suspender_producto(producto_id: int, db: Session = Depends(get_db)):
    # 1. Buscamos el producto por su ID
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # 2. Invertimos el estado (Si era True pasa a False, y viceversa)
    producto.activo = not producto.activo
    db.commit()
    return {"mensaje": "Estado actualizado", "activo": producto.activo}