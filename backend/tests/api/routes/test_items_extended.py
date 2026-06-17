import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.item import create_random_item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string



# Unauthenticated access


def test_create_item_no_auth(client: TestClient) -> None:
    data = {"title": "Foo", "description": "Bar"}
    response = client.post(f"{settings.API_V1_STR}/items/", json=data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_read_items_no_auth(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/items/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_read_item_no_auth(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/items/{uuid.uuid4()}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_item_no_auth(client: TestClient) -> None:
    data = {"title": "Updated", "description": "Updated"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}", json=data
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_delete_item_no_auth(client: TestClient) -> None:
    response = client.delete(f"{settings.API_V1_STR}/items/{uuid.uuid4()}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# Input validation 


def test_create_item_empty_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # title min_length=1 on ItemBase, empty string should be rejected
    data = {"title": "", "description": "Some description"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422


def test_create_item_title_too_long(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # title max_length=255
    data = {"title": "x" * 256, "description": "desc"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422


def test_create_item_missing_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # title is required, description is optional
    data = {"description": "No title here"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422


def test_create_item_no_description(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # description is optional (default None), this should succeed
    data = {"title": "Title only"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Title only"
    assert content["description"] is None


# Pagination 
def test_read_items_limit_zero(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # ensure at least one item exists
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/?limit=0",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["data"] == []
    # count still reflects total rows even when limit=0
    assert content["count"] >= 1


def test_read_items_skip_beyond_count(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/?skip=99999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["data"] == []


# Normal user — owns their items, cannot see others' items

def test_normal_user_can_create_item(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"title": "My item", "description": "Owned by normal user"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "My item"
    assert "owner_id" in content


def test_normal_user_sees_only_own_items(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # create an item belonging to a different user directly in DB
    other_item = create_random_item(db)

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    item_ids = [item["id"] for item in content["data"]]
    # the other user's item must NOT appear in this user's list
    assert str(other_item.id) not in item_ids


def test_normal_user_can_update_own_item(
    client: TestClient, normal_user_token_headers: dict[str, str], 
) -> None:
    # create item as normal user first
    create_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        json={"title": "Before update"},
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    update_response = client.put(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=normal_user_token_headers,
        json={"title": "After update"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "After update"


def test_normal_user_can_delete_own_item(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    create_response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        json={"title": "To be deleted"},
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    delete_response = client.delete(
        f"{settings.API_V1_STR}/items/{item_id}",
        headers=normal_user_token_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Item deleted successfully"