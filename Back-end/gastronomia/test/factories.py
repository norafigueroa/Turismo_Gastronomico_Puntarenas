import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import Group
from api.models import (
    PerfilUsuario, Categoria, Restaurante, CategoriaMenu, Platillo,
    Pedido, DetallePedido, Resena, ArticuloBlog, CategoriaBlog,
    LugaresTuristicos, RedSocial, RestauranteRedSocial, Testimonio,
    MensajesContacto
)


# ==================== USUARIOS ====================

class PerfilUsuarioFactory(DjangoModelFactory):
    class Meta:
        model = PerfilUsuario

    username = factory.Sequence(lambda n: f"usuario{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


# ==================== CATEGORÍAS ====================

class CategoriaFactory(DjangoModelFactory):
    class Meta:
        model = Categoria

    nombre_categoria = factory.Sequence(lambda n: f"Categoría {n}")
    descripcion = factory.Faker('sentence')


class CategoriaBlogFactory(DjangoModelFactory):
    class Meta:
        model = CategoriaBlog

    nombre_categoria = factory.Sequence(lambda n: f"Blog Category {n}")
    descripcion = factory.Faker('sentence')


class CategoriaMenuFactory(DjangoModelFactory):
    class Meta:
        model = CategoriaMenu

    nombre_categoria = factory.Sequence(lambda n: f"Menu Category {n}")
    descripcion = factory.Faker('sentence')


# ==================== RESTAURANTES ====================

class RestauranteFactory(DjangoModelFactory):
    class Meta:
        model = Restaurante

    usuario_propietario = factory.SubFactory(PerfilUsuarioFactory)
    categoria = factory.SubFactory(CategoriaFactory)
    nombre_restaurante = factory.Sequence(lambda n: f"Restaurante {n}")
    descripcion = factory.Faker('sentence', nb_words=10)
    direccion = factory.Faker('address')
    telefono = factory.Sequence(lambda n: f"2661{n:04d}")  # max_length=15 en el modelo
    email = factory.Sequence(lambda n: f"restaurante{n}@test.com")  # unique en el modelo
    estado = 'activo'
    verificado = True
    calificacion_promedio = 4.5
    total_resenas = 0


# ==================== PLATILLOS ====================

class PlatilloFactory(DjangoModelFactory):
    class Meta:
        model = Platillo

    restaurante = factory.SubFactory(RestauranteFactory)
    categoria_menu = factory.SubFactory(CategoriaMenuFactory)
    nombre_platillo = factory.Sequence(lambda n: f"Platillo {n}")
    descripcion = factory.Faker('sentence', nb_words=8)
    precio = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    tiempo_preparacion = factory.Faker('random_int', min=10, max=60)
    disponible = True
    es_especial_dia = False
    promocion = False


# ==================== PEDIDOS ====================

class PedidoFactory(DjangoModelFactory):
    class Meta:
        model = Pedido

    usuario = factory.SubFactory(PerfilUsuarioFactory)
    restaurante = factory.SubFactory(RestauranteFactory)
    estado_pedido = 'pendiente'
    subtotal = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    total = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    metodo_pago = 'tarjeta'


class DetallePedidoFactory(DjangoModelFactory):
    class Meta:
        model = DetallePedido

    pedido = factory.SubFactory(PedidoFactory)
    platillo = factory.SubFactory(PlatilloFactory)
    cantidad = factory.Faker('random_int', min=1, max=5)
    precio_unitario = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    subtotal = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)


# ==================== RESEÑAS ====================

class ResenaFactory(DjangoModelFactory):
    class Meta:
        model = Resena

    usuario = factory.SubFactory(PerfilUsuarioFactory)
    restaurante = factory.SubFactory(RestauranteFactory)
    calificacion = factory.Faker('random_int', min=1, max=5)
    comentario = factory.Faker('sentence', nb_words=15)


# ==================== BLOG ====================

class ArticuloBlogFactory(DjangoModelFactory):
    class Meta:
        model = ArticuloBlog

    categoria_blog = factory.SubFactory(CategoriaBlogFactory)
    titulo = factory.Sequence(lambda n: f"Artículo Blog {n}")
    contenido = factory.Faker('paragraph', nb_sentences=5)
    resumen = factory.Faker('sentence', nb_words=15)
    vistas = factory.Faker('random_int', min=0, max=1000)
    estado = 'publicado'
    destacado = False


# ==================== LUGARES TURÍSTICOS ====================

class LugaresTuristicosFactory(DjangoModelFactory):
    class Meta:
        model = LugaresTuristicos

    nombre_lugar = factory.Sequence(lambda n: f"Lugar Turístico {n}")
    descripcion = factory.Faker('sentence', nb_words=15)
    latitud = factory.Faker('latitude')
    longitud = factory.Faker('longitude')


# ==================== REDES SOCIALES ====================

class RedSocialFactory(DjangoModelFactory):
    class Meta:
        model = RedSocial

    nombre_red = 'facebook'
    link = factory.Faker('url')


class RestauranteRedSocialFactory(DjangoModelFactory):
    class Meta:
        model = RestauranteRedSocial

    restaurante = factory.SubFactory(RestauranteFactory)
    red_social = factory.SubFactory(RedSocialFactory)


# ==================== TESTIMONIOS ====================

class TestimonioFactory(DjangoModelFactory):
    class Meta:
        model = Testimonio

    restaurante = factory.SubFactory(RestauranteFactory)
    nombre = factory.Faker('name')
    comentario = factory.Faker('paragraph', nb_sentences=3)
    calificacion = factory.Faker('random_int', min=1, max=5)


# ==================== MENSAJES CONTACTO ====================

class MensajesContactoFactory(DjangoModelFactory):
    class Meta:
        model = MensajesContacto

    nombre = factory.Faker('name')
    correo = factory.Faker('email')
    telefono = factory.Sequence(lambda n: f"2661{n:04d}")  # max_length=15 en el modelo
    asunto = factory.Faker('sentence')
    mensaje = factory.Faker('paragraph', nb_sentences=3)
    archivado = False
    leido = False