from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView
from .models import *
from .serializers import *
from .permissions import (
    EsAdminGeneral,
    EsAdminGeneralOSoloLectura,
    EsPersonalOSoloLectura,
    EsPropietarioRestauranteOSoloLectura,
    EsAutorOAdminGeneralOSoloLectura,
    EsAdminGeneralOMismoUsuario,
    PermisoPedido,
    RestaurantePropioMixin,
    es_admin_general,
    es_propietario,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q

# Las vistas que no declaran permission_classes exigen sesión (ver settings.py).
# Convención: lectura pública / escritura por rol, salvo que se indique lo contrario.


# --- USUARIOS ---
class PerfilUsuarioListCreateView(ListCreateAPIView):
    """Listar y crear usuarios (con cualquier rol) es exclusivo del Admin General."""
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [EsAdminGeneral]

class PerfilUsuarioDetailView(RetrieveUpdateDestroyAPIView):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [EsAdminGeneralOMismoUsuario]

# --- GRUPOS ---
class GroupListCreateView(ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [EsAdminGeneral]

class GroupDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [EsAdminGeneral]

# --- CATEGORÍAS ---
class CategoriaListCreateView(ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class CategoriaDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- RESTAURANTES ---
class RestauranteListCreateView(ListCreateAPIView):
    """Crear restaurantes desde aquí es del Admin General; los dueños se registran en /register-restaurante."""
    queryset = Restaurante.objects.all()
    serializer_class = RestauranteSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class RestauranteDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Restaurante.objects.all()
    serializer_class = RestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]
    restaurante_lookup = 'self'
    propietario_puede_eliminar = False

# --- HORARIOS ---

class HorarioListCreateView(RestaurantePropioMixin, ListCreateAPIView):
    queryset = HorarioRestaurante.objects.all()
    serializer_class = HorarioRestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]


class HorarioDetailView(RestaurantePropioMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = HorarioRestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]
    lookup_field = 'restaurante_id'
    lookup_url_kwarg = 'restaurante_id'

    def get_queryset(self):
        restaurante_id = self.kwargs.get('restaurante_id')
        return HorarioRestaurante.objects.filter(restaurante_id=restaurante_id)


# --- CATEGORIA-RESTAURANTE ---
class CategoriaRestauranteListCreateView(RestaurantePropioMixin, ListCreateAPIView):
    queryset = CategoriaRestaurante.objects.all()
    serializer_class = CategoriaRestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

class CategoriaRestauranteDetailView(RestaurantePropioMixin, RetrieveUpdateDestroyAPIView):
    queryset = CategoriaRestaurante.objects.all()
    serializer_class = CategoriaRestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

# --- FOTOS RESTAURANTE ---
class FotoRestauranteListCreateView(RestaurantePropioMixin, ListCreateAPIView):
    queryset = FotoRestaurante.objects.all()
    serializer_class = FotoRestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

class FotoRestauranteDetailView(RestaurantePropioMixin, RetrieveUpdateDestroyAPIView):
    queryset = FotoRestaurante.objects.all()
    serializer_class = FotoRestauranteSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

# --- CATEGORIA MENÚ ---
class CategoriaMenuListCreateView(ListCreateAPIView):
    queryset = CategoriaMenu.objects.all()
    serializer_class = CategoriaMenuSerializer
    permission_classes = [EsPersonalOSoloLectura]

class CategoriaMenuDetailView(RetrieveUpdateDestroyAPIView):
    """
    Las categorías del menú son compartidas por todos los restaurantes y borrarlas
    elimina en cascada los platillos que las usan, así que solo el Admin General
    puede eliminarlas. Editarlas queda abierto al personal de restaurantes.
    """
    queryset = CategoriaMenu.objects.all()
    serializer_class = CategoriaMenuSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [EsAdminGeneral()]
        return [EsPersonalOSoloLectura()]

# --- PLATILLOS ---
class PlatilloListCreateView(RestaurantePropioMixin, ListCreateAPIView):
    queryset = Platillo.objects.all()
    serializer_class = PlatilloSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

    def get_queryset(self):
        queryset = super().get_queryset()
        restaurante_id = self.request.query_params.get("restaurante")

        if restaurante_id:
            queryset = queryset.filter(restaurante_id=restaurante_id)

        return queryset

class PlatilloDetailView(RestaurantePropioMixin, RetrieveUpdateDestroyAPIView):
    queryset = Platillo.objects.all()
    serializer_class = PlatilloSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

class ActualizarPromocionPlatillo(RestaurantePropioMixin, UpdateAPIView):
    queryset = Platillo.objects.all()
    serializer_class = PlatilloSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

# --- PEDIDOS ---
def _pedidos_visibles(usuario):
    """Pedidos que un usuario puede ver: los suyos y los de sus restaurantes (todos, si es Admin General)."""
    pedidos = Pedido.objects.select_related('usuario', 'restaurante')
    if not es_admin_general(usuario):
        pedidos = pedidos.filter(Q(usuario=usuario) | Q(restaurante__usuario_propietario=usuario))
    return pedidos.order_by('-fecha_pedido')


class PedidoListAdminView(ListAPIView):
    """
    Vista para que el admin de un restaurante vea solo los pedidos de sus restaurantes.
    """
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Pedido.objects
            .select_related('usuario', 'restaurante')
            .filter(restaurante__usuario_propietario=self.request.user)
            .order_by('-fecha_pedido')
        )

class PedidoListCreateView(ListCreateAPIView):
    """
    GET: pedidos del usuario (más los de sus restaurantes; todos si es Admin General).
    POST: crea un pedido. Los precios y totales los calcula el servidor.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CrearPedidoSerializer
        return PedidoSerializer

    def get_queryset(self):
        return _pedidos_visibles(self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()

class PedidoDetailView(RetrieveUpdateDestroyAPIView):
    """
    El cliente y el dueño del restaurante pueden ver el pedido; solo el dueño
    (o el Admin General) puede cambiar su estado o eliminarlo.
    """
    permission_classes = [PermisoPedido]

    def get_queryset(self):
        return _pedidos_visibles(self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return PedidoSerializer
        return PedidoEstadoSerializer

# --- RESEÑAS ---
class ResenaListCreateView(ListCreateAPIView):
    queryset = Resena.objects.all()
    serializer_class = ResenaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class ResenaDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Resena.objects.all()
    serializer_class = ResenaSerializer
    permission_classes = [EsAutorOAdminGeneralOSoloLectura]

# --- FOTOS RESEÑA ---
class ResenaPropiaMixin:
    """La foto solo se puede asociar a una reseña propia (o ser Admin General)."""

    def _verificar_resena(self, serializer):
        resena = serializer.validated_data.get('resena')
        if resena is not None and resena.usuario_id != self.request.user.id and not es_admin_general(self.request.user):
            raise PermissionDenied('Solo puedes agregar fotos a tus propias reseñas.')

    def perform_create(self, serializer):
        self._verificar_resena(serializer)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._verificar_resena(serializer)
        super().perform_update(serializer)


class FotosResenaListCreateView(ResenaPropiaMixin, ListCreateAPIView):
    queryset = FotosResena.objects.all()
    serializer_class = FotosResenaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class FotosResenaDetailView(ResenaPropiaMixin, RetrieveUpdateDestroyAPIView):
    queryset = FotosResena.objects.all()
    serializer_class = FotosResenaSerializer
    permission_classes = [EsAutorOAdminGeneralOSoloLectura]
    autor_lookup = 'resena.usuario'

# --- TESTIMONIOS ---
class TestimonioListCreateView(ListCreateAPIView):
    """Cualquier visitante puede dejar un testimonio (es anónimo, con nombre libre)."""
    queryset = Testimonio.objects.all()
    serializer_class = TestimonioSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        restaurante_id = self.request.query_params.get("restaurante")

        if restaurante_id:
            queryset = queryset.filter(restaurante_id=restaurante_id)

        return queryset

class TestimonioDetailView(RestaurantePropioMixin, RetrieveUpdateDestroyAPIView):
    queryset = Testimonio.objects.all()
    serializer_class = TestimonioSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

# --- CATEGORIA BLOG ---
class CategoriaBlogListCreateView(ListCreateAPIView):
    queryset = CategoriaBlog.objects.all()
    serializer_class = CategoriaBlogSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class CategoriaBlogDetailView(RetrieveUpdateDestroyAPIView):
    queryset = CategoriaBlog.objects.all()
    serializer_class = CategoriaBlogSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- ARTICULO BLOG ---
class ArticulosVisiblesMixin:
    """Los borradores e inactivos solo los ve el Admin General."""

    def get_queryset(self):
        queryset = ArticuloBlog.objects.all()
        if not es_admin_general(self.request.user):
            queryset = queryset.filter(estado='publicado')
        return queryset


class ArticuloBlogListCreateView(ArticulosVisiblesMixin, ListCreateAPIView):
    serializer_class = ArticuloBlogSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class ArticuloBlogDetailView(ArticulosVisiblesMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ArticuloBlogSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- ETIQUETA ARTICULO ---
class EtiquetaArticuloListCreateView(ListCreateAPIView):
    queryset = EtiquetaArticulo.objects.all()
    serializer_class = EtiquetaArticuloSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class EtiquetaArticuloDetailView(RetrieveUpdateDestroyAPIView):
    queryset = EtiquetaArticulo.objects.all()
    serializer_class = EtiquetaArticuloSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- ARTICULO ETIQUETA ---
class ArticuloEtiquetaListCreateView(ListCreateAPIView):
    queryset = ArticuloEtiqueta.objects.all()
    serializer_class = ArticuloEtiquetaSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class ArticuloEtiquetaDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ArticuloEtiqueta.objects.all()
    serializer_class = ArticuloEtiquetaSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- GALERÍA COMUNITARIA ---
class GaleriaComunitariaListCreateView(ListCreateAPIView):
    queryset = GaleriaComunitaria.objects.all()
    serializer_class = GaleriaComunitariaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class GaleriaComunitariaDetailView(RetrieveUpdateDestroyAPIView):
    queryset = GaleriaComunitaria.objects.all()
    serializer_class = GaleriaComunitariaSerializer
    permission_classes = [EsAutorOAdminGeneralOSoloLectura]

# --- COMENTARIOS GALERÍA ---
# 🔴 Lista de palabras ofensivas
PALABRAS_OFENSIVAS = [
    "idiota",
    "estupido",
    "estúpido",
    "tonto",
    "mierda",
    "puta",
    "pendejo",
    "imbecil",
    "imbécil",
]

class ComentariosGaleriaListCreateView(ListCreateAPIView):
    queryset = ComentariosGaleria.objects.all().order_by("-fecha_comentario")
    serializer_class = ComentariosGaleriaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        texto = self.request.data.get("comentario", "").lower()

        # 🔎 Validación de lenguaje ofensivo
        for palabra in PALABRAS_OFENSIVAS:
            if palabra in texto:
                raise ValidationError({
                    "comentario": "Tu comentario contiene lenguaje ofensivo y no puede publicarse"
                })

        # ✅ Guardar comentario si pasa la validación
        serializer.save(usuario=self.request.user)

class ComentariosGaleriaDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ComentariosGaleria.objects.all()
    serializer_class = ComentariosGaleriaSerializer
    permission_classes = [EsAutorOAdminGeneralOSoloLectura]

# --- LUGARES TURÍSTICOS ---
class LugaresTuristicosListCreateView(ListCreateAPIView):
    queryset = LugaresTuristicos.objects.all()
    serializer_class = LugaresTuristicosSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class LugaresTuristicosDetailView(RetrieveUpdateDestroyAPIView):
    queryset = LugaresTuristicos.objects.all()
    serializer_class = LugaresTuristicosSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- FOTOS LUGARES ---
class FotosLugaresListCreateView(ListCreateAPIView):
    queryset = FotosLugares.objects.all()
    serializer_class = FotosLugaresSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class FotosLugaresDetailView(RetrieveUpdateDestroyAPIView):
    queryset = FotosLugares.objects.all()
    serializer_class = FotosLugaresSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- MENSAJES CONTACTO ---
class MensajesContactoListCreateView(ListCreateAPIView):
    """Cualquier visitante puede enviar un mensaje; solo el Admin General los lee."""
    queryset = MensajesContacto.objects.filter(archivado=False)
    serializer_class = MensajesContactoSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [EsAdminGeneral()]

    def perform_create(self, serializer):
        # Un visitante no decide si su mensaje aparece como leído o archivado.
        serializer.save(leido=False, archivado=False)

class MensajesContactoDetailView(RetrieveUpdateDestroyAPIView):
    queryset = MensajesContacto.objects.all()
    serializer_class = MensajesContactoSerializer
    permission_classes = [EsAdminGeneral]

    def retrieve(self, request, *args, **kwargs):
        # Marcar como leído cuando se visualiza
        instance = self.get_object()
        instance.leido = True
        instance.save()
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # En lugar de eliminar, archivamos
        instance = self.get_object()
        instance.archivado = True
        instance.save()
        return Response({'mensaje': 'Mensaje archivado'}, status=status.HTTP_200_OK)

# --- REDES SOCIALES ---
class RedSocialListCreateView(ListCreateAPIView):
    queryset = RedSocial.objects.all()
    serializer_class = RedSocialSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

class RedSocialDetailView(RetrieveUpdateDestroyAPIView):
    queryset = RedSocial.objects.all()
    serializer_class = RedSocialSerializer
    permission_classes = [EsAdminGeneralOSoloLectura]

# --- RESTAURANTE-RED SOCIAL (Intermedia) ---
class RestauranteRedSocialListCreateView(RestaurantePropioMixin, ListCreateAPIView):
    queryset = RestauranteRedSocial.objects.all()
    serializer_class = RestauranteRedSocialSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

class RestauranteRedSocialDetailView(RestaurantePropioMixin, RetrieveUpdateDestroyAPIView):
    queryset = RestauranteRedSocial.objects.all()
    serializer_class = RestauranteRedSocialSerializer
    permission_classes = [EsPropietarioRestauranteOSoloLectura]

# --- REGISTRO COMBINADO RESTAURANTE ---
class RestauranteRegistrationView(CreateAPIView):
    """
    Vista para el registro combinado de un PerfilUsuario (Admin Restaurante)
    y su Restaurante asociado.
    """
    serializer_class = RestauranteRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # La función create del serializer devuelve un diccionario con 'user' y 'restaurante'
        data = serializer.save()
        user = data['user']
        restaurante = data['restaurante']

        # Preparamos una respuesta informativa para el frontend
        respuesta = {
            'mensaje': 'Registro de restaurante y propietario exitoso.',
            'restaurante': {
                'id': restaurante.id,
                'nombre': restaurante.nombre_restaurante,
                'direccion': restaurante.direccion,
            },
            'propietario': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': 'Admin Restaurante'
            }
        }
        return Response(respuesta, status=status.HTTP_201_CREATED)

# --- CONFIGURACION ---
class VistaConfiguracionPlataforma(RetrieveUpdateAPIView):
    """
    Vista para obtener y actualizar la configuración de la plataforma.
    GET: Cualquiera puede ver
    PUT/PATCH: Solo Admin General
    """
    serializer_class = SerializadorConfiguracionPlataforma
    permission_classes = [EsAdminGeneralOSoloLectura]

    def get_object(self):
        return ConfiguracionPlataforma.obtener_instancia()
