import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group

from api.permissions import GRUPO_ADMIN_GENERAL, GRUPO_ADMIN_RESTAURANTE

GRUPOS = [GRUPO_ADMIN_GENERAL, GRUPO_ADMIN_RESTAURANTE, 'Cliente']


class Command(BaseCommand):
    help = (
        "Crea los roles de la plataforma (Admin General, Admin Restaurante, Cliente). "
        "Es idempotente: se puede ejecutar en cada despliegue. "
        "Con --admin-general USUARIO (o la variable de entorno ADMIN_GENERAL_USERNAME) asigna además "
        "el rol de Admin General a un usuario existente."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-general',
            metavar='USUARIO',
            help="Nombre de un usuario existente al que dar el rol de Admin General.",
        )

    def handle(self, *args, **opciones):
        for nombre in GRUPOS:
            _, creado = Group.objects.get_or_create(name=nombre)
            self.stdout.write(f"{'Creado' if creado else 'Ya existía'}: {nombre}")

        username = opciones.get('admin_general')
        desde_entorno = False
        if not username:
            username = os.environ.get('ADMIN_GENERAL_USERNAME')
            desde_entorno = bool(username)

        if username:
            Usuario = get_user_model()
            try:
                usuario = Usuario.objects.get(username=username)
            except Usuario.DoesNotExist:
                mensaje = (
                    f"El usuario '{username}' no existe. Regístralo primero en la web "
                    f"(o con 'python manage.py createsuperuser') y vuelve a ejecutar el comando."
                )
                if desde_entorno:
                    # No debe tumbar el despliegue: el usuario puede registrarse después.
                    self.stdout.write(self.style.WARNING(mensaje))
                    return
                raise CommandError(mensaje)
            usuario.groups.add(Group.objects.get(name=GRUPO_ADMIN_GENERAL))
            self.stdout.write(self.style.SUCCESS(f"{username} ahora es Admin General."))
