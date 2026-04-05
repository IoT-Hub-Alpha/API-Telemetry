from __future__ import annotations

from datetime import datetime, timezone
import importlib

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_module(monkeypatch):
    module = importlib.import_module("app.main")
    importlib.reload(module)
    return module


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


class FakeQuery:
    def __init__(self):
        self.filters = []

    def filter(self, *conditions):
        self.filters.extend(conditions)
        return self


class FakeSession:
    def __init__(self):
        self.query_model = None
        self.query_obj = FakeQuery()

    def query(self, model):
        self.query_model = model
        return self.query_obj


@pytest.fixture
def fake_db(app_module):
    session = FakeSession()
    app_module.app.dependency_overrides[app_module.get_db] = lambda: session
    yield session
    app_module.app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/v1/telemetry/health")
    assert response.status_code == 200
    assert response.json() == {"health": "ok"}


@pytest.mark.anyio
async def test_get_telemetry_without_filters(app_module, fake_db, monkeypatch):
    def fake_paginate(query):
        assert query is fake_db.query_obj
        return {
            "items": [
                {
                    "id": 1,
                    "device": "device-1",
                    "timestamp": "2026-04-05T10:00:00Z",
                    "payload": {"temperature": 23},
                }
            ],
            "total": 1,
            "page": 1,
            "size": 50,
            "pages": 1,
        }

    monkeypatch.setattr(app_module, "paginate", fake_paginate)

    body = await app_module.get_telemetry(db=fake_db, auth={"sub": "x"})

    assert body["items"][0]["device"] == "device-1"
    assert fake_db.query_model is app_module.Telemetry
    assert fake_db.query_obj.filters == []


@pytest.mark.anyio
async def test_get_telemetry_with_all_filters(app_module, fake_db, monkeypatch):
    def fake_paginate(query):
        return {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}

    monkeypatch.setattr(app_module, "paginate", fake_paginate)

    after = "2026-04-05T09:00:00Z"
    before = "2026-04-05T11:00:00Z"
    body = await app_module.get_telemetry(
        device="device-7",
        after=datetime.fromisoformat("2026-04-05T09:00:00+00:00"),
        before=datetime.fromisoformat("2026-04-05T11:00:00+00:00"),
        db=fake_db,
        auth={"sub": "x"},
    )

    assert body["items"] == []
    assert len(fake_db.query_obj.filters) == 3


def test_get_aggregates_success(client, app_module, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"avg": 12.5, "count": 4}

    class FakeAsyncClient:
        def __init__(self, timeout):
            assert timeout == 10.0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params):
            assert params["device"] == "abc"
            assert url == "http://scala-aggregation-service:8081/agg"
            return FakeResponse()

    monkeypatch.setattr(app_module.httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/v1/telemetry/aggregates", params={"device": "abc"})

    assert response.status_code == 200
    assert response.json() == {"avg": 12.5, "count": 4}


@pytest.mark.parametrize(
    ("exc", "expected_prefix"),
    [
        (httpx.ConnectError("boom"), "Connect error:"),
        (httpx.ReadTimeout("slow"), "Timeout:"),
        (httpx.RequestError("bad request"), "Request error:"),
    ],
)
def test_get_aggregates_request_failures(
    client, app_module, monkeypatch, exc, expected_prefix
):
    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params):
            raise exc

    monkeypatch.setattr(app_module.httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/v1/telemetry/aggregates")

    assert response.status_code == 502
    assert response.json()["detail"].startswith(expected_prefix)


def test_get_aggregates_http_status_error(client, app_module, monkeypatch):
    request = httpx.Request("GET", "http://scala-aggregation-service:8081/agg")
    bad_response = httpx.Response(503, request=request, text="service unavailable")
    error = httpx.HTTPStatusError(
        "upstream failed", request=request, response=bad_response
    )

    class FakeResponse:
        def raise_for_status(self):
            raise error

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params):
            return FakeResponse()

    monkeypatch.setattr(app_module.httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/v1/telemetry/aggregates")

    assert response.status_code == 502
    assert response.json()["detail"] == "Scala returned 503: service unavailable"


def test_telemetry_response_model_from_attributes():
    schemas = importlib.import_module("app.services.schemas")

    class Obj:
        id = 5
        device = "sensor-9"
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        payload = {"humidity": 55}

    model = schemas.TelemetryResponse.model_validate(Obj(), from_attributes=True)
    assert model.id == 5
    assert model.payload == {"humidity": 55}


def test_get_db_yields_and_closes(monkeypatch):
    database = importlib.import_module("app.services.database")

    class DummySession:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    session = DummySession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    gen = database.get_db()
    yielded = next(gen)
    assert yielded is session
    with pytest.raises(StopIteration):
        next(gen)
    assert session.closed is True


def test_models_table_metadata():
    models = importlib.import_module("app.models")
    table = models.Telemetry.__table__

    assert table.name == "telemetry"
    assert table.c.device.nullable is False
    assert str(table.c.payload.type) == "JSONB"
    assert {idx.name for idx in table.indexes} == {
        "idx_telemetry_device_time",
        "idx_telemetry_payload_gin",
    }
