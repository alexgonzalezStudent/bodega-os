import { useState, useEffect } from 'react'
import axios from 'axios'
import Inventario from './Inventario'

function App() {
  const [vistaActiva, setVistaActiva] = useState('caja') 
  const [productos, setProductos] = useState([])
  const [carrito, setCarrito] = useState([])
  const [totales, setTotales] = useState({ usd: 0, local: 0 })
  const [busqueda, setBusqueda] = useState("")
  
  const [ticketVenta, setTicketVenta] = useState(null)

  useEffect(() => {
    if (vistaActiva === 'caja') {
      axios.get('http://127.0.0.1:8000/productos/')
        .then(respuesta => setProductos(respuesta.data))
        .catch(error => console.error(error))
    }
  }, [vistaActiva])

  const agregarAlCarrito = async (producto) => {
    const itemExistente = carrito.find(item => item.id === producto.id)
    if (itemExistente) {
      modificarCantidad(producto.id, 1)
    } else {
      try {
        const respuesta = await axios.get(`http://127.0.0.1:8000/productos/${producto.id}/precio`)
        const precioData = respuesta.data
        const nuevoItem = {
          id: producto.id, nombre: producto.nombre, cantidad: 1, 
          precio_usd: precioData.precio_venta_usd, precio_local: precioData.precio_venta_local
        }
        actualizarEstadoCarrito([...carrito, nuevoItem])
      } catch (error) {
        alert("Error al obtener precio. Verifica inventario y tasa.")
      }
    }
  }

  const modificarCantidad = (id, cambio) => {
    const nuevoCarrito = carrito.map(item => {
      if (item.id === id) {
        return { ...item, cantidad: item.cantidad + cambio }
      }
      return item
    }).filter(item => item.cantidad > 0)
    actualizarEstadoCarrito(nuevoCarrito)
  }

  const actualizarEstadoCarrito = (nuevoCarrito) => {
    setCarrito(nuevoCarrito)
    let sumUsd = 0, sumLocal = 0
    nuevoCarrito.forEach(item => {
      sumUsd += item.precio_usd * item.cantidad
      sumLocal += item.precio_local * item.cantidad
    })
    setTotales({ usd: sumUsd, local: sumLocal })
  }

  const procesarCobro = async () => {
    if (carrito.length === 0) return alert("El carrito está vacío.")
    const datosVenta = { items: carrito.map(item => ({ producto_id: item.id, cantidad: item.cantidad })) }
    
    try {
      const respuesta = await axios.post('http://127.0.0.1:8000/ventas/', datosVenta)
      
      setTicketVenta({
        id: respuesta.data.id,
        total_local: respuesta.data.total_local,
        total_usd: totales.usd 
      })
      
      setCarrito([])
      setTotales({ usd: 0, local: 0 })
      const resProductos = await axios.get('http://127.0.0.1:8000/productos/')
      setProductos(resProductos.data)
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || "Error desconocido"}`)
    }
  }

  const generarCorteCaja = async () => {
    try {
      const respuesta = await axios.get('http://127.0.0.1:8000/ventas/reporte/diario')
      const datos = respuesta.data
      alert(`📊 CORTE DEL DÍA (${datos.fecha})\n\nTickets emitidos: ${datos.cantidad_tickets}\nTotal en Caja (USD): $${datos.total_usd.toFixed(2)}\nTotal en Caja (Local): Bs. ${datos.total_local.toFixed(2)}\n\n¡Buen trabajo hoy!`)
    } catch (error) {
      alert("Error al generar el reporte.")
    }
  } 

  // LA REGLA CLAVE: Ocultar los que dicen 'activo === false'
  const productosFiltrados = productos.filter(producto => 
    producto.activo !== false && producto.nombre.toLowerCase().includes(busqueda.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-200 p-4 relative">
      <header className="bg-blue-800 text-white p-4 rounded-lg shadow mb-4 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <h1 className="text-2xl font-bold">Bodega OS</h1>
          <nav className="flex gap-2">
            <button onClick={() => setVistaActiva('caja')} className={`px-4 py-2 rounded transition font-medium ${vistaActiva === 'caja' ? 'bg-blue-600 shadow-inner' : 'hover:bg-blue-700 text-blue-200'}`}>Caja Registradora</button>
            <button onClick={() => setVistaActiva('inventario')} className={`px-4 py-2 rounded transition font-medium ${vistaActiva === 'inventario' ? 'bg-blue-600 shadow-inner' : 'hover:bg-blue-700 text-blue-200'}`}>Gestión de Catálogo</button>
          </nav>
        </div>
        <div className="flex gap-3">
          <span className="bg-blue-600 px-3 py-2 rounded font-bold text-sm">Usuario: Alexander</span>
          <button onClick={generarCorteCaja} className="bg-yellow-500 hover:bg-yellow-600 text-yellow-900 px-3 py-2 rounded font-bold text-sm transition">Corte del Día</button>
        </div>
      </header>

      {vistaActiva === 'caja' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 bg-white rounded-lg shadow p-4 h-[80vh] flex flex-col">
            <input type="text" placeholder="Buscar producto..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} className="w-full p-3 border border-gray-300 rounded mb-4 focus:ring-2 focus:ring-blue-500 outline-none" />
            <div className="flex-1 overflow-y-auto">
              <h2 className="text-lg font-bold text-gray-700 mb-2">Catálogo Disponible</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {productosFiltrados.map(producto => (
                  <div key={producto.id} onClick={() => agregarAlCarrito(producto)} className="border p-3 rounded shadow-sm hover:bg-blue-100 cursor-pointer relative overflow-hidden transition">
                    <p className="font-semibold text-gray-800 leading-tight">{producto.nombre}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Unidad: {producto.tipo_unidad} | <span className={`ml-1 font-bold ${producto.stock > 0 ? 'text-green-600' : 'text-red-500'}`}>Disp: {producto.stock}</span>
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4 h-[80vh] flex flex-col">
            <h2 className="text-xl font-bold text-gray-800 border-b pb-2 mb-4">Ticket de Venta</h2>
            <div className="flex-1 overflow-y-auto pr-2">
              {carrito.length === 0 ? <p className="text-center text-gray-400 mt-10">El carrito está vacío</p> : (
                carrito.map((item, index) => (
                  <div key={index} className="flex flex-col border-b py-3 text-sm">
                    <div className="flex justify-between font-bold text-gray-800">
                      <span>{item.nombre}</span>
                      <span>${(item.precio_usd * item.cantidad).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-gray-500">${item.precio_usd.toFixed(2)} c/u</span>
                      <div className="flex items-center gap-3 bg-gray-100 rounded px-2 py-1">
                        <button onClick={() => modificarCantidad(item.id, -1)} className="text-red-500 font-bold hover:scale-125 transition text-lg px-2">-</button>
                        <span className="font-bold text-gray-700">{item.cantidad}</span>
                        <button onClick={() => modificarCantidad(item.id, 1)} className="text-green-500 font-bold hover:scale-125 transition text-lg px-2">+</button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="border-t pt-4 mt-4">
              <div className="flex justify-between mb-2"><span className="font-bold">Total USD:</span><span className="font-bold text-green-600">${totales.usd.toFixed(2)}</span></div>
              <div className="flex justify-between text-xl mb-4"><span className="font-bold">Total Local:</span><span className="font-bold text-blue-600">Bs. {totales.local.toFixed(2)}</span></div>
              <button onClick={procesarCobro} className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-4 rounded text-lg shadow-md transition-all active:scale-95">COBRAR VENTA</button>
            </div>
          </div>
        </div>
      ) : (
        <Inventario />
      )}

      {ticketVenta && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full text-center">
            <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-green-100 mb-5">
              <svg className="h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            
            <h2 className="text-3xl font-extrabold text-gray-800 mb-2">¡Cobro Exitoso!</h2>
            <p className="text-gray-500 mb-6 font-medium">Ticket de sistema #{ticketVenta.id}</p>
            
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 mb-8 shadow-inner">
              <p className="text-xs text-gray-400 uppercase font-bold tracking-widest mb-2">Total Pagado</p>
              <p className="text-4xl font-black text-blue-600 mb-3">Bs. {ticketVenta.total_local.toFixed(2)}</p>
              <p className="text-xl font-bold text-green-700 bg-green-100 rounded-lg py-1">REF: ${ticketVenta.total_usd.toFixed(2)}</p>
            </div>
            
            <button
              onClick={() => setTicketVenta(null)}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 rounded-xl transition-colors shadow-lg text-lg"
            >
              SIGUIENTE CLIENTE
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App