from app import app, init_db

init_db()


def client():
    return app.test_client()


def test_health():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_home_page():
    r = client().get("/")
    assert r.status_code == 200
    assert b"Hello DevOps" in r.data


def test_about_page():
    assert client().get("/about").status_code == 200


def test_version():
    r = client().get("/version")
    assert r.status_code == 200
    assert "version" in r.get_json()


def test_api_list_tasks():
    r = client().get("/api/tasks")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_api_add_task():
    r = client().post("/api/tasks", json={"title": "Learn Terraform"})
    assert r.status_code == 201
    assert r.get_json()["title"] == "Learn Terraform"


def test_api_add_task_requires_title():
    r = client().post("/api/tasks", json={})
    assert r.status_code == 400


def test_error_route_returns_500():
    assert client().get("/error").status_code == 500
