from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from .models import *
from django.db.models import Avg
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from .permissions import es_admin_general


def _solicitante_es_admin_general(serializador):
    """True si la petición asociada al serializador viene de un Admin General."""
    solicitud = serializador.context.get('request')
    return solicitud is not None and es_admin_general(solicitud.user)


def calcular_precio_final(platillo):
    """Precio vigente de un platillo (con su promoción, si la tiene), a 2 decimales."""
    precio = platillo.precio
    if platillo.promocion and platillo.porcentaje:
        precio = precio - (precio * platillo.porcentaje / 100)
    return Decimal(precio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all()
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'foto_perfil',
            'groups',
            'password',
            'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False}
        }

    def validate_email(self, value):
        existentes = PerfilUsuario.objects.filter(email__iexact=value)
        if self.instance is not None:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value

    def validate_password(self, value):
        # Aplica los validadores de AUTH_PASSWORD_VALIDATORS (largo mínimo, contraseñas comunes, etc.)
        validate_password(value)
        return value

    def create(self, validated_data):
        groups_data = validated_data.pop('groups', [])
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_active'] = True 
        user = PerfilUsuario.objects.create(**validated_data)
        user.groups.set(groups_data)
        return user

    def update(self, instance, validated_data):
        groups_data = validated_data.pop('groups', None)
        password = validated_data.pop('password', None)

        # Un usuario no puede cambiarse a sí mismo el rol ni reactivarse: solo el Admin General.
        if not _solicitante_es_admin_general(self):
            groups_data = None
            validated_data.pop('is_active', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.password = make_password(password)
        if groups_data is not None:
            instance.groups.set(groups_data)

        instance.save()
        return instance

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del grupo no puede estar vacío.")
        return value.title()


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

    def validate_nombre_categoria(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la categoría no puede estar vacío.")
        return value.title()


class RestauranteSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    calificacion_promedio = serializers.SerializerMethodField()

    class Meta:
        model = Restaurante
        fields = '__all__'

    def get_calificacion_promedio(self, obj):
        promedio = Resena.objects.filter(restaurante=obj.id).aggregate(
            Avg('calificacion')
        )['calificacion__avg']

        return round(promedio or 0, 1)

    def validate_nombre_restaurante(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del restaurante no puede estar vacío.")
        return value.title()

    def update(self, instance, validated_data):
        # El dueño no puede aprobarse, cambiar su estado ni traspasar el restaurante.
        if not _solicitante_es_admin_general(self):
            for campo in ('estado', 'verificado', 'usuario_propietario', 'total_resenas'):
                validated_data.pop(campo, None)
        return super().update(instance, validated_data)

class HorarioRestauranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioRestaurante
        fields = ['id', 'restaurante', 'horario']

class CategoriaRestauranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaRestaurante
        fields = '__all__'
    

class FotoRestauranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoRestaurante
        fields = '__all__'
    
    # ✅ CloudinaryField maneja la validación automáticamente
    # No necesita validación adicional de URL


class CategoriaMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMenu
        fields = '__all__'

    def validate_nombre_categoria(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la categoría del menú no puede estar vacío.")
        return value.title()


class PlatilloSerializer(serializers.ModelSerializer):
    precio_descuento = serializers.SerializerMethodField()
    categoria_nombre = serializers.CharField(source='categoria_menu.nombre', read_only=True)
    """ categoria_nombre = serializers.CharField(source='categoria_menu.nombre_categoria', read_only=True) by gemini"""

    class Meta:
        model = Platillo
        fields = '__all__' 

    def get_precio_descuento(self, obj):
        """Calcula el precio final con promoción."""
        return calcular_precio_final(obj)

    def validate(self, data):
        """Evita activar promoción sin porcentaje."""
        if data.get("promocion") and not data.get("porcentaje"):
            raise serializers.ValidationError("Debe indicar un porcentaje para aplicar una promoción.")
        return data


class DetallePedidoSerializer(serializers.ModelSerializer):
    platillo_nombre = serializers.CharField(source='platillo.nombre', read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['id', 'platillo', 'platillo_nombre', 'cantidad', 'precio_unitario', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    restaurante_nombre = serializers.CharField(source='restaurante.nombre_restaurante', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'usuario_nombre', 'restaurante', 'restaurante_nombre', 'subtotal', 'total', 'metodo_pago', 'estado_pedido', 'detalles', 'fecha_pedido']


class PedidoEstadoSerializer(PedidoSerializer):
    """Edición de un pedido existente: solo se puede cambiar el estado."""

    class Meta(PedidoSerializer.Meta):
        read_only_fields = [
            campo for campo in PedidoSerializer.Meta.fields if campo != 'estado_pedido'
        ]


class CrearDetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = ['platillo', 'cantidad', 'precio_unitario']
        # El precio lo fija el servidor a partir del platillo; el cliente no lo decide.
        read_only_fields = ['precio_unitario']
        extra_kwargs = {'cantidad': {'required': True, 'min_value': 1, 'max_value': 100}}


class CrearPedidoSerializer(serializers.ModelSerializer):
    items = CrearDetallePedidoSerializer(many=True, write_only=True, allow_empty=False)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    restaurante_nombre = serializers.CharField(source='restaurante.nombre_restaurante', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'usuario_nombre', 'restaurante', 'restaurante_nombre',
                  'subtotal', 'total', 'metodo_pago', 'estado_pedido', 'items', 'fecha_pedido']
        # subtotal y total se calculan en el servidor; lo que envíe el cliente se ignora.
        read_only_fields = ['id', 'estado_pedido', 'fecha_pedido', 'usuario', 'subtotal', 'total']

    def validate(self, attrs):
        restaurante = attrs['restaurante']
        for item in attrs['items']:
            platillo = item['platillo']
            if platillo.restaurante_id != restaurante.id:
                raise serializers.ValidationError(
                    {'items': f"El platillo '{platillo.nombre_platillo}' no pertenece a este restaurante."}
                )
            if not platillo.disponible:
                raise serializers.ValidationError(
                    {'items': f"El platillo '{platillo.nombre_platillo}' no está disponible."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['usuario'] = self.context['request'].user
        validated_data['estado_pedido'] = 'pendiente'

        detalles = []
        subtotal_pedido = Decimal('0.00')
        for item in items_data:
            precio = calcular_precio_final(item['platillo'])
            subtotal_item = precio * item['cantidad']
            subtotal_pedido += subtotal_item
            detalles.append(DetallePedido(
                platillo=item['platillo'],
                cantidad=item['cantidad'],
                precio_unitario=precio,
                subtotal=subtotal_item,
            ))

        pedido = Pedido.objects.create(
            subtotal=subtotal_pedido,
            total=subtotal_pedido,
            **validated_data,
        )
        for detalle in detalles:
            detalle.pedido = pedido
        DetallePedido.objects.bulk_create(detalles)

        return pedido


class FotosResenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotosResena
        fields = '__all__'

class ResenaSerializer(serializers.ModelSerializer):
    fotos = FotosResenaSerializer(many=True, read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Resena
        fields = ['id', 'usuario', 'usuario_nombre', 'restaurante', 'calificacion', 'comentario', 'fecha_resena', 'fotos']
        read_only_fields = ['usuario']  # lo asigna la vista con el usuario autenticado
    
    # ✅ CloudinaryField maneja la validación automáticamente

class TestimonioSerializer(serializers.ModelSerializer):
    restaurante_nombre = serializers.CharField(source='restaurante.nombre_restaurante', read_only=True)

    class Meta:
        model = Testimonio
        fields = '__all__'

    def validate_comentario(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("El comentario debe tener al menos 5 caracteres.")
        return value.strip()

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("Debe incluir un nombre.")
        return value.title()    


class CategoriaBlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaBlog
        fields = '__all__'

    def validate_nombre_categoria(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la categoría no puede estar vacío.")
        return value.title()


class ArticuloBlogSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria_blog.nombre_categoria', read_only=True)
    
    class Meta:
        model = ArticuloBlog
        fields = [
            'id', 'categoria_blog', 'categoria_nombre', 'titulo', 'contenido', 
            'resumen', 'imagen_portada', 'fecha_publicacion', 'vistas', 'estado', 'destacado'
        ]

    def validate_titulo(self, value):
        if not value.strip():
            raise serializers.ValidationError("El título no puede estar vacío.")
        return value.title()


class EtiquetaArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtiquetaArticulo
        fields = '__all__'

    def validate_nombre_etiqueta(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la etiqueta no puede estar vacío.")
        return value.lower()


class ArticuloEtiquetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticuloEtiqueta
        fields = '__all__'

    def validate(self, data):
        if data['articulo'] is None or data['etiqueta'] is None:
            raise serializers.ValidationError("El artículo y la etiqueta son obligatorios.")
        return data


class GaleriaComunitariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GaleriaComunitaria
        fields = '__all__'
        read_only_fields = ['usuario']  # lo asigna la vista con el usuario autenticado

    def validate_titulo(self, value):
        if not value.strip():
            raise serializers.ValidationError("El título de la foto no puede estar vacío.")
        return value.title()


class ComentariosGaleriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComentariosGaleria
        fields = '__all__'
        read_only_fields = ['usuario']  # lo asigna la vista con el usuario autenticado

    def validate_comentario(self, value):
        if not value.strip():
            raise serializers.ValidationError("El comentario no puede estar vacío.")
        return value.strip()


class LugaresTuristicosSerializer(serializers.ModelSerializer):
    class Meta:
        model = LugaresTuristicos
        fields = '__all__'

    def validate_nombre_lugar(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del lugar no puede estar vacío.")
        return value.title()

    def validate_latitud(self, value):
        # Si viene vacío desde React ("") lo convertimos en None
        if value in ["", None]:
            return None

        try:
            value = Decimal(str(value).strip())
            value = value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        except:
            raise serializers.ValidationError("La latitud debe ser un número válido.")

        return value

    def validate_longitud(self, value):
        # Si viene vacío desde React ("") lo convertimos en None
        if value in ["", None]:
            return None

        try:
            value = Decimal(str(value).strip())
            value = value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        except:
            raise serializers.ValidationError("La longitud debe ser un número válido.")

        return value
    
class FotosLugaresSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotosLugares
        fields = '__all__'
    
    # ✅ CloudinaryField maneja la validación automáticamente


class MensajesContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensajesContacto
        fields = '__all__'  # Ya incluye 'archivado' automáticamente

    def validate_correo(self, value):
        if not value or '@' not in value:
            raise serializers.ValidationError("Debe proporcionar un correo válido.")
        return value

    def validate_mensaje(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("El mensaje debe tener al menos 10 caracteres.")
        return value.strip()
    

class RedSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedSocial
        fields = '__all__'

    def validate_nombre_red(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la red social no puede estar vacío.")
        return value

    def validate_link(self, value):
        if not value.startswith("http"):
            raise serializers.ValidationError("Debe proporcionar un enlace válido (que comience con http o https).")
        return value


class RestauranteRedSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestauranteRedSocial
        fields = '__all__'

    def validate(self, data):
        restaurante = data.get('restaurante')
        red_social = data.get('red_social')

        if RestauranteRedSocial.objects.filter(restaurante=restaurante, red_social=red_social).exists():
            raise serializers.ValidationError("Esta red social ya está asociada a este restaurante.")
        return data
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Obtener el grupo del usuario (rol)
        groups = self.user.groups.values_list('name', flat=True)

        # Agregar información extra
        data['role'] = groups[0] if groups else None
        data['id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data
    
# Serializer Específico para el Registro de Dueños de Restaurante
class RestauranteRegistrationSerializer(serializers.Serializer):
    """
    Serializador combinado que maneja la creación de un PerfilUsuario
    (con rol 'Admin Restaurante') y la creación de la entidad Restaurante,
    todo en una sola transacción.
    """

    # CAMPOS DEL USUARIO (PerfilUsuario)

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    
    # CAMPOS DEL RESTAURANTE (Restaurante)
    # Nota: Los IDs de las FK se recibirán como ID, si aplica
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(),
        required=False, 
        allow_null=True
    )
    nombre_restaurante = serializers.CharField(max_length=255)
    direccion = serializers.CharField(max_length=255)
    telefono_restaurante = serializers.CharField(max_length=20, allow_blank=True, required=False) # Nombre diferente para evitar colisión
    email_restaurante = serializers.EmailField(required=False, allow_blank=True) # Nombre diferente para evitar colisión
    longitud = serializers.DecimalField(max_digits=10, decimal_places=8, required=False, allow_null=True)
    latitud = serializers.DecimalField(max_digits=10, decimal_places=8, required=False, allow_null=True)
    
    # Validaciones personalizadas
    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        #Validación de usuario único
        if PerfilUsuario.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Este nombre de usuario ya está registrado."})
        if PerfilUsuario.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Este email ya está registrado."})
        return data

    @transaction.atomic
    def create(self, validated_data):
        # Comprobar el rol antes de crear nada
        try:
            grupo_restaurante = Group.objects.get(name='Admin Restaurante')
        except Group.DoesNotExist:
            raise serializers.ValidationError({"error": "El grupo 'Admin Restaurante' no existe. Pídele al administrador general que lo cree."})

        #Sacar datos del usuario
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'telefono': validated_data.pop('telefono', None),
        }
        
        #Crear PerfilUsuario (dueño del restaurante)
        user = PerfilUsuario.objects.create_user(
            **user_data
        )
        
        #Asignar el rol 'Admin Restaurante'
        user.groups.add(grupo_restaurante)

        #Crear la entidad Restaurante
        restaurante = Restaurante.objects.create(
            usuario_propietario=user, # 👈 Asigna la FK al usuario recién creado
            categoria=validated_data.get('categoria'),
            nombre_restaurante=validated_data.get('nombre_restaurante'),
            direccion=validated_data.get('direccion'),
            telefono=validated_data.get('telefono_restaurante') or None, # Usar el campo de restaurante
            email=validated_data.get('email_restaurante') or None,     # None (no '') para no chocar con unique=True
            longitud=validated_data.get('longitud'),
            latitud=validated_data.get('latitud'),
        )
        
        #Devolver la instancia del Restaurante y el Usuario asociado
        #Devolver la instancia del Restaurante y el Usuario
        return {'user': user, 'restaurante': restaurante}
    
 # CONFIGURACIÓN
class SerializadorConfiguracionPlataforma(serializers.ModelSerializer):

    class Meta:
        model = ConfiguracionPlataforma
        fields = [
            'id',
            'nombre_plataforma',
            'logo',
            'correo_contacto',
            'telefono_contacto',
            'direccion_general',
            'horarios_atencion',
            'mision',
            'vision',
            'valores',
            'url_facebook',
            'url_instagram',
            'url_twitter',
            'url_tiktok',
            'url_youtube',
            'url_whatsapp',
            'fecha_creacion',
            'fecha_ultima_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_ultima_actualizacion']

    # ✔ Validación correcta con nombre estándar de DRF
    def validate_nombre_plataforma(self, valor):
        if not valor or not valor.strip():
            raise serializers.ValidationError("El nombre de la plataforma no puede estar vacío.")
        return valor.strip()

    # ✔ Validación de correo corregida
    def validate_correo_contacto(self, valor):
        if valor and '@' not in valor:
            raise serializers.ValidationError("Ingresa un correo válido.")
        return valor