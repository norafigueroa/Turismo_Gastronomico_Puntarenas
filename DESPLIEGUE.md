# Guía de despliegue gratuito: Neon + Render + Vercel

```
Navegador ──► Vercel (React) ──/api/*──► Render (Django) ──► Neon (Postgres)
                  │                            │
                  └─ un solo dominio           └─ imágenes: Cloudinary
```

El navegador solo habla con Vercel. Vercel reenvía `/api/...` a Render (regla en
`Front-end/sabor_gastronomico/vercel.json`), así las cookies de sesión son del mismo dominio.

**Orden: Neon → Render → Vercel** (cada uno necesita datos del anterior).
Los planes gratuitos cambian; confirma las condiciones al registrarte.

---

## Paso 1. Código en GitHub y secretos ✅ (ya hecho)

- Código subido a GitHub.
- Clave de Cloudinary rotada. Ten a mano: *Cloud name*, *API Key* y *API Secret* **nuevos**.

## Paso 2. Neon (base de datos)

1. Entra a [neon.tech](https://neon.tech) → **Sign up** con GitHub.
2. Crea un proyecto (nombre libre, p. ej. `sabor-gastronomico`). Elige la región más cercana a Oregon/EE. UU. Este
   si puedes (Render gratuito está en EE. UU.).
3. En el panel del proyecto pulsa **Connect** y copia la **connection string** (empieza por `postgresql://`
   y termina en `?sslmode=require`). Ese texto es tu `DATABASE_URL`. **Guárdalo en un bloc de notas.**
   Contiene tu contraseña: no lo pegues en ningún archivo del proyecto.

## Paso 3. Render (back-end)

1. Entra a [render.com](https://render.com) → **Get Started** con GitHub.
2. **New +** → **Blueprint** → conecta tu repositorio `Turismo_Gastronomico_Puntarenas` → Render detecta `render.yaml`.
3. Te pedirá los valores de estas variables:

   | Variable | Qué poner |
   |---|---|
   | `DATABASE_URL` | la connection string de Neon (Paso 2) |
   | `CLOUDINARY_CLOUD_NAME` | tu cloud name |
   | `CLOUDINARY_API_KEY` | la API key nueva |
   | `CLOUDINARY_API_SECRET` | el API secret nuevo |

   (`DJANGO_SECRET_KEY` la genera Render sola.)
4. Pulsa **Apply / Deploy**. El primer despliegue tarda unos minutos. Sigue los *Logs*: al final debe aparecer
   `Listening at: http://0.0.0.0:...` y, antes, las migraciones y `Creado: Admin General`, etc.
5. Copia la URL del servicio (algo como `https://sabor-gastronomico-api.onrender.com`).
   Comprueba que `https://TU-SERVICIO.onrender.com/api/configuracion/` muestra un JSON
   (la primera vez puede tardar hasta un minuto).

> Si Render te exige tarjeta para los Blueprints, crea el servicio a mano: **New + → Web Service**, mismo
> repositorio, *Root Directory* `Back-end/gastronomia`, *Runtime* Python 3, *Instance Type* Free, y copia el
> *Build Command* y el *Start Command* de `render.yaml`; añade las mismas variables más `DJANGO_DEBUG=False`,
> `DJANGO_SECRET_KEY` (una clave larga aleatoria) y `PYTHON_VERSION=3.12.10`.

## Paso 4. Vercel (front-end)

1. En `Front-end/sabor_gastronomico/vercel.json` cambia `REEMPLAZA-CON-TU-SERVICIO.onrender.com` por el dominio
   de tu servicio de Render (sin `https://` en ese texto; deja el resto de la línea igual). Commit y push.
2. Entra a [vercel.com](https://vercel.com) → **Add New… → Project** → importa el repositorio.
3. **Root Directory**: `Front-end/sabor_gastronomico`. Framework: Vite (lo detecta solo).
4. **Environment Variables**: `VITE_GOOGLE_MAPS_API_KEY` = tu clave de Google Maps.
5. **Deploy**. Vercel te da una URL `https://algo.vercel.app`: ese es el enlace para tu CV.

## Paso 5. Tu usuario Admin General

1. En tu sitio de Vercel: **Registrarse** y crea tu cuenta (la primera petición puede tardar: el back-end despierta).
2. En Render → tu servicio → **Environment** → añade `ADMIN_GENERAL_USERNAME` = tu nombre de usuario → guarda
   (Render redespliega solo).
3. Cierra sesión y vuelve a entrar. Ya tienes el panel `/AdminGeneral`.

## Paso 6. Ajustes finales

- **Google Maps**: en Google Cloud Console → Credenciales → tu clave → restricción por sitios web:
  añade `https://tu-app.vercel.app/*`.
- **Mantener el back-end despierto** (opcional, recomendado para el CV): en [uptimerobot.com](https://uptimerobot.com)
  crea un monitor HTTP que visite `https://TU-SERVICIO.onrender.com/api/configuracion/` cada 5 minutos.
  Así casi nadie ve el arranque lento. Si aun así ocurre, el sitio muestra el aviso
  «Despertando el servidor…».
- **Datos de ejemplo**: entra como Admin General / dueño y crea algunos restaurantes y platillos con buenas fotos;
  un reclutador verá una base vacía si no lo haces.

## Checklist de pruebas en producción

- [ ] La portada carga y se ven restaurantes.
- [ ] Recargar `/Restaurantes` o `/Login` no da 404.
- [ ] Registrar un cliente, iniciar sesión, y la sesión sigue al recargar.
- [ ] Como cliente: agregar un platillo al carrito y hacer un pedido.
- [ ] Registrar un restaurante; como Admin General, cambiar su estado a *activo*.
- [ ] Como dueño: ver el pedido y cambiar su estado.
- [ ] Como Admin General: mensajes de contacto, blog y configuración.

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| Todo da error de red | `vercel.json` aún tiene `REEMPLAZA-CON-TU-SERVICIO` o el dominio está mal |
| `DisallowedHost` en los logs de Render | El servicio no se llama como en la URL usada o falta `RENDER_EXTERNAL_HOSTNAME` (Render la define sola) |
| `Falta la variable de entorno DJANGO_SECRET_KEY` | No se cargó en Render (Paso 3) |
| `could not connect to server` / `SSL` | `DATABASE_URL` mal copiada; debe terminar en `?sslmode=require` |
| El login funciona y al recargar se pierde | Estás entrando por el dominio de Render en vez del de Vercel |
| Primera carga muy lenta | Es el plan gratuito de Render despertando (ver UptimeRobot) |
| Sitio sin estilos en `/admin` de Django | Revisa en el build de Render que `collectstatic` terminó bien |

## Desarrollo local

```bash
cd Back-end/gastronomia
pip install -r requirements-dev.txt
cp .env.example .env          # completa los valores (MySQL local)
python manage.py migrate
python manage.py crear_grupos
python manage.py runserver

cd Front-end/sabor_gastronomico
npm install
npm run dev                   # http://localhost:5173 o http://127.0.0.1:5173
```
