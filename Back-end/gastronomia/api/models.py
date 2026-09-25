from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings 
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator, MaxValueValidator


# USUARIOS
class PerfilUsuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)
    foto_perfil = CloudinaryField('foto_perfil', blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.username}"


# CATEGORÍAS
class Categoria(models.Model):
    nombre_categoria = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    icono = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre_categoria


# RESTAURANTES
class Restaurante(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('pendiente', 'Pendiente'),
        ('inactivo', 'Inactivo'),
    ]

    usuario_propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_restaurante = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    historia_negocio = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.CharField(max_length=255)
    longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    horario_apertura = models.TimeField(blank=True, null=True)
    horario_cierre = models.TimeField(blank=True, null=True)
    dias_operacion = models.CharField(max_length=100, blank=True, null=True)
    logo = CloudinaryField('logo', blank=True, null=True)
    foto_portada = models.URLField(max_length=255, blank=True, null=True)
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_resenas = models.IntegerField(default=0)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    verificado = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_restaurante

class HorarioRestaurante(models.Model):
    restaurante = models.ForeignKey(
        Restaurante,
        related_name='horarios',
        on_delete=models.CASCADE
    )

    horario = models.JSONField(default=dict)

    def __str__(self):
        return f"Horario de {self.restaurante.nombre_restaurante}"        

# REDES SOCIALES
class RedSocial(models.Model):
    REDES_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter / X'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('whatsapp', 'WhatsApp'),
        ('otra', 'Otra'),
    ]

    nombre_red = models.CharField(max_length=30, choices=REDES_CHOICES)
    link = models.URLField(max_length=255)
    icono = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.get_nombre_red_display()



# RELACIÓN RESTAURANTE - RED SOCIAL
class RestauranteRedSocial(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='redes')
    red_social = models.ForeignKey(RedSocial, on_delete=models.CASCADE, related_name='restaurantes')

    class Meta:
        unique_together = ('restaurante', 'red_social')

    def __str__(self):
        return f"{self.restaurante.nombre_restaurante} - {self.red_social}"


# CATEGORÍAS RESTAURANTE
class CategoriaRestaurante(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='categoria_restaurante')
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='categoria_restaurante')

    class Meta:
        unique_together = ('categoria', 'restaurante')

    def __str__(self):
        return f"{self.categoria.nombre_categoria} - {self.restaurante.nombre_restaurante}"


# FOTOS RESTAURANTE
class FotoRestaurante(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='fotos')
    url_foto = CloudinaryField('foto_restaurante')    
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.restaurante.nombre_restaurante}"


# MENÚ Y PLATILLOS
class CategoriaMenu(models.Model):
    nombre_categoria = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre_categoria


class Platillo(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='platillos')
    categoria_menu = models.ForeignKey(CategoriaMenu, on_delete=models.CASCADE, related_name='platillos')
    nombre_platillo = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tiempo_preparacion = models.IntegerField(blank=True, null=True)
    disponible = models.BooleanField(default=True)
    es_especial_dia = models.BooleanField(default=False)
    foto = CloudinaryField('foto_platillo', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    numero_orden = models.IntegerField(blank=True, null=True)
    promocion = models.BooleanField(default=False)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.nombre_platillo


# PEDIDOS Y DETALLES
class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('sinpe', 'SINPE Móvil'),
        ('transferencia', 'Transferencia'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='pedidos')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notas_especiales = models.CharField(max_length=255, blank=True, null=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    platillo = models.ForeignKey(Platillo, on_delete=models.CASCADE, related_name='detalles')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}x {self.platillo.nombre_platillo} - Pedido #{self.pedido.id}"


# RESEÑAS
class Resena(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    calificacion = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.CharField(max_length=255, blank=True, null=True)
    fecha_resena = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.usuario.username} para {self.restaurante.nombre_restaurante}"        

class FotosResena(models.Model):
    resena = models.ForeignKey(Resena, on_delete=models.CASCADE)
    url_foto = CloudinaryField('foto_resena')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto reseña {self.resena.id}"

class Testimonio(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name="testimonios")
    nombre = models.CharField(max_length=100)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    calificacion = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.restaurante.nombre_restaurante}"        


# BLOG Y ETIQUETAS
class CategoriaBlog(models.Model):
    nombre_categoria = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    icono = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre_categoria


class ArticuloBlog(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('inactivo', 'Inactivo'),
    ]

    categoria_blog = models.ForeignKey(CategoriaBlog, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=150, unique=True)
    contenido = models.TextField()
    resumen = models.CharField(max_length=255, blank=True, null=True)
    imagen_portada = CloudinaryField('imagen_portada', blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    vistas = models.IntegerField(default=0)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='borrador')
    destacado = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo


class EtiquetaArticulo(models.Model):
    nombre_etiqueta = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nombre_etiqueta


class ArticuloEtiqueta(models.Model):
    articulo = models.ForeignKey(ArticuloBlog, on_delete=models.CASCADE)
    etiqueta = models.ForeignKey(EtiquetaArticulo, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('articulo', 'etiqueta')

    def __str__(self):
        return f"{self.articulo} - {self.etiqueta}"


# GALERÍA COMUNITARIA
class GaleriaComunitaria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    url_foto = CloudinaryField('foto_galeria')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class ComentariosGaleria(models.Model):
    foto_galeria = models.ForeignKey(GaleriaComunitaria, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comentario = models.CharField(max_length=255)
    fecha_comentario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.foto_galeria}"


# LUGARES TURÍSTICOS
class LugaresTuristicos(models.Model):
    nombre_lugar = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    imagen_principal = CloudinaryField('foto_lugar', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_lugar


class FotosLugares(models.Model):
    lugar = models.ForeignKey(LugaresTuristicos, on_delete=models.CASCADE)
    url_foto = CloudinaryField('foto_lugar')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.lugar}"


# MENSAJES DE CONTACTO
class MensajesContacto(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(max_length=120)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    asunto = models.CharField(max_length=120)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    archivado = models.BooleanField(default=False)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.nombre} - {self.asunto}"

#CONFIGURACIÓN
class ConfiguracionPlataforma(models.Model):
    """
    Modelo singleton para almacenar la configuración global de la plataforma.
    Solo debe existir UNA instancia de este modelo.
    """
    
    # Información General
    nombre_plataforma = models.CharField(max_length=200, default="El Sabor de la Perla del Pacífico")
    logo = CloudinaryField('logo_plataforma', blank=True, null=True)
    correo_contacto = models.EmailField(default="contacto@elsabor.com")
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    
    # Dirección
    direccion_general = models.CharField(max_length=255, blank=True, null=True)
    horarios_atencion = models.CharField(max_length=255, blank=True, null=True)
    
    # Misión, Visión y Valores
    mision = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)
    valores = models.TextField(blank=True, null=True)
    
    # Redes Sociales
    url_facebook = models.URLField(max_length=255, blank=True, null=True)
    url_instagram = models.URLField(max_length=255, blank=True, null=True)
    url_twitter = models.URLField(max_length=255, blank=True, null=True)
    url_tiktok = models.URLField(max_length=255, blank=True, null=True)
    url_youtube = models.URLField(max_length=255, blank=True, null=True)
    url_whatsapp = models.URLField(max_length=255, blank=True, null=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de la Plataforma"
        verbose_name_plural = "Configuración de la Plataforma"
    
    def __str__(self):
        return f"Configuración - {self.nombre_plataforma}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para asegurar que solo existe UNA instancia.
        Si se intenta crear otra, actualiza la existente.
        """
        if not self.pk and ConfiguracionPlataforma.objects.exists():
            # Si no tiene ID (es nueva) pero ya existe una configuración,
            # actualizar la existente en lugar de crear nueva
            self.pk = ConfiguracionPlataforma.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def obtener_instancia(cls):
        """
        Método para obtener la instancia única de la configuración.
        Si no existe, la crea con valores por defecto.
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
