// URL base de la API (sin "/" final).
// - Producción (Vercel): "/api", que vercel.json reenvía al back-end en Railway. Así el navegador
//   ve un solo dominio y las cookies de sesión no se bloquean como cookies de terceros.
// - Desarrollo: el mismo host desde el que se abrió el front (localhost o 127.0.0.1) en el puerto 8000;
//   las cookies no se comparten entre esos dos nombres, así que mezclarlos rompe el login.
// Se puede forzar con VITE_API_URL (ver .env.example).
const porDefecto = import.meta.env.PROD
  ? '/api'
  : `http://${window.location.hostname}:8000/api`;

export const API_BASE_URL = (import.meta.env.VITE_API_URL || porDefecto).replace(/\/+$/, '');
