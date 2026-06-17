from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings



# Health check —
def test_health_check(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


# test-email endpoint 

def test_send_test_email_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.send_email", return_value=None):
        response = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            headers=superuser_token_headers,
            params={"email_to": "test@example.com"},
        )
    assert response.status_code == 201
    assert response.json()["message"] == "Test email sent"


def test_send_test_email_as_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        headers=normal_user_token_headers,
        params={"email_to": "test@example.com"},
    )
    assert response.status_code == 403


def test_send_test_email_no_auth(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
    )
    assert response.status_code == 401


def test_send_test_email_invalid_email(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # email_to is EmailStr — invalid format should be rejected
    response = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        headers=superuser_token_headers,
        params={"email_to": "not-an-email"},
    )
    assert response.status_code == 422