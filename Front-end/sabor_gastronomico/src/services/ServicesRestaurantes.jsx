import { API_BASE_URL } from "./apiConfig";

const API_URL = `${API_BASE_URL}/restaurantes/`;

async function postRestaurante(restauranteData) {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(restauranteData)
        });

        if (!response.ok) {
            let errorDetail = 'Error desconocido al crear el restaurante.';
            try {
                const errorData = await response.json();
                errorDetail = JSON.stringify(errorData);
            } catch (e) {
                errorDetail = await response.text();
            }
            throw new Error(`Respuesta del servidor (${response.status}): ${errorDetail}`);
        }

        return await response.json();

    } catch (error) {
        console.error("Existe un error al crear el restaurante:", error);
        throw error;
    }
}

async function getRestaurantes() {
  const response = await fetch(API_URL); 
  if (!response.ok) {
    throw new Error(`Error al obtener los restaurantes: ${response.status}`);
  }
  return await response.json();
}

async function getRestauranteById(id) {
  const response = await fetch(`${API_URL}${id}`); 
  if (!response.ok) {
    throw new Error(`Error al obtener el restaurante con ID ${id}: ${response.status}`);
  }
  return await response.json();
}


async function updateRestaurante(id, restauranteData) {
    try {
        const response = await fetch(`${API_URL}${id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(restauranteData)
        });

        if (!response.ok) {
            throw new Error(`Error al actualizar el restaurante: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Error al actualizar el restaurante:", error);
        throw error;
    }
}

async function patchRestaurante(id, formData) {
    try {
        const response = await fetch(`${API_URL}${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`Error al modificar parcialmente el restaurante: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Error al modificar parcialmente el restaurante:", error);
        throw error;
    }
}

async function deleteRestaurante(id) {
    try {
        const response = await fetch(`${API_URL}${id}/`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`Error al eliminar el restaurante: ${response.status}`);
        }

        return { message: "Restaurante eliminado correctamente" };
    } catch (error) {
        console.error("Error al eliminar el restaurante:", error);
        throw error;
    }
}

export {getRestaurantes, getRestauranteById, postRestaurante, updateRestaurante, patchRestaurante, deleteRestaurante};
