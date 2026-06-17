from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User



# Missing required fields —

def test_create_private_user_missing_email(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={"password": "password123", "full_name": "No Email"},
    )
    assert response.status_code == 422


def test_create_private_user_missing_password(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={"email": "nopass@example.com", "full_name": "No Pass"},
    )
    assert response.status_code == 422


def test_create_private_user_missing_full_name(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={"email": "noname@example.com", "password": "password123"},
    )
    assert response.status_code == 422


def test_create_private_user_empty_body(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={},
    )
    assert response.status_code == 422


# Duplicate email 


def test_create_private_user_duplicate_email(
    client: TestClient, db: Session
) -> None:
    payload = {
        "email": "duplicate2@example.com",
        "password": "password123",
        "full_name": "First User",
    }
    first = client.post(
        f"{settings.API_V1_STR}/private/users/", json=payload
    )
    assert first.status_code == 200

    
    import pytest
    with pytest.raises(Exception):
        client.post(
            f"{settings.API_V1_STR}/private/users/", json=payload
        )




def test_create_private_user_is_stored_in_db(
    client: TestClient, db: Session
) -> None:
    payload = {
        "email": "stored@example.com",
        "password": "password123",
        "full_name": "Stored User",
    }
    response = client.post(
        f"{settings.API_V1_STR}/private/users/", json=payload
    )
    assert response.status_code == 200
    data = response.json()

  
    user = db.exec(select(User).where(User.id == data["id"])).first()
    assert user is not None
    assert user.email == "stored@example.com"
    assert user.full_name == "Stored User"
 
    assert user.hashed_password != "password123"


def test_create_private_user_default_not_superuser(
    client: TestClient, db: Session
) -> None:
    payload = {
        "email": "defaultrole@example.com",
        "password": "password123",
        "full_name": "Default Role",
    }
    response = client.post(
        f"{settings.API_V1_STR}/private/users/", json=payload
    )
    assert response.status_code == 200
    data = response.json()

    user = db.exec(select(User).where(User.id == data["id"])).first()
    assert user is not None
    assert user.is_superuser is False
    assert user.is_active is True