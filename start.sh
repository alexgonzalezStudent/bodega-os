#!/bin/bash
echo "Limpiando memoria de servidores viejos..."
pkill -f uvicorn
pkill -f vite

echo "1. Encendiendo la Pantalla (React)..."
cd ~/Proyecto_Personal_Alex/bodega-os/frontend
npm run dev &

echo "2. Abriendo el navegador..."
sleep 3
explorer.exe "http://localhost:5173/" &

echo "3. Encendiendo el Cerebro (Python)..."
cd ~/Proyecto_Personal_Alex/bodega-os/backend

# Buscador Inteligente del Entorno Virtual (venv)
if [ -f "../../venv/bin/activate" ]; then
    source "../../venv/bin/activate"
elif [ -f "../venv/bin/activate" ]; then
    source "../venv/bin/activate"
elif [ -f "./venv/bin/activate" ]; then
    source "./venv/bin/activate"
fi

# Ahora que el venv está activado correctamente, encendemos el motor
uvicorn app.main:app

# Si lees esto, algo falló
echo ""
echo "================================================="
echo " ERROR: El servidor de Python no pudo iniciar."
echo "================================================="
read -p "Presiona ENTER para cerrar esta ventana..."