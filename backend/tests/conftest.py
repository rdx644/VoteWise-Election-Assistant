"""
Pytest configuration and shared fixtures for VoteWise tests.
"""

from __future__ import annotations

import os

os.environ["APP_ENV"] = "testing"
os.environ["RATE_LIMIT_RPM"] = "10000"
os.environ["RATE_LIMIT_BURST"] = "10000"

import pytest
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
