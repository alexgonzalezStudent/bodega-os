def calcular_precios(costo_base: float, margen: float, tasa_activa: float):
    # TU FÓRMULA MATEMÁTICA REAL DE RETAIL
    # Costo dividido entre (1 - margen) para garantizar la ganancia exacta
    precio_usd = round(costo_base / (1 - margen), 2)
    
    # Conversión a moneda local
    precio_local = round(precio_usd * tasa_activa, 2)
    
    return {
        "precio_usd": precio_usd,
        "precio_local": precio_local
    }