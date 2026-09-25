import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import ArticuloBlog, CategoriaBlog, PerfilUsuario, Restaurante
from .factories import CategoriaMenuFactory, PerfilUsuarioFactory, RestauranteFactory

NO_AUTORIZADO = (401, 403)


def cliente_de(usuario):
    """APIClient autenticado (cookie JWT) como el usuario dado."""
    client = APIClient()
    refresh = RefreshToken.for_user(usuario)
    client.cookies.load({'access_token': str(refresh.access_token)})
    return client


@pytest.fixture
def restaurante_ajeno():
    """Restaurante de otro dueño distinto al de la fixture 'restaurante'."""
    return RestauranteFactory()


# ==================== USUARIOS ====================

@pytest.mark.permissions
@pytest.mark.django_db
class TestPerfiles:

    def test_anonimo_no_puede_listar_ni_crear_usuarios(self, client, grupo_admin_general):
        assert client.get('/api/perfiles').status_code in NO_AUTORIZADO
        data = {
            'username': 'intruso', 'email': 'intruso@test.com', 'password': 'TestPass123!',
            'groups': [grupo_admin_general.id],
        }
        assert client.post('/api/perfiles', data, format='json').status_code in NO_AUTORIZADO
        assert not PerfilUsuario.objects.filter(username='intruso').exists()

    def test_cliente_no_puede_crear_usuarios(self, authenticated_client, grupo_admin_general):
        data = {
            'username': 'intruso', 'email': 'intruso@test.com', 'password': 'TestPass123!',
            'groups': [grupo_admin_general.id],
        }
        response = authenticated_client.post('/api/perfiles', data, format='json')
        assert response.status_code == 403
        assert not PerfilUsuario.objects.filter(username='intruso').exists()

    def test_admin_general_puede_crear_usuarios(self, admin_general_client, grupo_cliente):
        data = {
            'username': 'nuevo_usuario', 'email': 'nuevo@test.com', 'password': 'TestPass123!',
            'groups': [grupo_cliente.id],
        }
        response = admin_general_client.post('/api/perfiles', data, format='json')
        assert response.status_code == 201
        assert PerfilUsuario.objects.filter(username='nuevo_usuario').exists()

    def test_cliente_no_puede_ver_perfil_ajeno(self, authenticated_client):
        otro = PerfilUsuarioFactory()
        assert authenticated_client.get(f'/api/perfiles/{otro.id}').status_code == 403

    def test_cliente_no_puede_ascenderse_a_admin_general(
        self, authenticated_client, usuario_cliente, grupo_admin_general
    ):
        response = authenticated_client.patch(
            f'/api/perfiles/{usuario_cliente.id}',
            {'groups': [grupo_admin_general.id]},
            format='json',
        )
        assert response.status_code == 200
        assert list(usuario_cliente.groups.values_list('name', flat=True)) == ['Cliente']

    def test_cliente_no_puede_borrar_su_usuario(self, authenticated_client, usuario_cliente):
        response = authenticated_client.delete(f'/api/perfiles/{usuario_cliente.id}')
        assert response.status_code == 403
        assert PerfilUsuario.objects.filter(id=usuario_cliente.id).exists()

    def test_grupos_solo_admin_general(self, client, authenticated_client, admin_general_client):
        assert client.get('/api/grupos').status_code in NO_AUTORIZADO
        assert authenticated_client.get('/api/grupos').status_code == 403
        assert admin_general_client.get('/api/grupos').status_code == 200


# ==================== RESTAURANTES Y MENÚ ====================

@pytest.mark.permissions
@pytest.mark.django_db
class TestRestaurantes:

    def test_lectura_publica(self, client, restaurante):
        assert client.get('/api/restaurantes/').status_code == 200
        assert client.get(f'/api/restaurantes/{restaurante.id}').status_code == 200

    def test_anonimo_no_puede_modificar_ni_borrar(self, client, restaurante):
        assert client.patch(
            f'/api/restaurantes/{restaurante.id}', {'descripcion': 'hack'}, format='json'
        ).status_code in NO_AUTORIZADO
        assert client.delete(f'/api/restaurantes/{restaurante.id}').status_code in NO_AUTORIZADO

    def test_dueno_puede_editar_su_restaurante(self, admin_rest_client, restaurante):
        response = admin_rest_client.patch(
            f'/api/restaurantes/{restaurante.id}', {'descripcion': 'Nueva descripción'}, format='json'
        )
        assert response.status_code == 200
        restaurante.refresh_from_db()
        assert restaurante.descripcion == 'Nueva descripción'

    def test_dueno_no_puede_editar_restaurante_ajeno(self, admin_rest_client, restaurante_ajeno):
        response = admin_rest_client.patch(
            f'/api/restaurantes/{restaurante_ajeno.id}', {'descripcion': 'hack'}, format='json'
        )
        assert response.status_code == 403

    def test_dueno_no_puede_cambiar_estado_ni_verificacion(self, admin_rest_client, restaurante):
        response = admin_rest_client.patch(
            f'/api/restaurantes/{restaurante.id}',
            {'estado': 'inactivo', 'verificado': False},
            format='json',
        )
        assert response.status_code == 200
        restaurante.refresh_from_db()
        assert restaurante.estado == 'activo'
        assert restaurante.verificado is True

    def test_dueno_no_puede_traspasar_el_restaurante(self, admin_rest_client, restaurante, usuario_cliente):
        admin_rest_client.patch(
            f'/api/restaurantes/{restaurante.id}',
            {'usuario_propietario': usuario_cliente.id},
            format='json',
        )
        restaurante.refresh_from_db()
        assert restaurante.usuario_propietario_id != usuario_cliente.id

    def test_dueno_no_puede_eliminar_su_restaurante(self, admin_rest_client, restaurante):
        assert admin_rest_client.delete(f'/api/restaurantes/{restaurante.id}').status_code == 403
        assert Restaurante.objects.filter(id=restaurante.id).exists()

    def test_admin_general_puede_editar_y_eliminar(self, admin_general_client, restaurante):
        response = admin_general_client.patch(
            f'/api/restaurantes/{restaurante.id}', {'estado': 'inactivo'}, format='json'
        )
        assert response.status_code == 200
        restaurante.refresh_from_db()
        assert restaurante.estado == 'inactivo'
        assert admin_general_client.delete(f'/api/restaurantes/{restaurante.id}').status_code == 204

    def test_crear_restaurante_solo_admin_general(self, admin_rest_client, usuario_admin_restaurante):
        data = {'usuario_propietario': usuario_admin_restaurante.id, 'nombre_restaurante': 'Nuevo', 'direccion': 'Calle 1'}
        assert admin_rest_client.post('/api/restaurantes/', data, format='json').status_code == 403


@pytest.mark.permissions
@pytest.mark.django_db
class TestPlatillos:

    def test_lectura_publica(self, client):
        assert client.get('/api/platillos/').status_code == 200

    def test_dueno_crea_platillo_en_su_restaurante(self, admin_rest_client, restaurante, categoria_menu):
        data = {
            'restaurante': restaurante.id, 'categoria_menu': categoria_menu.id,
            'nombre_platillo': 'Ceviche', 'precio': '3500.00',
        }
        assert admin_rest_client.post('/api/platillos/', data, format='json').status_code == 201

    def test_dueno_no_crea_platillo_en_restaurante_ajeno(self, admin_rest_client, restaurante_ajeno, categoria_menu):
        data = {
            'restaurante': restaurante_ajeno.id, 'categoria_menu': categoria_menu.id,
            'nombre_platillo': 'Ceviche', 'precio': '3500.00',
        }
        assert admin_rest_client.post('/api/platillos/', data, format='json').status_code == 403

    def test_anonimo_no_puede_crear_platillos(self, client, restaurante, categoria_menu):
        data = {
            'restaurante': restaurante.id, 'categoria_menu': categoria_menu.id,
            'nombre_platillo': 'Ceviche', 'precio': '3500.00',
        }
        assert client.post('/api/platillos/', data, format='json').status_code in NO_AUTORIZADO

    def test_categoria_menu_solo_admin_general_elimina(self, admin_rest_client, admin_general_client):
        categoria = CategoriaMenuFactory()
        assert admin_rest_client.delete(f'/api/categorias-menu/{categoria.id}/').status_code == 403
        assert admin_general_client.delete(f'/api/categorias-menu/{categoria.id}/').status_code == 204

    def test_categoria_menu_personal_puede_crear(self, admin_rest_client, authenticated_client):
        data = {'nombre_categoria': 'Postres'}
        assert authenticated_client.post('/api/categorias-menu/', data, format='json').status_code == 403
        assert admin_rest_client.post('/api/categorias-menu/', data, format='json').status_code == 201


# ==================== CONTENIDO GENERAL ====================

@pytest.mark.permissions
@pytest.mark.django_db
class TestContenidoGeneral:

    def test_configuracion_lectura_publica_escritura_admin_general(
        self, client, authenticated_client, admin_general_client
    ):
        assert client.get('/api/configuracion/').status_code == 200
        payload = {'nombre_plataforma': 'Nuevo nombre'}
        assert client.patch('/api/configuracion/', payload, format='json').status_code in NO_AUTORIZADO
        assert authenticated_client.patch('/api/configuracion/', payload, format='json').status_code == 403
        assert admin_general_client.patch('/api/configuracion/', payload, format='json').status_code == 200

    def test_mensajes_contacto_publico_para_enviar_privado_para_leer(
        self, client, authenticated_client, admin_general_client
    ):
        data = {
            'nombre': 'Visitante', 'correo': 'visitante@test.com', 'asunto': 'Consulta',
            'mensaje': 'Quisiera más información sobre la plataforma.',
            'leido': True, 'archivado': True,
        }
        response = client.post('/api/mensajes-contacto', data, format='json')
        assert response.status_code == 201
        assert response.data['leido'] is False
        assert response.data['archivado'] is False

        assert client.get('/api/mensajes-contacto').status_code in NO_AUTORIZADO
        assert authenticated_client.get('/api/mensajes-contacto').status_code == 403
        assert admin_general_client.get('/api/mensajes-contacto').status_code == 200

    def test_blog_solo_admin_general_escribe(self, client, authenticated_client, admin_general_client):
        assert client.get('/api/categorias-blog').status_code == 200
        data = {'nombre_categoria': 'Historia'}
        assert client.post('/api/categorias-blog', data, format='json').status_code in NO_AUTORIZADO
        assert authenticated_client.post('/api/categorias-blog', data, format='json').status_code == 403
        assert admin_general_client.post('/api/categorias-blog', data, format='json').status_code == 201

    def test_borradores_del_blog_solo_los_ve_el_admin_general(self, client, admin_general_client):
        categoria = CategoriaBlog.objects.create(nombre_categoria='Cultura')
        ArticuloBlog.objects.create(categoria_blog=categoria, titulo='Publicado', contenido='x', estado='publicado')
        ArticuloBlog.objects.create(categoria_blog=categoria, titulo='Borrador', contenido='x', estado='borrador')

        titulos_publicos = {a['titulo'] for a in client.get('/api/articulos-blog').data}
        titulos_admin = {a['titulo'] for a in admin_general_client.get('/api/articulos-blog').data}

        assert titulos_publicos == {'Publicado'}
        assert titulos_admin == {'Publicado', 'Borrador'}

    def test_turismo_solo_admin_general_escribe(self, client, admin_rest_client, admin_general_client):
        assert client.get('/api/lugares-turisticos').status_code == 200
        data = {'nombre_lugar': 'El Faro'}
        assert client.post('/api/lugares-turisticos', data, format='json').status_code in NO_AUTORIZADO
        assert admin_rest_client.post('/api/lugares-turisticos', data, format='json').status_code == 403
        assert admin_general_client.post('/api/lugares-turisticos', data, format='json').status_code == 201


# ==================== RESEÑAS ====================

@pytest.mark.permissions
@pytest.mark.django_db
class TestResenas:

    def test_resena_se_asigna_al_usuario_autenticado(self, authenticated_client, usuario_cliente, restaurante):
        otro = PerfilUsuarioFactory()
        data = {'restaurante': restaurante.id, 'calificacion': 5, 'comentario': 'Excelente', 'usuario': otro.id}
        response = authenticated_client.post('/api/resenas/', data, format='json')
        assert response.status_code == 201
        assert response.data['usuario'] == usuario_cliente.id

    def test_anonimo_no_puede_resenar(self, client, restaurante):
        data = {'restaurante': restaurante.id, 'calificacion': 5}
        assert client.post('/api/resenas/', data, format='json').status_code in NO_AUTORIZADO


# ==================== REGISTRO DE RESTAURANTE ====================

@pytest.mark.crud
@pytest.mark.django_db
class TestRegistroRestaurante:

    DATOS = {
        'username': 'dueno_nuevo', 'email': 'dueno@test.com', 'password': 'TestPass123!',
        'first_name': 'Ana', 'last_name': 'Mora',
        'nombre_restaurante': 'Marisquería Nueva', 'direccion': 'Paseo de los Turistas',
    }

    def test_registro_sin_telefono(self, client, grupo_admin_restaurante):
        response = client.post('/api/register-restaurante', self.DATOS, format='json')
        assert response.status_code == 201
        usuario = PerfilUsuario.objects.get(username='dueno_nuevo')
        assert usuario.groups.filter(name='Admin Restaurante').exists()

    def test_registro_sin_grupo_no_deja_usuario_huerfano(self, client):
        Group.objects.filter(name='Admin Restaurante').delete()
        response = client.post('/api/register-restaurante', self.DATOS, format='json')
        assert response.status_code == 400
        assert not PerfilUsuario.objects.filter(username='dueno_nuevo').exists()
        assert not Restaurante.objects.filter(nombre_restaurante='Marisquería Nueva').exists()

    def test_dos_registros_sin_email_de_restaurante(self, client, grupo_admin_restaurante):
        segundo = dict(self.DATOS, username='dueno_dos', email='dueno2@test.com', nombre_restaurante='Otra Marisquería')
        assert client.post('/api/register-restaurante', self.DATOS, format='json').status_code == 201
        assert client.post('/api/register-restaurante', segundo, format='json').status_code == 201
