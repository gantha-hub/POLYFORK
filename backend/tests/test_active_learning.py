"""Unit tests for Active Learning audit queue and verification actions."""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from shapely.geometry import box, mapping
from app.models.survey import Survey
from app.models.tree import Tree
from app.services.active_learning import rank_trees_for_verification


def test_active_learning_ranking():
    """Tests that low-confidence and anomalous trees receive higher audit priority."""
    t_high_conf = Tree(
        tree_id="t1",
        survey_id="s1",
        geometry_geojson="{}",
        centroid_x=10.0,
        centroid_y=10.0,
        crown_area_sqm=25.0,
        confidence=0.95,
        status="detected",
        data_source="synthetic",
    )
    t_low_conf = Tree(
        tree_id="t2",
        survey_id="s1",
        geometry_geojson="{}",
        centroid_x=20.0,
        centroid_y=20.0,
        crown_area_sqm=25.0,
        confidence=0.52,  # Low confidence
        status="detected",
        data_source="synthetic",
    )

    ranked = rank_trees_for_verification([t_high_conf, t_low_conf])
    assert len(ranked) == 2
    # The low confidence tree must be first in queue
    assert ranked[0]["tree_id"] == "t2"
    assert ranked[0]["priority_score"] > ranked[1]["priority_score"]


def test_verify_queue_and_actions(client: TestClient, db_session: Session):
    """Tests GET /verify/queue/{id} and POST /verify (accept, reject, edit)."""
    p_res = client.post("/projects", json={"name": "Verification Project"})
    project_id = p_res.json()["data"]["id"]

    survey = Survey(
        id="survey-ver-1",
        project_id=project_id,
        file_path="mock.tif",
        original_filename="mock.tif",
        forest_type="tropical_moist",
    )
    db_session.add(survey)

    tree1 = Tree(
        tree_id="tr-to-accept",
        survey_id="survey-ver-1",
        geometry_geojson=json.dumps(mapping(box(0, 0, 5, 5))),
        centroid_x=2.5,
        centroid_y=2.5,
        crown_area_sqm=25.0,
        confidence=0.55,
        status="detected",
        data_source="synthetic",
    )
    tree2 = Tree(
        tree_id="tr-to-reject",
        survey_id="survey-ver-1",
        geometry_geojson=json.dumps(mapping(box(10, 10, 15, 15))),
        centroid_x=12.5,
        centroid_y=12.5,
        crown_area_sqm=25.0,
        confidence=0.48,
        status="detected",
        data_source="synthetic",
    )
    db_session.add_all([tree1, tree2])
    db_session.commit()

    # 1. Fetch Queue
    q_res = client.get("/verify/queue/survey-ver-1")
    assert q_res.status_code == 200
    queue = q_res.json()["data"]
    assert len(queue) == 2

    # 2. Accept Tree 1
    acc_res = client.post(
        "/verify",
        json={"tree_id": "tr-to-accept", "action": "accept", "user_id": "auditor_bob"},
    )
    assert acc_res.status_code == 201

    db_session.refresh(tree1)
    assert tree1.status == "verified"

    # 3. Reject Tree 2
    rej_res = client.post(
        "/verify",
        json={"tree_id": "tr-to-reject", "action": "reject", "user_id": "auditor_bob"},
    )
    assert rej_res.status_code == 201

    db_session.refresh(tree2)
    assert tree2.status == "rejected"
