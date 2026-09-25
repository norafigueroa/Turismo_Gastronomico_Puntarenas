import React, { useState } from "react";
import "./PagContactanos.css";
import { API_BASE_URL } from "../../services/apiConfig";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import Instagram from "../../assets/instagram.png";
import Facebook from "../../assets/facebook.png";
import Tiktok from "../../assets/tiktok.png";

function PagContactanos() {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [formulario, setFormulario] = useState({
    nombre: "",
    correo: "",
    telefono: "",
    asunto: "",
    mensaje: "",
  });

  const handleOpenModal = () => setShowModal(true);
  const handleCloseModal = () => {
    setShowModal(false);
    // Limpiar formulario al cerrar
    setFormulario({
      nombre: "",
      correo: "",
      telefono: "",
      asunto: "",
      mensaje: "",
    });
  };

  const handleCambio = (e) => {
    const { name, value } = e.target;
    setFormulario({
      ...formulario,
      [name]: value,
    });
  };

  const validarFormulario = () => {
    if (!formulario.nombre.trim()) {
      Swal.fire("Error", "El nombre es obligatorio", "error");
      return false;
    }

    if (!formulario.correo.trim()) {
      Swal.fire("Error", "El correo es obligatorio", "error");
      return false;
    }

    if (!formulario.correo.includes("@")) {
      Swal.fire("Error", "El correo no es válido", "error");
      return false;
    }

    if (!formulario.asunto.trim()) {
      Swal.fire("Error", "El asunto es obligatorio", "error");
      return false;
    }

    if (!formulario.mensaje.trim()) {
      Swal.fire("Error", "El mensaje es obligatorio", "error");
      return false;
    }

    if (formulario.mensaje.trim().length < 10) {
      Swal.fire(
        "Error",
        "El mensaje debe tener al menos 10 caracteres",
        "error"
      );
      return false;
    }

    return true;
  };

  const handleEnviar = async (e) => {
    e.preventDefault();

    if (!validarFormulario()) {
      return;
    }

    try {
      setCargando(true);

      const response = await fetch(
        `${API_BASE_URL}/mensajes-contacto`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formulario),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || "Error al enviar el mensaje"
        );
      }

      const data = await response.json();

      await Swal.fire({
        icon: "success",
        title: "¡Mensaje enviado!",
        text: "Gracias por contactarnos. Pronto nos pondremos en contacto contigo.",
        confirmButtonText: "Aceptar",
      });

      handleCloseModal();
    } catch (error) {
      console.error("Error al enviar mensaje:", error);
      Swal.fire(
        "Error",
        error.message || "No se pudo enviar el mensaje. Intenta más tarde.",
        "error"
      );
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="contacto-page">
      <div className="contacto-header">
        <h1>Contáctanos</h1>
        <p>
          ¿Tienes preguntas o deseas más información sobre Puntarenas?
          ¡Estamos aquí para ayudarte!
        </p>
      </div>

      {/* ====== INFORMACIÓN DE CONTACTO ====== */}
      <div className="contacto-info">
        <h2>Información de contacto</h2>
        <ul>
          <li>📧 saborperladelpacifico@gmail.com</li>
          <li>🌐 www.saborperla.cr</li>
          <li>📱 +506 6095 4689</li>
          <li>📍 Puntarenas, Costa Rica</li>
          <li>🕐 Lunes a Sábados - 8:00 a.m. a 6:00 p.m.</li>
        </ul>

        {/* Redes sociales */}
        <div className="redes-sociales">
          <a
            href="https://www.instagram.com/elsabordelaperladelpacifico?igsh=c2hxd3Jkemd6Mnhl"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img src={Instagram} alt="Instagram" />
          </a>
          <a
            href="https://www.facebook.com/share/1Bn4qJV8JQ/?mibextid=wwXIfr"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img src={Facebook} alt="Facebook" />
          </a>
        </div>

        <button className="btn-abrir-modal" onClick={handleOpenModal}>
          Enviar mensaje
        </button>
      </div>

      {/* ====== MODAL DEL FORMULARIO ====== */}
      {showModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button className="modal-cerrar" onClick={handleCloseModal}>
              ✖
            </button>
            <h2>Envíanos un mensaje</h2>
            <form className="contacto-form" onSubmit={handleEnviar}>
              <label>Nombre: *</label>
              <input
                type="text"
                name="nombre"
                placeholder="Tu nombre"
                value={formulario.nombre}
                onChange={handleCambio}
                required
              />

              <label>Correo electrónico: *</label>
              <input
                type="email"
                name="correo"
                placeholder="tucorreo@ejemplo.com"
                value={formulario.correo}
                onChange={handleCambio}
                required
              />

              <label>Teléfono:</label>
              <input
                type="tel"
                name="telefono"
                placeholder="+506 1234-5678"
                value={formulario.telefono}
                onChange={handleCambio}
              />

              <label>Asunto: *</label>
              <input
                type="text"
                name="asunto"
                placeholder="Motivo del mensaje"
                value={formulario.asunto}
                onChange={handleCambio}
                required
              />

              <label>Mensaje: *</label>
              <textarea
                name="mensaje"
                placeholder="Escribe tu mensaje aquí (mínimo 10 caracteres)..."
                rows="5"
                value={formulario.mensaje}
                onChange={handleCambio}
                required
              ></textarea>

              <button
                type="submit"
                className="btn-enviar"
                disabled={cargando}
              >
                {cargando ? "Enviando..." : "Enviar mensaje"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ====== FOOTER TURISMO ====== */}
      <footer className="footer-turismo">
        <p>
          © 2025 El Sabor de la Perla del Pacífico | Todos los derechos
          reservados
        </p>
      </footer>
    </div>
  );
}

export default PagContactanos;