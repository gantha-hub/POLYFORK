"""Unit tests for allometric carbon estimation and Monte Carlo uncertainty propagation."""

import pytest
from app.services.carbon import (
    load_carbon_parameters,
    compute_tree_allometry_point,
    run_monte_carlo_carbon_estimation,
)


def test_load_carbon_parameters():
    """Verifies that allometric coefficients load correctly from config/carbon.yaml."""
    params = load_carbon_parameters("tropical_moist")
    assert params.carbon_fraction == 0.47
    assert params.a > 0
    assert params.b > 0
    assert params.sigma_dbh > 0
    assert params.sigma_agb > 0


def test_compute_tree_allometry_point():
    """Tests single tree allometric scaling CPA -> DBH -> AGB -> Carbon."""
    dbh, agb, carbon = compute_tree_allometry_point(crown_area_sqm=25.0)
    assert dbh > 5.0  # Realistic DBH in cm
    assert agb > 10.0  # Dry biomass in kg
    assert carbon == pytest.approx(agb * 0.47, abs=0.5)


def test_monte_carlo_carbon_simulation_1000_draws():
    """Tests that Monte Carlo error propagation generates valid mean and 90% confidence bounds."""
    crown_areas = [15.0, 25.0, 40.0, 10.0, 55.0, 30.0, 20.0, 35.0]

    result = run_monte_carlo_carbon_estimation(
        crown_areas_sqm=crown_areas,
        forest_type="tropical_moist",
        n_draws=1000,
        random_seed=42,
    )

    assert result.mean_carbon_kg > 0
    assert result.mean_carbon_tonnes == pytest.approx(result.mean_carbon_kg / 1000.0, abs=0.01)

    # 90% confidence interval: low < mean < high
    assert result.interval_kg.low < result.mean_carbon_kg < result.interval_kg.high
    assert result.interval_tonnes.low < result.mean_carbon_tonnes < result.interval_tonnes.high
    assert result.interval_kg.confidence_level == 0.90
