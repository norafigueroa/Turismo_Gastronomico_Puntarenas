import React, { useEffect, useState } from "react";
import {
  obtenerPedidos,
  actualizarPedido,
  eliminarPedido,
} from "../../../../services/servicesAdminRest/ServicesPedidos";
import Swal from "sweetalert2";
import "./Pedidos.css";

function Pedidos() {
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  // Cargar pedidos al inicio
  useEffect(() => {
    const cargarPedidos = async () => {
      try {
        const data = await obtenerPedidos();
        setPedidos(data);
      } catch (err) {
        setError("Error al cargar los pedidos");
        console.error(err);
      } finally {
        setCargando(false);
      }
    };

    cargarPedidos();
  }, []);

  // Cambiar estado del pedido
  const cambiarEstado = async (id, estado) => {
    try {
      await actualizarPedido(id, { estado_pedido: estado });
      setPedidos((prev) =>
        prev.map((p) => (p.id === id ? { ...p, estado_pedido: estado } : p))
      );

      Swal.fire({
        icon: "success",
        title: "Estado actualizado",
        text: `El pedido ${id} ahora está ${estado.replace("_", " ")}`,
        timer: 1500,
        showConfirmButton: false,
      });
    } catch (err) {
      console.error(err);
      Swal.fire({
        icon: "error",
        title: "Error",
        text: "No se pudo actualizar el estado del pedido",
      });
    }
  };

  // Eliminar pedido
  const handleEliminar = async (id) => {
    const confirm = await Swal.fire({
      title: "¿Eliminar pedido?",
      text: `Se eliminará el pedido ${id}`,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
    });

    if (confirm.isConfirmed) {
      try {
        await eliminarPedido(id);
        setPedidos((prev) => prev.filter((p) => p.id !== id));
        Swal.fire({
          icon: "success",
          title: "Pedido eliminado",
          timer: 1500,
          showConfirmButton: false,
        });
      } catch (err) {
        console.error(err);
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "No se pudo eliminar el pedido",
        });
      }
    }
  };

  if (cargando) return <p>Cargando pedidos...</p>;
  if (error) return <p>{error}</p>;

  return (
    <section className="pedidos-section">
      <h2>Pedidos Recibidos</h2>
      {pedidos.length === 0 ? (
        <p>No hay pedidos en este momento.</p>
      ) : (
        <table className="tabla-pedidos">
          <thead>
            <tr>
              <th>ID</th>
              <th>Cliente</th>
              <th>Fecha</th>
              <th>Platos</th>
              <th>Total</th>
              <th>Método Pago</th>
              <th>Estado</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            {pedidos.map((pedido) => (
              <tr key={pedido.id}>
                <td>{pedido.id}</td>
                <td>{pedido.usuario_nombre}</td>
                <td>{new Date(pedido.fecha_pedido).toLocaleString()}</td>
                <td>
                  {pedido.detalles.map((item) => (
                    <div key={item.id}>
                      {item.cantidad}x {item.platillo_nombre} — ₡
                      {Number(item.subtotal).toLocaleString("es-CR")}
                    </div>
                  ))}
                </td>
                <td>₡{Number(pedido.total).toLocaleString("es-CR")}</td>
                <td>{pedido.metodo_pago}</td>
                <td>{pedido.estado_pedido.replace("_", " ")}</td>
                <td>
                  <select
                    value={pedido.estado_pedido}
                    onChange={(e) =>
                      cambiarEstado(pedido.id, e.target.value)
                    }
                  >
                    <option value="pendiente">Pendiente</option>
                    <option value="en_proceso">En proceso</option>
                    <option value="entregado">Entregado</option>
                    <option value="cancelado">Cancelado</option>
                  </select>
                  <button
                    className="btn-eliminar"
                    onClick={() => handleEliminar(pedido.id)}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default Pedidos;
