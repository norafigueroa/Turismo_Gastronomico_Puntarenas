import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

export async function refreshAccessToken() {
  try {
    console.log('🔄 Renovando token...');

    await axios.post(
      `${API_BASE_URL}/token/refresh/`,
      {},
      { withCredentials: true }
    );

    console.log('✅ Token renovado');
    return true;

  } catch (error) {
    console.error('❌ Error al renovar token:', error.response?.data || error.message);
    return false;
  }
}
