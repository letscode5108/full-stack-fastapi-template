from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.crud import create_user
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string


# Inactive user cannot log in


def test_login_inactive_user(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    create_user(session=db, user_create=user_in)

    login_data = {"username": email, "password": password}
    response = client.post(
        f"{settings.API_V1_STR}/login/access-token", data=login_data
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


# test-token endpoint with bad / missing token

def test_test_token_no_auth(client: TestClient) -> None:
    response = client.post(f"{settings.API_V1_STR}/login/test-token")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_test_token_malformed_token(client: TestClient) -> None:
    headers = {"Authorization": "Bearer this.is.not.a.valid.jwt"}
    response = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=headers
    )
    assert response.status_code == 403


def test_test_token_wrong_scheme(client: TestClient) -> None:
    headers = {"Authorization": "Basic sometoken"}
    response = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=headers
    )
    assert response.status_code == 401


# Reset password edge cases not in existing tests


def test_reset_password_inactive_user(client: TestClient, db: Session) -> None:
    from app.utils import generate_password_reset_token

    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    create_user(session=db, user_create=user_in)

    token = generate_password_reset_token(email=email)
    data = {"new_password": random_lower_string(), "token": token}
    response = client.post(f"{settings.API_V1_STR}/reset-password/", json=data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


def test_reset_password_new_password_too_short(client: TestClient) -> None:
    from app.utils import generate_password_reset_token

    token = generate_password_reset_token(email=settings.FIRST_SUPERUSER)
    data = {"new_password": "short", "token": token}
    response = client.post(f"{settings.API_V1_STR}/reset-password/", json=data)
    assert response.status_code == 422