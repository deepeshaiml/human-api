from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from human_api.main import create_app


@pytest.fixture
def app(tmp_path: Path):
    return create_app(f"sqlite:///{tmp_path / 'human_api_test.db'}", scheduler_enabled=False)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def headers(user_id: str) -> dict[str, str]:
    return {"X-Demo-User": user_id}
