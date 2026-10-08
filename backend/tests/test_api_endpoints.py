"""Unit tests for Phase 1 API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Tests the root informational endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["status"] == "online"
    assert data["model_backend"] in ["mock", "torch"]


def test_health_check(client: TestClient):
    """Tests the /health diagnostic endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "healthy"
    assert res_json["data"]["database"] == "connected"
    assert res_json["data_source"] in ["synthetic", "real"]


def test_create_and_list_projects(client: TestClient):
    """Tests project creation and listing."""
    # 1. Create a project
    payload = {
        "name": "Western Ghats Canopy Survey 2026",
        "description": "High resolution UAV survey over moist deciduous forest reserve.",
    }
    response = client.post("/projects", json=payload)
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["success"] is True
    project_data = res_json["data"]
    assert project_data["name"] == payload["name"]
    assert "id" in project_data

    project_id = project_data["id"]

    # 2. List projects
    list_response = client.get("/projects")
    assert list_response.status_code == 200
    list_json = list_response.json()
    assert list_json["success"] is True
    assert len(list_json["data"]) >= 1
    assert any(p["id"] == project_id for p in list_json["data"])


def test_project_validation_failure(client: TestClient):
    """Tests validation error on empty project name."""
    response = client.post("/projects", json={"name": ""})
    assert response.status_code == 422


def test_get_project_and_project_surveys(client: TestClient):
    """Tests GET /projects/{id} and GET /projects/{id}/surveys."""
    # 1. Create a project
    create_res = client.post("/projects", json={"name": "Fetch Test Project"})
    assert create_res.status_code == 201
    proj_id = create_res.json()["data"]["id"]

    # 2. Get single project
    get_res = client.get(f"/projects/{proj_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "Fetch Test Project"

    # 3. List surveys for project (initially empty)
    surveys_res = client.get(f"/projects/{proj_id}/surveys")
    assert surveys_res.status_code == 200
    assert isinstance(surveys_res.json()["data"], list)

    # 4. Test 404 on nonexistent project
    bad_res = client.get("/projects/nonexistent-uuid-1234")
    assert bad_res.status_code == 404
