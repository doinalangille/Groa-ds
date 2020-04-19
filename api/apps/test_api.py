from fastapi.testclient import TestClient
from apps import create_app

application = create_app()
client = TestClient(application)


def test_index():
    response = client.get("/")
    assert response.status_code == 200


def test_wrong_method():
    response = client.post("/", json={"message": "testing"})
    assert response.status_code == 405


def test_decades():
    response = client.get("/stats/decades/1")
    assert response.status_code == 200


def test_recommendations():
    payload = {
        "user_id": 11,
        "number_of_recommendations": 50,
        "good_threshold": 5,
        "bad_threshold": 4,
        "harshness": 1
    }
    response = client.post("/recommendation", json=payload)
    assert response.status_code == 200
