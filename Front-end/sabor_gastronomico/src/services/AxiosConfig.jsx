import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

const axiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/`,
  withCredentials: true, // los tokens viajan en cookies HttpOnly
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== INTERCEPTOR DE RESPUESTA ====================
axiosInstance.interceptors.response.use(
  (respuesta) => {
    return respuesta;
  },

  async (error) => {
    const solicitudOriginal = error.config;

    if (
      error.response?.status === 401 &&
      !solicitudOriginal._reintento &&
      !solicitudOriginal.url.includes("pedidos")
    ) {
      solicitudOriginal._reintento = true;

      try {
        console.log('🔄 Intentando renovar el token...');

        if (solicitudOriginal.url.includes("token/refresh")) {
          throw new Error("No se puede renovar desde refresh");
        }

        await axiosInstance.post('token/refresh/');

        return axiosInstance(solicitudOriginal);

      } catch (errorRefresh) {
        console.error('❌ No se pudo renovar el token, cerrando sesión');

        localStorage.removeItem("usuario");
        window.location.href = '/Login';

        return Promise.reject(errorRefresh);
      }
    }

    console.error('❌ Error en respuesta:', error.response?.status);
    return Promise.reject(error);
  }
);

export default axiosInstance;
