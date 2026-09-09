def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_browser_preflight_is_allowed_for_frontend_origins(client):
    """The Next.js dev server calls this API cross-origin; without CORS
    headers the browser blocks register/login/uploads while curl works."""
    for origin in ("http://localhost:3001", "http://localhost:3000"):
        response = client.options(
            "/api/v1/users/register",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_register_login_and_read_current_user(client):
    register_payload = {
        "username": "lawyer-test",
        "email": "lawyer-test@example.com",
        "password": "Test123456!",
    }

    register_response = client.post("/api/v1/users/register", json=register_payload)
    assert register_response.status_code == 200
    assert register_response.json()["email"] == register_payload["email"]

    login_response = client.post(
        "/api/v1/login/access-token",
        data={
            "username": register_payload["email"],
            "password": register_payload["password"],
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == register_payload["username"]


def test_login_rejects_wrong_password(client, make_user):
    user = make_user(
        email="wrong-password@example.com",
        username="wrong-password",
        password="Correct123!",
    )

    response = client.post(
        "/api/v1/login/access-token",
        data={
            "username": user.email,
            "password": "Wrong123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_rejects_inactive_user(client, make_user, auth_headers_for):
    inactive_user = make_user(
        email="inactive@example.com",
        username="inactive-user",
        is_active=False,
    )

    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers_for(inactive_user),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"
