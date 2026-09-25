# Guía de despliegue: Vercel (front-end) + Railway (back-end y MySQL)

```
Navegador ──► Vercel (React)  ──/api/*──► Railway (Django + Gunicorn) ──► Railway MySQL
                  │                                   │
                  └── un solo dominio para el usuario └── imágenes: Cloudinary
```

El navegador solo habla con Vercel. Las peticiones a `/api/...` las reenvía Vercel al back-end
(regla en `Front-end/sabor_gastronomico/vercel.json`). Así las cookies de sesión son del mismo
dominio y ningún navegador las bloquea.

Orden: **Railway primero** (necesitas su URL para el `vercel.json`), después Vercel.

---

## 0. Antes de empezar

- [ ] Haz **commit y push** de todos los cambios a GitHub (Railway y Vercel despliegan desde el repositorio).
- [ ] **Rota los secretos que estuvieron en el código** (siguen en el historial de git):
  - Cloudinary: en Settings → API Keys genera un *API secret* nuevo.
  - Para producción usarás una `DJANGO_SECRET_KEY` nueva (paso 1.3) y una contraseña de MySQL nueva (Railway la genera sola).
- [ ] Cuentas en [railway.com](https://railway.com) y [vercel.com](https://vercel.com), ambas con GitHub.

## 1. Railway: base de datos y back-end

### 1.1 Crear el proyecto y MySQL
1. *New Project* → **Provision MySQL** (o *Database → MySQL*). Anota el nombre del servicio (normalmente `MySQL`).

### 1.2 Crear el servicio del back-end
1. En el mismo proyecto: *New → GitHub Repo* → elige `Turismo_Gastronomico_Puntarenas`.
2. En el servicio: *Settings → Source → **Root Directory*** = `Back-end/gastronomia`.
   (Railway leerá de ahí `requirements.txt`, `.python-version` y `railway.toml`.)
3. *Settings → Networking → **Generate Domain***. Te dará algo como `mi-api.up.railway.app`. **Cópialo.**

### 1.3 Variables del servicio del back-end (pestaña *Variables*)

| Variable | Valor |
|---|---|
| `DJANGO_SECRET_KEY` | una clave **nueva** (ver abajo) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` (el dominio de Railway se añade solo) |
| `MYSQLHOST` | `${{MySQL.MYSQLHOST}}` |
| `MYSQLPORT` | `${{MySQL.MYSQLPORT}}` |
| `MYSQLUSER` | `${{MySQL.MYSQLUSER}}` |
| `MYSQLPASSWORD` | `${{MySQL.MYSQLPASSWORD}}` |
| `MYSQLDATABASE` | `${{MySQL.MYSQLDATABASE}}` |
| `CLOUDINARY_CLOUD_NAME` | tu cloud name |
| `CLOUDINARY_API_KEY` | tu API key |
| `CLOUDINARY_API_SECRET` | el secret **nuevo** |

- Si tu servicio de base de datos no se llama `MySQL`, cambia ese nombre dentro de `${{...}}`.
- Generar la clave (en tu PC, con Node o Python):
  ```bash
  node -e "console.log(require('crypto').randomBytes(50).toString('base64url'))"
  ```
- **No** definas `DB_HOST`, `DB_USER`, etc.: tienen prioridad sobre `MYSQL*`.

### 1.4 Desplegar
Railway despliega al guardar las variables. En cada despliegue `railway.toml` ejecuta solo:
1. `python manage.py migrate` (crea las tablas),
2. `python manage.py crear_grupos` (crea los roles Admin General, Admin Restaurante y Cliente),
3. `collectstatic` y `gunicorn`.

Comprueba en *Deployments → Logs* que no haya errores, y abre `https://mi-api.up.railway.app/api/configuracion/`:
debe mostrar un JSON.

## 2. Vercel: front-end

1. **Antes**, edita `Front-end/sabor_gastronomico/vercel.json` y cambia
   `REEMPLAZA-CON-TU-DOMINIO.up.railway.app` por tu dominio de Railway (por ejemplo `mi-api.up.railway.app`).
   Deja intacto el resto de la línea (`https://` delante y `/api/:path*` detrás). Haz commit y push.
2. En Vercel: *Add New → Project* → importa el repositorio.
3. Configuración:
   - **Root Directory**: `Front-end/sabor_gastronomico`
   - Framework Preset: Vite (lo detecta solo). Build: `npm run build`, Output: `dist`.
   - **Environment Variables**: `VITE_GOOGLE_MAPS_API_KEY` = tu clave de Google Maps.
     (No hace falta `VITE_API_URL`: en producción usa `/api` por defecto.)
4. *Deploy*.

## 3. Crear tu usuario Admin General

1. Entra a tu sitio de Vercel → *Registrarse* y crea tu cuenta normal.
2. En Railway, servicio del back-end → *Variables* → añade `ADMIN_GENERAL_USERNAME` = tu nombre de usuario.
3. Redespliega (*Deployments → Redeploy*). El comando `crear_grupos` te asigna el rol de Admin General.
4. Cierra sesión y vuelve a entrar. Ya puedes usar el panel `/AdminGeneral`.

(Después puedes borrar esa variable.)

## 4. Ajustes finales

- **Google Maps**: en Google Cloud Console → Credenciales → tu clave → *Restricciones de sitios web*:
  añade `https://tu-app.vercel.app/*` (y tu dominio propio si lo tienes).
- **Cloudinary**: el front sube imágenes directo a Cloudinary con el preset `el_sabor_de_la_perla`
  (debe existir como preset *unsigned* en tu cuenta).
- **Dominio propio** (opcional): añádelo en Vercel; no hay que tocar Railway.

## 5. Checklist de pruebas en producción

- [ ] La portada carga y se ven los restaurantes.
- [ ] Recargar `/Restaurantes` o `/Login` no da 404.
- [ ] Registrar un cliente e iniciar sesión (revisa que la sesión sigue al recargar la página).
- [ ] Como cliente: agregar un platillo al carrito y hacer un pedido.
- [ ] Registrar un restaurante; como Admin General, cambiar su estado a *activo*.
- [ ] Como dueño del restaurante: ver el pedido y cambiar su estado.
- [ ] Como Admin General: ver mensajes de contacto, blog y configuración.

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| El sitio carga pero todo da error de red | `vercel.json` aún tiene `REEMPLAZA-CON-TU-DOMINIO` o el dominio está mal escrito |
| `DisallowedHost` en los logs de Railway | Falta generar el dominio público del servicio (paso 1.2) o `RAILWAY_PUBLIC_DOMAIN` no llegó |
| `Falta la variable de entorno DJANGO_SECRET_KEY` | No se cargaron las variables (paso 1.3) |
| El login funciona y al recargar se pierde | No estás entrando por el dominio de Vercel, sino por el de Railway |
| `Can't connect to MySQL` | Variables `MYSQL*` mal referenciadas (revisa el nombre del servicio en `${{...}}`) |
| 404 en rutas con `/` final, p. ej. `/api/login/` | Revisa que `vercel.json` conserva `/api/:path*` tal cual |
| Estáticos del `/admin` sin estilos | Revisa en los logs que `collectstatic` terminó bien |

## Migrar los datos de tu MySQL local (opcional)

Si ya tienes restaurantes, platillos o usuarios reales en tu MySQL local, expórtalos y cárgalos en Railway
(usa la URL pública `MYSQL_PUBLIC_URL` del servicio de MySQL desde tu PC):

```bash
mysqldump -u root -p gastronomia > respaldo.sql
mysql -h <host-publico> -P <puerto> -u root -p railway < respaldo.sql
```

Hazlo **después** del primer despliegue (que crea las tablas) o antes, pero no ambos: si importas
tablas ya existentes se producirán conflictos.

## Desarrollo local (sin cambios)

```bash
cd Back-end/gastronomia
pip install -r requirements-dev.txt
cp .env.example .env        # completa los valores
python manage.py migrate
python manage.py crear_grupos
python manage.py runserver

cd Front-end/sabor_gastronomico
npm install
npm run dev                 # abre http://localhost:5173 o http://127.0.0.1:5173
```
