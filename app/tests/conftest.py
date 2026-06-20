"""Test fixtures — a TestClient over a freshly-seeded mock cloud per test.

`store.db`, `main.db` and `sim.db` are all the *same* singleton object. We reset
it in place (rather than reassigning) so every module keeps seeing the same fresh
fleet. Tests assert *observable behaviour* (what an operator sees / the API
returns), not internal calls — per the PRD's testing decisions.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app import store
    from app.main import app
    store.db.__dict__.update(store.Store().__dict__)   # reset state in place
    return TestClient(app)
