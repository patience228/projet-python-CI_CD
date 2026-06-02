import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app import models

# Base de données en mémoire pour les tests
TEST_DB = "sqlite:///./test.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_todo():
    r = client.post("/todos", json={"title": "Apprendre CI/CD"})
    # assert r.status_code == 201
    assert r.status_code == 200  # volontairement faux !
    assert r.json()["title"] == "Apprendre CI/CD"
    assert r.json()["done"] == False

def test_list_todos():
    client.post("/todos", json={"title": "Tâche 1"})
    client.post("/todos", json={"title": "Tâche 2"})
    r = client.get("/todos")
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_get_todo():
    created = client.post("/todos", json={"title": "Tâche test"}).json()
    r = client.get(f"/todos/{created['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Tâche test"

def test_get_todo_not_found():
    r = client.get("/todos/999")
    assert r.status_code == 404

def test_update_todo():
    created = client.post("/todos", json={"title": "Ancienne"}).json()
    r = client.put(f"/todos/{created['id']}", json={"title": "Nouvelle", "done": True})
    assert r.status_code == 200
    assert r.json()["title"] == "Nouvelle"
    assert r.json()["done"] == True

def test_delete_todo():
    created = client.post("/todos", json={"title": "À supprimer"}).json()
    r = client.delete(f"/todos/{created['id']}")
    assert r.status_code == 204
    r = client.get(f"/todos/{created['id']}")
    assert r.status_code == 404