from django.urls import path
from .views import *
from .views_auth import login_view, logout_view, register_cliente, token_refresh_view


urlpatterns = [
    # Usuarios y perfiles
    path('perfiles', PerfilUsuarioListCreateView.as_view(), name="crear y listar perfiles de usuario"),
    path('perfiles/<int:pk>', PerfilUsuarioDetailView.as_view(), name="actualizar y eliminar perfil de usuario"),

    # Grupos
    path('grupos', GroupListCreateView.as_view(), name="crear y listar grupos"),
    path('grupos/<int:pk>', GroupDetailView.as_view(), name="actualizar y eliminar grupo"),

    # Categorías
    path('categorias/', CategoriaListCreateView.as_view(), name="crear y listar categorias"),
    path('categorias/<int:pk>', CategoriaDetailView.as_view(), name="actualizar y eliminar categoria"),

    # Restaurantes
    path('restaurantes/', RestauranteListCreateView.as_view(), name="crear y listar restaurantes"),
    path('restaurantes/<int:pk>', RestauranteDetailView.as_view(), name="actualizar y eliminar restaurante"),
    path('categorias-restaurante', CategoriaRestauranteListCreateView.as_view(), name="crear y listar categorias de restaurante"),
    path('categorias-restaurante/<int:pk>', CategoriaRestauranteDetailView.as_view(), name="actualizar y eliminar categoria de restaurante"),
    path('fotos-restaurante', FotoRestauranteListCreateView.as_view(), name="crear y listar fotos de restaurante"),
    path('fotos-restaurante/<int:pk>', FotoRestauranteDetailView.as_view(), name="actualizar y eliminar foto de restaurante"),

    # --- URLs HORARIOS ---
    # path('restaurantes/<int:restaurante_id>/horarios/', HorarioRestauranteListCreateView.as_view(), name='horarios-restaurante'),
    # path('horarios/<int:pk>/', HorarioRestauranteDetailView.as_view(), name='horario-detalle'),

    path('restaurantes/horarios/', HorarioListCreateView.as_view(), name='horarios-restaurante'),
    path('restaurantes/<int:restaurante_id>/horarios/', HorarioDetailView.as_view(), name='horario'),
    
    # Menú y platillos
    path('categorias-menu/', CategoriaMenuListCreateView.as_view(), name="crear y listar categorias de menú"),
    path('categorias-menu/<int:pk>/', CategoriaMenuDetailView.as_view(), name="actualizar y eliminar categoria de menú"),
    path('platillos/', PlatilloListCreateView.as_view(), name="crear y listar platillos"),
    path('platillos/<int:pk>/', PlatilloDetailView.as_view(), name="actualizar y eliminar platillo"),
    path('platillos/<int:pk>/promocion/', ActualizarPromocionPlatillo.as_view()),


    # Pedidos
    path('pedidos/', PedidoListCreateView.as_view(), name="crear y listar pedidos"),
    path('pedidos/<int:pk>', PedidoDetailView.as_view(), name="actualizar y eliminar pedido"),
    path('pedidos/<int:pk>/', PedidoDetailView.as_view()),  # el front-end lo llama con "/" final
    path('pedidos/admin/', PedidoListAdminView.as_view(), name='pedidos-admin'),

    # Reseñas
    path('resenas/', ResenaListCreateView.as_view(), name='resenas'),
    path('resenas/<int:pk>', ResenaDetailView.as_view(), name="actualizar y eliminar reseña"),
    path('fotos-resenas', FotosResenaListCreateView.as_view(), name="crear y listar fotos de reseñas"),
    path('fotos-resenas/<int:pk>', FotosResenaDetailView.as_view(), name="actualizar y eliminar foto de reseña"),

    #Testimonio
    path('testimonios/', TestimonioListCreateView.as_view(), name='testimonios'),
    path('testimonios/<int:pk>/', TestimonioDetailView.as_view(), name='detalle-testimonio'),


    # Blog
    path('categorias-blog', CategoriaBlogListCreateView.as_view(), name="crear y listar categorias de blog"),
    path('categorias-blog/<int:pk>', CategoriaBlogDetailView.as_view(), name="actualizar y eliminar categoria de blog"),
    path('articulos-blog', ArticuloBlogListCreateView.as_view(), name="crear y listar articulos de blog"),
    path('articulos-blog/<int:pk>', ArticuloBlogDetailView.as_view(), name="actualizar y eliminar articulo de blog"),
    path('etiquetas-articulo', EtiquetaArticuloListCreateView.as_view(), name="crear y listar etiquetas de articulo"),
    path('etiquetas-articulo/<int:pk>', EtiquetaArticuloDetailView.as_view(), name="actualizar y eliminar etiqueta de articulo"),
    path('articulo-etiqueta', ArticuloEtiquetaListCreateView.as_view(), name="crear y listar articulos-etiquetas"),
    path('articulo-etiqueta/<int:pk>', ArticuloEtiquetaDetailView.as_view(), name="actualizar y eliminar articulo-etiqueta"),

    # Galería comunitaria
    path('galeria-comunitaria', GaleriaComunitariaListCreateView.as_view(), name="crear y listar fotos de galeria comunitaria"),
    path('galeria-comunitaria/<int:pk>', GaleriaComunitariaDetailView.as_view(), name="actualizar y eliminar foto de galeria comunitaria"),
    path('comentarios-galeria', ComentariosGaleriaListCreateView.as_view(), name="crear y listar comentarios de galeria"),
    path('comentarios-galeria/<int:pk>', ComentariosGaleriaDetailView.as_view(), name="actualizar y eliminar comentario de galeria"),

    # Lugares turísticos
    path('lugares-turisticos', LugaresTuristicosListCreateView.as_view(), name="crear y listar lugares turísticos"),
    path('lugares-turisticos/<int:pk>', LugaresTuristicosDetailView.as_view(), name="actualizar y eliminar lugar turístico"),
    path('fotos-lugares', FotosLugaresListCreateView.as_view(), name="crear y listar fotos de lugares"),
    path('fotos-lugares/<int:pk>', FotosLugaresDetailView.as_view(), name="actualizar y eliminar foto de lugar"),

    # Mensajes de contacto
    path('mensajes-contacto', MensajesContactoListCreateView.as_view(), name="crear y listar mensajes de contacto"),
    path('mensajes-contacto/<int:pk>', MensajesContactoDetailView.as_view(), name="actualizar y eliminar mensaje de contacto"),

    # Redes Sociales
    path('redes-sociales', RedSocialListCreateView.as_view(), name="crear y listar redes sociales"),
    path('redes-sociales/<int:pk>', RedSocialDetailView.as_view(), name="actualizar y eliminar red social"),

    # Relación Restaurante - Red Social
    path('restaurantes-redes', RestauranteRedSocialListCreateView.as_view(), name="crear y listar asociaciones restaurante-red"),
    path('restaurantes-redes/<int:pk>', RestauranteRedSocialDetailView.as_view(), name="actualizar y eliminar asociación restaurante-red"),

    # Nuevo Endpoint de Registro Combinado
    path('register-restaurante', RestauranteRegistrationView.as_view(), name="registro_restaurante_propietario"),

    # Autenticación
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', token_refresh_view, name='token_refresh'),
    path('register-cliente/', register_cliente, name='register_cliente'),

    #Configuración
    path('configuracion/', VistaConfiguracionPlataforma.as_view(), name="obtener y actualizar configuracion"),
]

  