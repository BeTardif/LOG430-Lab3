"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
import requests
from store_manager import app

BASE_URL = "http://localhost:5000"

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`)
    product_data = {'name': 'Some Item', 'sku': '12345', 'price': 99.90}
    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    
    assert response.status_code == 201

    data = response.get_json()
    assert data['product_id'] > 0 

    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    product_id = response.get_json()['product_id']
    added_stocks={
        "product_id": product_id,
        "quantity":5
    }
    response_stock_post = client.post('/stocks', json=added_stocks)
    assert response_stock_post.status_code == 201

    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    response_stock_get = client.get(f'/stocks/{product_id}')
    data = response_stock_get.get_json()

    assert data['quantity', 5]
    
    # 4. Faites une commande de l'article que vous avez crée, 2 unités (`POST /orders`)
    user_res = client.post('/users', json={'name': 'Somebody', 'email': 'someone@somewhere.com'})
    user_id = user_res.get_json()['id']

    order_payload = {'product_id': product_id, 'quantity': 2, 'user_id': user_id}
    res_order = client.post('/orders', json=order_payload)
    assert res_order.status_code == 201
    order_id = res_order.get_json()['id']

    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    res_stock_after = client.get(f'/stocks/{product_id}')
    assert res_stock_after.get_json()['quantity'] == 3

    # 6. Étape extra: supprimez la commande et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
    res_delete = client.delete(f'/orders/{order_id}')
    assert res_delete.status_code in [200, 204]