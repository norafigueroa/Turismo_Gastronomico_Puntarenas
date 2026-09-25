from decimal import Decimal

import pytest

from api.models import Pedido
from .factories import PedidoFactory, PlatilloFactory, RestauranteFactory

NO_AUTORIZADO = (401, 403)


def payload(restaurante, *items, **extra):
    """Cuerpo de un pedido. Los precios/total enviados a propósito son falsos."""
    datos = {
        'restaurante': restaurante.id,
        'metodo_pago': 'efectivo',
        'subtotal': '1.00',
        'total': '1.00',
        'items': [
            {'platillo': platillo.id, 'cantidad': cantidad, 'precio_unitario': '1.00'}
            for platillo, cantidad in items
        ],
    }
    datos.update(extra)
    return datos


@pytest.mark.crud
@pytest.mark.django_db
class TestCrearPedido:

    def test_el_servidor_recalcula_precios_y_total(self, authenticated_client, restaurante):
        ceviche = PlatilloFactory(restaurante=restaurante, precio=Decimal('1000.00'))
        arroz = PlatilloFactory(restaurante=restaurante, precio=Decimal('2500.50'))

        response = authenticated_client.post(
            '/api/pedidos/', payload(restaurante, (ceviche, 2), (arroz, 1)), format='json'
        )

        assert response.status_code == 201
        pedido = Pedido.objects.get(id=response.data['id'])
        assert pedido.subtotal == Decimal('4500.50')
        assert pedido.total == Decimal('4500.50')
        precios = {d.platillo_id: d.precio_unitario for d in pedido.detalles.all()}
        assert precios == {ceviche.id: Decimal('1000.00'), arroz.id: Decimal('2500.50')}

    def test_aplica_la_promocion_vigente(self, authenticated_client, restaurante):
        promo = PlatilloFactory(
            restaurante=restaurante, precio=Decimal('2000.00'),
            promocion=True, porcentaje=Decimal('10.00'),
        )
        response = authenticated_client.post('/api/pedidos/', payload(restaurante, (promo, 2)), format='json')

        assert response.status_code == 201
        assert Pedido.objects.get(id=response.data['id']).total == Decimal('3600.00')

    def test_el_pedido_queda_a_nombre_del_usuario_autenticado(
        self, authenticated_client, usuario_cliente, restaurante
    ):
        platillo = PlatilloFactory(restaurante=restaurante)
        otro = PedidoFactory().usuario
        response = authenticated_client.post(
            '/api/pedidos/', payload(restaurante, (platillo, 1), usuario=otro.id), format='json'
        )
        assert response.status_code == 201
        assert Pedido.objects.get(id=response.data['id']).usuario_id == usuario_cliente.id

    def test_rechaza_platillo_de_otro_restaurante(self, authenticated_client, restaurante):
        ajeno = PlatilloFactory(restaurante=RestauranteFactory())
        response = authenticated_client.post('/api/pedidos/', payload(restaurante, (ajeno, 1)), format='json')
        assert response.status_code == 400
        assert Pedido.objects.count() == 0

    def test_rechaza_platillo_no_disponible(self, authenticated_client, restaurante):
        agotado = PlatilloFactory(restaurante=restaurante, disponible=False)
        response = authenticated_client.post('/api/pedidos/', payload(restaurante, (agotado, 1)), format='json')
        assert response.status_code == 400
        assert Pedido.objects.count() == 0

    def test_rechaza_pedido_sin_items(self, authenticated_client, restaurante):
        response = authenticated_client.post('/api/pedidos/', payload(restaurante), format='json')
        assert response.status_code == 400

    def test_rechaza_cantidad_invalida(self, authenticated_client, restaurante):
        platillo = PlatilloFactory(restaurante=restaurante)
        for cantidad in (0, -3):
            response = authenticated_client.post(
                '/api/pedidos/', payload(restaurante, (platillo, cantidad)), format='json'
            )
            assert response.status_code == 400

    def test_anonimo_no_puede_crear_pedidos(self, client, restaurante):
        platillo = PlatilloFactory(restaurante=restaurante)
        response = client.post('/api/pedidos/', payload(restaurante, (platillo, 1)), format='json')
        assert response.status_code in NO_AUTORIZADO


@pytest.mark.permissions
@pytest.mark.django_db
class TestVerYGestionarPedidos:

    def test_cada_cliente_ve_solo_sus_pedidos(self, authenticated_client, usuario_cliente, restaurante):
        propio = PedidoFactory(usuario=usuario_cliente, restaurante=restaurante)
        PedidoFactory(restaurante=restaurante)  # de otro cliente

        response = authenticated_client.get('/api/pedidos/')

        assert response.status_code == 200
        assert [p['id'] for p in response.data] == [propio.id]

    def test_el_dueno_ve_los_pedidos_de_su_restaurante(self, admin_rest_client, restaurante):
        del_restaurante = PedidoFactory(restaurante=restaurante)
        PedidoFactory(restaurante=RestauranteFactory())  # de otro restaurante

        for url in ('/api/pedidos/', '/api/pedidos/admin/'):
            response = admin_rest_client.get(url)
            assert response.status_code == 200
            assert [p['id'] for p in response.data] == [del_restaurante.id]

    def test_detalle_de_pedido_ajeno_no_es_visible(self, authenticated_client, restaurante):
        ajeno = PedidoFactory(restaurante=restaurante)
        assert authenticated_client.get(f'/api/pedidos/{ajeno.id}').status_code == 404

    def test_anonimo_no_accede_a_pedidos(self, client, restaurante):
        pedido = PedidoFactory(restaurante=restaurante)
        assert client.get('/api/pedidos/').status_code in NO_AUTORIZADO
        assert client.get(f'/api/pedidos/{pedido.id}').status_code in NO_AUTORIZADO
        assert client.patch(
            f'/api/pedidos/{pedido.id}', {'estado_pedido': 'entregado'}, format='json'
        ).status_code in NO_AUTORIZADO
        assert client.delete(f'/api/pedidos/{pedido.id}').status_code in NO_AUTORIZADO

    def test_cliente_no_puede_cambiar_estado_ni_eliminar(self, authenticated_client, usuario_cliente, restaurante):
        pedido = PedidoFactory(usuario=usuario_cliente, restaurante=restaurante)
        assert authenticated_client.get(f'/api/pedidos/{pedido.id}').status_code == 200
        assert authenticated_client.patch(
            f'/api/pedidos/{pedido.id}', {'estado_pedido': 'entregado'}, format='json'
        ).status_code == 403
        assert authenticated_client.delete(f'/api/pedidos/{pedido.id}').status_code == 403
        assert Pedido.objects.filter(id=pedido.id, estado_pedido='pendiente').exists()

    def test_dueno_cambia_solo_el_estado(self, admin_rest_client, restaurante):
        pedido = PedidoFactory(restaurante=restaurante, total=Decimal('5000.00'), subtotal=Decimal('5000.00'))

        response = admin_rest_client.patch(
            f'/api/pedidos/{pedido.id}/',  # el front-end usa "/" final
            {'estado_pedido': 'en_proceso', 'total': '1.00'},
            format='json',
        )

        assert response.status_code == 200
        pedido.refresh_from_db()
        assert pedido.estado_pedido == 'en_proceso'
        assert pedido.total == Decimal('5000.00')

    def test_dueno_de_otro_restaurante_no_puede_gestionar(self, admin_rest_client):
        pedido = PedidoFactory(restaurante=RestauranteFactory())
        assert admin_rest_client.patch(
            f'/api/pedidos/{pedido.id}', {'estado_pedido': 'entregado'}, format='json'
        ).status_code == 404
        assert admin_rest_client.delete(f'/api/pedidos/{pedido.id}').status_code == 404

    def test_dueno_puede_eliminar_pedido_de_su_restaurante(self, admin_rest_client, restaurante):
        pedido = PedidoFactory(restaurante=restaurante)
        assert admin_rest_client.delete(f'/api/pedidos/{pedido.id}/').status_code == 204
        assert not Pedido.objects.filter(id=pedido.id).exists()
