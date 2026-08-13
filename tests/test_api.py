from fastapi.testclient import TestClient

from skylinee_harness import __version__
from skylinee_harness.main import app


def test_healthz_reports_version() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}
