import { createContext, useState } from "react";

export const CartContext = createContext();

export function CartProvider({ children }) {
  const [cartItems, setCartItems] = useState([]);
  const [restauranteId, setRestauranteId] = useState(null);

  function addToCart(item) {
    // 🚫 Bloquear mezcla de restaurantes
    if (restauranteId && restauranteId !== item.restaurante) {
      alert("No puedes mezclar platillos de diferentes restaurantes");
      return;
    }

    setRestauranteId(item.restaurante);

    setCartItems((prev) => {
      const existente = prev.find((p) => p.id === item.id);

      if (existente) {
        return prev.map((p) =>
          p.id === item.id
            ? { ...p, cantidad: p.cantidad + 1 }
            : p
        );
      }

      // El carrito guarda el precio vigente (con promoción), igual que lo cobra el servidor.
      const precioVigente =
        item.promocion && item.precio_descuento ? item.precio_descuento : item.precio;

      return [...prev, { ...item, precio: precioVigente, cantidad: 1 }];
    });
  }

  function incrementarCantidad(id) {
    setCartItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, cantidad: item.cantidad + 1 }
          : item
      )
    );
  }

  function disminuirCantidad(id) {
    setCartItems((prev) =>
      prev
        .map((item) =>
          item.id === id
            ? { ...item, cantidad: item.cantidad - 1 }
            : item
        )
        .filter((item) => item.cantidad > 0)
    );
  }

  function removeFromCart(id) {
    setCartItems((prev) => prev.filter((item) => item.id !== id));
  }

  function clearCart() {
    setCartItems([]);
    setRestauranteId(null);
  }

  return (
    <CartContext.Provider
      value={{
        cartItems,
        addToCart,
        incrementarCantidad,
        disminuirCantidad,
        removeFromCart,
        clearCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}
