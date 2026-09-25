"""
Permisos por rol de la API.

Roles (grupos de Django): 'Admin General', 'Admin Restaurante' y 'Cliente'.
Por defecto la API exige sesión (ver DEFAULT_PERMISSION_CLASSES en settings.py);
las vistas públicas lo declaran de forma explícita con estas clases o con AllowAny.
"""
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission

GRUPO_ADMIN_GENERAL = 'Admin General'
GRUPO_ADMIN_RESTAURANTE = 'Admin Restaurante'


# ==================== HELPERS ====================

def _autenticado(usuario):
    return bool(usuario and usuario.is_authenticated)


def es_admin_general(usuario):
    if not _autenticado(usuario):
        return False
    return usuario.is_superuser or usuario.groups.filter(name=GRUPO_ADMIN_GENERAL).exists()


def es_admin_restaurante(usuario):
    if not _autenticado(usuario):
        return False
    return usuario.groups.filter(name=GRUPO_ADMIN_RESTAURANTE).exists()


def es_propietario(usuario, restaurante):
    return _autenticado(usuario) and restaurante.usuario_propietario_id == usuario.id


def puede_gestionar_restaurante(usuario, restaurante):
    return es_admin_general(usuario) or es_propietario(usuario, restaurante)


def _resolver(objeto, ruta):
    """Recorre una ruta con puntos ('resena.usuario') y devuelve el valor final o None."""
    for parte in ruta.split('.'):
        if objeto is None:
            return None
        objeto = getattr(objeto, parte, None)
    return objeto


# ==================== CLASES DE PERMISO ====================

class EsAdminGeneral(BasePermission):
    """Solo el Admin General (lectura y escritura)."""

    def has_permission(self, request, view):
        return es_admin_general(request.user)


class EsAdminGeneralOSoloLectura(BasePermission):
    """Lectura pública; escritura solo para el Admin General."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or es_admin_general(request.user)


class EsPersonalOSoloLectura(BasePermission):
    """Lectura pública; escritura para Admin General o Admin Restaurante."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return es_admin_general(request.user) or es_admin_restaurante(request.user)


class EsPropietarioRestauranteOSoloLectura(BasePermission):
    """
    Lectura pública; escritura para el Admin General o el dueño del restaurante
    al que pertenece el objeto.

    La vista puede definir:
      - restaurante_lookup: ruta hasta el restaurante ('restaurante' por defecto,
        'self' cuando el objeto es el propio Restaurante).
      - propietario_puede_eliminar: False para que solo el Admin General borre.

    Al crear, la vista debe usar RestaurantePropioMixin para comprobar que el
    restaurante enviado en el cuerpo pertenece a quien lo envía.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or _autenticado(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if es_admin_general(request.user):
            return True
        if request.method == 'DELETE' and not getattr(view, 'propietario_puede_eliminar', True):
            return False

        ruta = getattr(view, 'restaurante_lookup', 'restaurante')
        restaurante = obj if ruta == 'self' else _resolver(obj, ruta)
        return restaurante is not None and es_propietario(request.user, restaurante)


class EsAutorOAdminGeneralOSoloLectura(BasePermission):
    """
    Lectura pública; escritura para el autor del objeto o el Admin General.
    La vista puede definir autor_lookup (por defecto 'usuario').
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or _autenticado(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if es_admin_general(request.user):
            return True
        autor = _resolver(obj, getattr(view, 'autor_lookup', 'usuario'))
        return autor is not None and autor.pk == request.user.pk


class EsAdminGeneralOMismoUsuario(BasePermission):
    """Perfil de usuario: el Admin General gestiona todos; cada usuario solo el suyo (sin borrarlo)."""

    def has_permission(self, request, view):
        return _autenticado(request.user)

    def has_object_permission(self, request, view, obj):
        if es_admin_general(request.user):
            return True
        if request.method == 'DELETE':
            return False
        return obj.pk == request.user.pk


class PermisoPedido(BasePermission):
    """
    Pedidos: el cliente y el dueño del restaurante pueden verlo; solo el dueño del
    restaurante (o el Admin General) puede cambiar su estado o eliminarlo.
    """

    def has_permission(self, request, view):
        return _autenticado(request.user)

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if es_admin_general(usuario):
            return True
        es_dueno = es_propietario(usuario, obj.restaurante)
        if request.method in SAFE_METHODS:
            return es_dueno or obj.usuario_id == usuario.id
        return es_dueno


# ==================== MIXINS ====================

class RestaurantePropioMixin:
    """
    Al crear o modificar, el 'restaurante' enviado debe ser del usuario
    (o el usuario debe ser Admin General). Evita crear o mover registros
    dentro de restaurantes ajenos.
    """

    def _verificar_restaurante(self, serializer):
        restaurante = serializer.validated_data.get('restaurante')
        if restaurante is not None and not puede_gestionar_restaurante(self.request.user, restaurante):
            raise PermissionDenied('No tienes permiso para gestionar este restaurante.')

    def perform_create(self, serializer):
        self._verificar_restaurante(serializer)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._verificar_restaurante(serializer)
        super().perform_update(serializer)
