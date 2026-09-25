from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import CustomTokenObtainPairSerializer, PerfilUsuarioSerializer

# ==================== LOGIN ====================
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Vista de login que:
    1. Verifica credenciales
    2. Devuelve id, username, email, rol
    3. Guarda tokens en cookies HttpOnly con duración correcta
    4. Retorna datos del usuario en la respuesta
    """
    nombre_usuario = request.data.get('username')
    contrasena = request.data.get('password')
    
    if not nombre_usuario or not contrasena:
        return Response(
            {'error': 'Usuario y contraseña son obligatorios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Autenticar usuario
    usuario = authenticate(username=nombre_usuario, password=contrasena)
    print(usuario)
    
    if usuario is not None:
        # Generar tokens
        refresh = RefreshToken.for_user(usuario)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Obtener grupos del usuario (rol)
        grupos = usuario.groups.values_list('name', flat=True)
        role = grupos[0] if grupos else 'Cliente'  # Por defecto 'Cliente'
        
        # Crear respuesta con la información del usuario
        respuesta = Response({
            'mensaje': 'Login exitoso',
            'user': {
                'id': usuario.id,
                'username': usuario.username,
                'email': usuario.email,
                'first_name': usuario.first_name,
                'last_name': usuario.last_name,
                'role': role,
            }
        }, status=status.HTTP_200_OK)
        
        # ✅ ACCESO: 60 minutos (3600 segundos)
        respuesta.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite='Lax',
            max_age=3600,  # 60 minutos = 3600 segundos
            path='/',
        )
        
        # ✅ REFRESH: 7 días (604800 segundos)
        respuesta.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite='Lax',
            max_age=604800,  # 7 días = 604800 segundos
            path='/',
        )
        
        print(f'✅ Login exitoso para usuario: {usuario.username} con rol: {role}')
        return respuesta
    
    else:
        print(f'❌ Intento fallido de login para usuario: {nombre_usuario}')
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# ==================== REFRESH TOKEN ====================
@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """
    Vista para renovar el access_token usando el refresh_token.
    Lee el refresh_token desde cookies y genera un nuevo access_token.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token no encontrado en cookies'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Validar y renovar el token
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)
        
        # Crear respuesta
        respuesta = Response({
            'mensaje': 'Token renovado exitosamente'
        }, status=status.HTTP_200_OK)
        
        # Actualizar el access_token en cookies
        respuesta.set_cookie(
            key='access_token',
            value=new_access_token,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite='Lax',
            max_age=3600,  # 60 minutos
            path='/',
        )
        
        print('✅ Token renovado exitosamente')
        return respuesta
    
    except TokenError as e:
        print(f'❌ Error al renovar token: {str(e)}')
        return Response(
            {'error': 'Refresh token inválido o expirado'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        print(f'❌ Error inesperado: {str(e)}')
        return Response(
            {'error': 'Error al renovar token'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== LOGOUT ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Vista de logout que:
    1. Valida que el usuario está autenticado
    2. Elimina las cookies de tokens
    3. Opcionalmente, agrega el token a una blacklist
    """
    try:
        # Obtener el refresh_token para agregarlo a blacklist (opcional)
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Agrega a blacklist (si está configurado)
            except Exception as e:
                print(f'⚠️ Aviso al hacer blacklist: {str(e)}')
        
        # Crear respuesta
        respuesta = Response(
            {'mensaje': 'Logout exitoso'},
            status=status.HTTP_200_OK
        )
        
        # Eliminar cookies
        respuesta.delete_cookie('access_token', path='/')
        respuesta.delete_cookie('refresh_token', path='/')
        
        print(f'✅ Logout exitoso para usuario: {request.user.username}')
        return respuesta
    
    except Exception as e:
        print(f'❌ Error en logout: {str(e)}')
        return Response(
            {'error': 'Error al cerrar sesión'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== REGISTRO CLIENTE ====================
@api_view(['POST'])
@permission_classes([AllowAny])
def register_cliente(request):
    """
    Registro de cliente que:
    1. Valida los datos
    2. Asigna automáticamente el grupo 'Cliente'
    3. Retorna datos del usuario creado
    """
    try:
        # El rol Cliente es el rol base sin permisos especiales: se crea si aún no existe.
        grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
        
        # Validar que username y email no existan
        username = request.data.get('username')
        email = request.data.get('email')
        
        if not username or not email:
            return Response(
                {'error': 'Username y email son obligatorios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data.copy()   # Aquí sí es mutable
        
        # ✅ CAPITALIZAR NOMBRE Y APELLIDO AQUÍ
        if 'first_name' in data and data['first_name']:
            data['first_name'] = data['first_name'].strip().lower()
            data['first_name'] = data['first_name'][0].upper() + data['first_name'][1:]
        
        if 'last_name' in data and data['last_name']:
            data['last_name'] = data['last_name'].strip().lower()
            data['last_name'] = data['last_name'][0].upper() + data['last_name'][1:]
        
        data['groups'] = [grupo_cliente.id]
        
        # Serializar y validar datos
        serializador = PerfilUsuarioSerializer(data=data)
        
        if serializador.is_valid():
            usuario = serializador.save()
            
            print(f'✅ Cliente registrado: {usuario.username}')
            
            return Response({
                'mensaje': 'Cliente registrado exitosamente',
                'user': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'role': 'Cliente'
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'errores': serializador.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Group.DoesNotExist:
        print('❌ Grupo Cliente no existe')
        return Response(
            {'error': 'Grupo Cliente no existe. Contacta al administrador.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as excepcion:
        # El detalle solo va al log del servidor; al cliente no se le exponen errores internos.
        print(f'❌ Error en registro: {str(excepcion)}')
        return Response(
            {'error': 'No se pudo completar el registro. Inténtalo de nuevo.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )