import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import PerfilUsuario, Categoria, Restaurante, CategoriaMenu


# ==================== FIXTURES DE GROUPS ====================

@pytest.fixture
def grupo_cliente():
    """Crea o obtiene el grupo Cliente"""
    grupo, created = Group.objects.get_or_create(name='Cliente')
    return grupo


@pytest.fixture
def grupo_admin_restaurante():
    """Crea o obtiene el grupo Admin Restaurante"""
    grupo, created = Group.objects.get_or_create(name='Admin Restaurante')
    return grupo


@pytest.fixture
def grupo_admin_general():
    """Crea o obtiene el grupo Admin General"""
    grupo, created = Group.objects.get_or_create(name='Admin General')
    return grupo


# ==================== FIXTURES DE USUARIOS ====================

@pytest.fixture
def usuario_cliente(grupo_cliente):
    """Crea un usuario con rol Cliente"""
    usuario = PerfilUsuario.objects.create_user(
        username='cliente_test',
        email='cliente@test.com',
        password='TestPass123!',
        first_name='Juan',
        last_name='Pérez'
    )
    usuario.groups.add(grupo_cliente)
    return usuario


@pytest.fixture
def usuario_admin_restaurante(grupo_admin_restaurante):
    """Crea un usuario con rol Admin Restaurante"""
    usuario = PerfilUsuario.objects.create_user(
        username='admin_rest_test',
        email='admin_rest@test.com',
        password='TestPass123!',
        first_name='Carlos',
        last_name='López'
    )
    usuario.groups.add(grupo_admin_restaurante)
    return usuario


@pytest.fixture
def usuario_admin_general(grupo_admin_general):
    """Crea un usuario con rol Admin General"""
    usuario = PerfilUsuario.objects.create_user(
        username='admin_general_test',
        email='admin_general@test.com',
        password='TestPass123!',
        first_name='Ana',
        last_name='García'
    )
    usuario.groups.add(grupo_admin_general)
    return usuario


# ==================== FIXTURES DE CLIENTS ====================

@pytest.fixture
def client():
    """Client básico sin autenticación"""
    return APIClient()


@pytest.fixture
def authenticated_client(usuario_cliente):
    """Client autenticado como Cliente"""
    client = APIClient()
    refresh = RefreshToken.for_user(usuario_cliente)
    client.cookies.load({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    })
    return client


@pytest.fixture
def admin_rest_client(usuario_admin_restaurante):
    """Client autenticado como Admin Restaurante"""
    client = APIClient()
    refresh = RefreshToken.for_user(usuario_admin_restaurante)
    client.cookies.load({'access_token': str(refresh.access_token)})
    return client


@pytest.fixture
def admin_general_client(usuario_admin_general):
    """Client autenticado como Admin General"""
    client = APIClient()
    refresh = RefreshToken.for_user(usuario_admin_general)
    client.cookies.load({'access_token': str(refresh.access_token)})
    return client


# ==================== FIXTURES DE DATOS BÁSICOS ====================

@pytest.fixture
def categoria():
    """Crea una categoría de restaurante"""
    return Categoria.objects.create(
        nombre_categoria='Comida Costarricense',
        descripcion='Platos típicos de Costa Rica'
    )


@pytest.fixture
def restaurante(usuario_admin_restaurante, categoria):
    """Crea un restaurante"""
    return Restaurante.objects.create(
        usuario_propietario=usuario_admin_restaurante,
        categoria=categoria,
        nombre_restaurante='El Sabor Puntarenas',
        descripcion='El mejor restaurant de comida costarricense',
        direccion='Calle Central, Puntarenas',
        telefono='+506 2661 1234',
        email='elsabor@test.com',
        estado='activo',
        verificado=True
    )


@pytest.fixture
def categoria_menu():
    """Crea una categoría de menú"""
    return CategoriaMenu.objects.create(
        nombre_categoria='Platos Principales'
    )


# ==================== FIXTURES PARA LIMPIAR AFTER EACH TEST ====================

@pytest.fixture(autouse=True)
def reset_sequences():
    """Resetea las secuencias de ID después de cada test (para tests consistentes)"""
    yield
    # Aquí iría lógica de limpieza si fuera necesaria