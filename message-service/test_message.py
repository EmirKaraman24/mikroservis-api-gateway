import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_send_message(client):
    response = client.post('/messages', json={"content": "Hello", "sender": "user1"})
    assert response.status_code == 201
    assert response.get_json()["message"] == "Message sent"

def test_get_messages(client):
    response = client.get('/messages')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_delete_message(client):
    response = client.delete('/messages/1')
    assert response.status_code == 200
    assert response.get_json()["message"] == "Message deleted"
