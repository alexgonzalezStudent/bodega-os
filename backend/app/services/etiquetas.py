import os
from fpdf import FPDF

def generar_etiqueta_pdf(nombre_producto: str, precio_usd: float, precio_local: float, id_producto: int):
    # Creamos un PDF con formato de etiqueta horizontal pequeña (80mm x 50mm)
    pdf = FPDF(orientation='L', unit='mm', format=(80, 50))
    pdf.add_page()
    
    # Nombre del producto (Centrado y en negrita)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, nombre_producto, align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Precio en Divisa (Letra normal)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Ref: ${precio_usd}", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Precio en Moneda Local (Letra muy grande para que el cliente lo vea claro)
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 15, f"Bs. {precio_local}", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Creamos una carpeta temporal si no existe para guardar los PDFs
    os.makedirs("temp", exist_ok=True)
    ruta_archivo = f"temp/etiqueta_{id_producto}.pdf"
    
    # Guardamos el archivo
    pdf.output(ruta_archivo)
    
    return ruta_archivo

from weasyprint import HTML
import os

def generar_etiquetas_masivas_pdf(lista_etiquetas):
    # Diseñamos una cuadrícula estilo bloque para aprovechar toda la hoja
    html_content = """
    <html>
    <head><style>
        body { font-family: 'Arial', sans-serif; margin: 0; padding: 15px; }
        .grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; }
        .etiqueta { 
            border: 2px dashed #444; width: 170px; height: 90px; 
            padding: 10px; text-align: center; display: flex; 
            flex-direction: column; justify-content: center; align-items: center;
        }
        .nombre { font-size: 11px; font-weight: bold; color: #333; text-transform: uppercase; margin-bottom: 8px;}
        .precio { font-size: 26px; font-weight: 900; color: #000; }
    </style></head>
    <body>
    <div class="grid">
    """
    
    # Llenamos la cuadrícula con los productos seleccionados
    for et in lista_etiquetas:
        html_content += f"<div class='etiqueta'><div class='nombre'>{et['nombre']}</div><div class='precio'>${et['precio_usd']}</div></div>"
    
    html_content += "</div></body></html>"

    ruta_pdf = "etiquetas_masivas.pdf"
    # Convertimos el HTML a PDF (Reutilizando tu conocimiento previo con WeasyPrint)
    HTML(string=html_content).write_pdf(ruta_pdf)
    return ruta_pdf

