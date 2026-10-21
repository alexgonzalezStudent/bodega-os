import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Inventario() {
  const [productos, setProductos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [tasaActiva, setTasaActiva] = useState(0)
  const [nuevaTasa, setNuevaTasa] = useState('')
  
  const [seleccionados, setSeleccionados] = useState([])
  const [archivoCSV, setArchivoCSV] = useState(null)

  const [busquedaTabla, setBusquedaTabla] = useState('')
  const [busquedaLote, setBusquedaLote] = useState('')

  const [formularioProducto, setFormularioProducto] = useState({ nombre: '', descripcion: '', codigo_barras: '', categoria_id: '', tipo_unidad: 'unidad' })
  const [formularioLote, setFormularioLote] = useState({ producto_id: '', cantidad_inicial: '', costo_unitario: '', fecha_vencimiento: '' })

  const cargarDatos = () => {
    axios.get('http://127.0.0.1:8000/productos/').then(res => {
      setProductos(res.data)
      if (res.data.length > 0 && !formularioLote.producto_id) setFormularioLote(prev => ({ ...prev, producto_id: res.data[0].id }))
    })
    axios.get('http://127.0.0.1:8000/categorias/').then(res => {
      setCategorias(res.data)
      if (res.data.length > 0 && !formularioProducto.categoria_id) setFormularioProducto(prev => ({ ...prev, categoria_id: res.data[0].id }))
    })
    axios.get('http://127.0.0.1:8000/tasas/activa').then(res => setTasaActiva(res.data.tasa)).catch(() => setTasaActiva(0))
  }

  useEffect(() => { cargarDatos() }, [])

  const actualizarTasa = async (e) => { e.preventDefault(); try { await axios.post('http://127.0.0.1:8000/tasas/', { tasa: parseFloat(nuevaTasa) }); alert("Tasa actualizada"); setNuevaTasa(''); cargarDatos(); } catch (e) { alert("Error"); } }
  
  const guardarProducto = async (e) => { 
    e.preventDefault(); 
    try { 
      const datosParaEnviar = {
        nombre: formularioProducto.nombre,
        tipo_unidad: formularioProducto.tipo_unidad,
        categoria_id: parseInt(formularioProducto.categoria_id)
      };
      await axios.post('http://127.0.0.1:8000/productos/', datosParaEnviar); 
      alert("¡Producto registrado con éxito!"); 
      setFormularioProducto({ ...formularioProducto, nombre: '' }); 
      cargarDatos(); 
    } catch (error) { 
      alert(`Error del servidor: ${error.response?.data?.detail || "Revisa la terminal negra"}`);
    } 
  }

  const guardarLote = async (e) => { 
    e.preventDefault(); 
    try { 
      let idCorrecto = formularioLote.producto_id;
      if (!productosFiltradosLote.find(p => p.id == idCorrecto) && productosFiltradosLote.length > 0) {
        idCorrecto = productosFiltradosLote[0].id;
      }

      const payload = { 
        producto_id: parseInt(idCorrecto), 
        cantidad_inicial: parseInt(formularioLote.cantidad_inicial), 
        costo_unitario: parseFloat(formularioLote.costo_unitario) 
      }; 
      await axios.post('http://127.0.0.1:8000/inventario/lotes/', payload); 
      alert("Mercancía ingresada"); 
      setFormularioLote({ ...formularioLote, cantidad_inicial: '', costo_unitario: '', fecha_vencimiento: '' }); 
      setBusquedaLote('');
      cargarDatos(); 
    } catch (e) { 
      alert("Error al guardar mercancía"); 
    } 
  }

  const suspenderProducto = async (id) => {
    if(!window.confirm("¿Estás seguro de cambiar el estado de este producto?")) return;
    try {
      await axios.put(`http://127.0.0.1:8000/productos/${id}/suspender`);
      cargarDatos(); 
    } catch (e) { 
      alert("Error al suspender el producto"); 
    }
  }
  
  const manejarCambioProd = (e) => setFormularioProducto({ ...formularioProducto, [e.target.name]: e.target.value })
  const manejarCambioLote = (e) => setFormularioLote({ ...formularioLote, [e.target.name]: e.target.value })
  const manejarSeleccion = (id) => setSeleccionados(prev => prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id])

  const imprimirSeleccionados = () => {
    if (seleccionados.length === 0) return alert("Selecciona al menos un producto de la tabla.")
    const idsString = seleccionados.join(',')
    window.open(`http://127.0.0.1:8000/productos/imprimir/masivo?ids=${idsString}`, '_blank')
    setSeleccionados([]) 
  }

  const subirArchivo = async (e) => {
    e.preventDefault()
    if (!archivoCSV) return alert("Selecciona un archivo primero.")
    const formData = new FormData()
    formData.append("file", archivoCSV)
    try {
      const res = await axios.post('http://127.0.0.1:8000/productos/importar-csv/', formData)
      alert(res.data.mensaje)
      cargarDatos()
    } catch (error) {
      alert("Error al procesar el archivo. Revisa el formato.")
    }
  }

  const productosFiltradosTabla = productos.filter(p => p.nombre.toLowerCase().includes(busquedaTabla.toLowerCase()))
  const productosFiltradosLote = productos.filter(p => p.nombre.toLowerCase().includes(busquedaLote.toLowerCase()))

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      {/* PANEL IZQUIERDO */}
      <div className="lg:col-span-1 bg-white rounded-lg shadow p-4 h-[80vh] overflow-y-auto space-y-6">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h2 className="text-lg font-bold text-blue-900 mb-1">Tasa del Día</h2>
          <p className="text-sm text-gray-700 mb-3">Actual: <span className="font-bold text-blue-700">Bs. {tasaActiva}</span></p>
          <form onSubmit={actualizarTasa} className="flex gap-2">
            <input required type="number" step="0.01" value={nuevaTasa} onChange={(e) => setNuevaTasa(e.target.value)} placeholder="Ej. 42.5" className="flex-1 p-2 border rounded focus:ring-2 w-full min-w-0" />
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 rounded">FIJAR</button>
          </form>
        </div>

        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <h2 className="text-sm font-bold text-purple-900 mb-2">⚡ Carga Rápida (Excel CSV)</h2>
          <form onSubmit={subirArchivo} className="space-y-2">
            <input type="file" accept=".csv" onChange={(e) => setArchivoCSV(e.target.files[0])} className="w-full text-xs text-gray-500 file:mr-4 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-purple-100 file:text-purple-700 hover:file:bg-purple-200" />
            <button type="submit" className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-1.5 text-sm rounded">IMPORTAR FACTURA</button>
          </form>
        </div>

        <div>
          <h2 className="text-sm font-bold text-gray-800 border-b pb-1 mb-2">Registro Manual (Individual)</h2>
          <form onSubmit={guardarProducto} className="space-y-2">
            <input required type="text" name="nombre" value={formularioProducto.nombre} onChange={manejarCambioProd} placeholder="Nombre del producto" className="w-full p-2 text-sm border rounded" />
            <div className="grid grid-cols-2 gap-2">
              <select name="categoria_id" value={formularioProducto.categoria_id} onChange={manejarCambioProd} className="w-full p-2 text-sm border rounded">
                {categorias.map(cat => <option key={cat.id} value={cat.id}>{cat.nombre}</option>)}
              </select>
              <select name="tipo_unidad" value={formularioProducto.tipo_unidad} onChange={manejarCambioProd} className="w-full p-2 text-sm border rounded">
                <option value="unidad">Unidad</option><option value="kg">Kg</option><option value="litro">Litros</option>
              </select>
            </div>
            <button type="submit" className="w-full border border-blue-600 text-blue-600 font-bold py-1 text-sm rounded">AGREGAR CATÁLOGO</button>
          </form>
        </div>

        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h2 className="text-sm font-bold text-green-900 mb-2">Ingresar Lote Físico</h2>
          <form onSubmit={guardarLote} className="space-y-2">
            <input type="text" placeholder="🔍 Filtrar producto..." value={busquedaLote} onChange={(e) => setBusquedaLote(e.target.value)} className="w-full p-2 text-sm border border-green-300 rounded focus:ring-2 focus:ring-green-500 outline-none" />
            <select name="producto_id" value={formularioLote.producto_id} onChange={manejarCambioLote} className="w-full p-2 text-sm border rounded font-semibold text-gray-800 bg-white">
              {productosFiltradosLote.length > 0 ? (
                productosFiltradosLote.map(prod => <option key={prod.id} value={prod.id}>{prod.nombre}</option>)
              ) : (
                <option value="">No hay resultados</option>
              )}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <input required type="number" name="cantidad_inicial" value={formularioLote.cantidad_inicial} onChange={manejarCambioLote} placeholder="Cant." className="w-full p-2 text-sm border rounded" />
              <input required type="number" step="0.01" name="costo_unitario" value={formularioLote.costo_unitario} onChange={manejarCambioLote} placeholder="Costo $" className="w-full p-2 text-sm border rounded" />
            </div>
            <button type="submit" className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-1.5 text-sm rounded transition">GUARDAR INVENTARIO</button>
          </form>
        </div>
      </div>

      {/* PANEL DERECHO: Catálogo */}
      <div className="lg:col-span-3 bg-white rounded-lg shadow p-4 h-[80vh] flex flex-col">
        <div className="flex justify-between items-center mb-4 border-b pb-2 gap-4">
          <h2 className="text-xl font-bold text-gray-800 whitespace-nowrap">Catálogo ({productos.length})</h2>
          <input 
            type="text" 
            placeholder="🔍 Buscar para imprimir..." 
            value={busquedaTabla} 
            onChange={(e) => setBusquedaTabla(e.target.value)} 
            className="flex-1 p-2 border border-gray-300 rounded shadow-sm focus:ring-2 focus:ring-blue-500 outline-none max-w-md"
          />
          <button 
            onClick={imprimirSeleccionados}
            className={`${seleccionados.length > 0 ? 'bg-black hover:bg-gray-800 shadow-lg scale-105' : 'bg-gray-300 cursor-not-allowed'} text-white font-bold py-2 px-4 rounded flex items-center gap-2 transition-all whitespace-nowrap`}
          >
            🖨️ IMPRIMIR ({seleccionados.length})
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Imprimir</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unidad</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {productosFiltradosTabla.map(producto => (
                <tr key={producto.id} className={`transition cursor-pointer ${producto.activo !== false ? 'hover:bg-blue-50' : 'bg-red-50 opacity-75'}`} onClick={() => manejarSeleccion(producto.id)}>
                  
                  {/* COLUMNA 1: Checkbox de Imprimir */}
                  <td className="px-4 py-3 text-center">
                    <input type="checkbox" checked={seleccionados.includes(producto.id)} readOnly className="w-4 h-4 text-blue-600 rounded border-gray-300 cursor-pointer" />
                  </td>
                  
                  {/* COLUMNA 2: ID */}
                  <td className="px-4 py-3 text-sm text-gray-500">#{producto.id}</td>
                  
                  {/* COLUMNA 3: Nombre */}
                  <td className="px-4 py-3 text-sm font-bold text-gray-900">
                    {producto.nombre} 
                    {producto.activo === false && <span className="text-red-500 text-xs ml-2">(Suspendido)</span>}
                  </td>
                  
                  {/* COLUMNA 4: Stock */}
                  <td className={`px-4 py-3 text-sm font-extrabold text-center ${producto.stock > 0 ? 'text-blue-600' : 'text-red-500'}`}>
                    {producto.stock}
                  </td>
                  
                  {/* COLUMNA 5: Unidad */}
                  <td className="px-4 py-3 text-sm text-gray-500">{producto.tipo_unidad}</td>

                  {/* COLUMNA 6: Botón de Estado */}
                  <td className="px-4 py-3 text-center">
                    <button 
                      onClick={(e) => { e.stopPropagation(); suspenderProducto(producto.id); }} 
                      className={`px-3 py-1 rounded text-xs font-bold ${producto.activo !== false ? 'bg-red-100 text-red-600 hover:bg-red-200 shadow-sm' : 'bg-green-100 text-green-600 hover:bg-green-200 shadow-sm'}`}>
                      {producto.activo !== false ? 'Suspender' : 'Activar'}
                    </button>
                  </td>

                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}