import axios from "axios";
import { API_BASE_URL } from "./apiConfig";

class LugaresServices {
  static async obtenerLugares() {
    try {
      const response = await axios.get(`${API_BASE_URL}/lugares-turisticos`);
      return response.data;
    } catch (error) {
      console.error("Error obteniendo lugares:", error);
      throw error;
    }
  }
}

export default LugaresServices;
