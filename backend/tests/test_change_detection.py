"""Unit tests for multi-survey temporal change detection."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.tree import Tree
from app.services.change_detection import match_surveys_change_detection


def make_dummy_tree(
    tree_id: str,
    survey_id: str,
    cx: float,
    cy: float,
    crown_area: float,
    carbon: float,
) -> Tree:
    """Helper to instantiate a dummy Tree record."""
    return Tree(
        tree_id=tree_id,
        survey_id=survey_id,
        geometry_geojson="{}",
        centroid_x=cx,
        centroid_y=cy,
        crown_area_sqm=crown_area,
        confidence=0.90,
        dbh_cm=20.0,
        biomass_kg=50.0,
        carbon_kg=carbon,
        status="detected",
        data_source="synthetic",
    )


def test_match_surveys_categories():
    """Tests bipartite matching correctly identifies new, lost, grown, and unchanged trees."""
    # Survey T1 trees
    t1_1 = make_dummy_tree("t1_1", "s1", 10.0, 10.0, crown_area=20.0, carbon=10.0)  # will grow
    t1_2 = make_dummy_tree("t1_2", "s1", 20.0, 20.0, crown_area=25.0, carbon=15.0)  # will stay unchanged
    t1_3 = make_dummy_tree("t1_3", "s1", 30.0, 30.0, crown_area=30.0, carbon=20.0)  # will be lost

    # Survey T2 trees
    t2_1 = make_dummy_tree("t2_1", "s2", 10.1, 10.1, crown_area=32.0, carbon=18.0)  # +60% growth -> grown
    t2_2 = make_dummy_tree("t2_2", "s2", 20.05, 20.05, crown_area=26.0, carbon=15.5)  # +4% growth -> unchanged
    t2_4 = make_dummy_tree("t2_4", "s2", 50.0, 50.0, crown_area=15.0, carbon=7.5)   # novel tree -> new

    summary = match_surveys_change_detection(
        trees_t1=[t1_1, t1_2, t1_3],
        trees_t2=[t2_1, t2_2, t2_4],
        max_centroid_dist_m=3.0,
        growth_threshold_pct=0.15,
    )

    assert len(summary.grown_trees) == 1
    assert summary.grown_trees[0].tree_id == "t2_1"

    assert len(summary.unchanged_trees) == 1
    assert summary.unchanged_trees[0].tree_id == "t2_2"

    assert len(summary.lost_trees) == 1
    assert summary.lost_trees[0].tree_id == "t1_3"

    assert len(summary.new_trees) == 1
    assert summary.new_trees[0].tree_id == "t2_4"


def test_compare_endpoint(client: TestClient, db_session: Session):
    """Tests GET /compare/{id1}/{id2} API endpoint."""
    # 1. Create project and two surveys
    p_res = client.post("/projects", json={"name": "Comparison Project"})
    project_id = p_res.json()["data"]["id"]

    from app.models.survey import Survey
    s1 = Survey(
        id="survey-t1",
        project_id=project_id,
        file_path="mock_t1.tif",
        original_filename="t1.tif",
        forest_type="tropical_moist",
    )
    s2 = Survey(
        id="survey-t2",
        project_id=project_id,
        file_path="mock_t2.tif",
        original_filename="t2.tif",
        forest_type="tropical_moist",
    )
    db_session.add_all([s1, s2])

    # Trees in T1
    tree_t1 = make_dummy_tree("tr1", "survey-t1", 10.0, 10.0, crown_area=20.0, carbon=10.0)
    # Trees in T2
    tree_t2_grown = make_dummy_tree("tr2_grown", "survey-t2", 10.0, 10.0, crown_area=35.0, carbon=18.0)
    tree_t2_new = make_dummy_tree("tr2_new", "survey-t2", 80.0, 80.0, crown_area=15.0, carbon=7.0)

    db_session.add_all([tree_t1, tree_t2_grown, tree_t2_new])
    db_session.commit()

    cmp_res = client.get("/compare/survey-t1/survey-t2")
    assert cmp_res.status_code == 200
    data = cmp_res.json()["data"]

    assert data["grown_trees"]["count"] == 1
    assert data["new_trees"]["count"] == 1
    assert data["lost_trees"]["count"] == 0
    assert data["net_tree_change"] == 1
