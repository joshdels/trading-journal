import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


@pytest.fixture
def client_logged_in(client):
    get_user_model().objects.create_user("joshua", password="pw12345")
    client.login(username="joshua", password="pw12345")
    return client


def test_portal_requires_login(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.url


def test_portal_ok(client_logged_in):
    assert client_logged_in.get("/").status_code == 200


def test_calendar_and_charts_ok(client_logged_in):
    assert client_logged_in.get("/calendar/").status_code == 200
    assert client_logged_in.get("/charts/").status_code == 200
    assert client_logged_in.get("/trades/").status_code == 200


def test_calendar_aggregation_toggles(client_logged_in):
    assert client_logged_in.get("/calendar/daily/").status_code == 200
    assert client_logged_in.get("/calendar/monthly/").status_code == 200
    assert client_logged_in.get("/calendar/monthly/?year=2026").status_code == 200
