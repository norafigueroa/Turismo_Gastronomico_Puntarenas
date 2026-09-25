import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError

from api.models import PerfilUsuario


@pytest.mark.django_db
class TestCrearGrupos:

    def test_crea_los_tres_roles(self):
        call_command('crear_grupos')
        nombres = set(Group.objects.values_list('name', flat=True))
        assert {'Admin General', 'Admin Restaurante', 'Cliente'} <= nombres

    def test_es_idempotente(self):
        call_command('crear_grupos')
        call_command('crear_grupos')
        assert Group.objects.filter(name='Admin General').count() == 1

    def test_promueve_a_admin_general(self):
        usuario = PerfilUsuario.objects.create_user(username='jefa', password='TestPass123!')
        call_command('crear_grupos', admin_general='jefa')
        assert usuario.groups.filter(name='Admin General').exists()

    def test_usuario_inexistente_da_error_claro(self):
        with pytest.raises(CommandError):
            call_command('crear_grupos', admin_general='no_existe')

    def test_promueve_desde_variable_de_entorno(self, monkeypatch):
        usuario = PerfilUsuario.objects.create_user(username='jefa', password='TestPass123!')
        monkeypatch.setenv('ADMIN_GENERAL_USERNAME', 'jefa')
        call_command('crear_grupos')
        assert usuario.groups.filter(name='Admin General').exists()

    def test_variable_de_entorno_con_usuario_inexistente_no_falla(self, monkeypatch):
        monkeypatch.setenv('ADMIN_GENERAL_USERNAME', 'todavia_no_existe')
        call_command('crear_grupos')  # no debe lanzar excepción
