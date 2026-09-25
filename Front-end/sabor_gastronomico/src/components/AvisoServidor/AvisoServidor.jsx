import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../../services/apiConfig';

// El back-end gratuito se duerme tras un rato sin visitas y tarda hasta ~1 minuto en despertar.
// Al abrir el sitio se le hace una petición ligera y, si tarda, se avisa al visitante.
const UMBRAL_MS = 3000;

const estilo = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  zIndex: 10000,
  padding: '10px 16px',
  background: '#1f2937',
  color: '#fff',
  textAlign: 'center',
  fontSize: '0.95rem',
};

function AvisoServidor() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!import.meta.env.PROD) return undefined;

    const temporizador = setTimeout(() => setVisible(true), UMBRAL_MS);
    const controlador = new AbortController();

    fetch(`${API_BASE_URL}/configuracion/`, { signal: controlador.signal })
      .catch(() => {})
      .finally(() => {
        clearTimeout(temporizador);
        setVisible(false);
      });

    return () => {
      clearTimeout(temporizador);
      controlador.abort();
    };
  }, []);

  if (!visible) return null;

  return (
    <div role="status" style={estilo}>
      Despertando el servidor… puede tardar hasta un minuto la primera vez. ¡Gracias por la paciencia!
    </div>
  );
}

export default AvisoServidor;
