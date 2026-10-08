"""Allometric carbon estimation service with Monte Carlo error propagation.

Converts Crown Projection Area (CPA, m^2) -> DBH (cm) -> Biomass (kg) -> Carbon (kg C).
Runs 1,000 Monte Carlo draws to propagate parameter uncertainty and return mean and 90% confidence intervals.
Loads regional coefficients from config/carbon.yaml.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import numpy as np
from app.schemas.common import CarbonEstimateResult, ConfidenceInterval
from app.core.logging import logger

CARBON_CONFIG_PATH = Path("./config/carbon.yaml")


@dataclass
class CarbonModelParams:
    """Allometric parameter set for a specific forest type."""

    forest_type: str
    carbon_fraction: float
    a: float  # DBH scaling constant: DBH = a * CPA^b
    b: float  # DBH power exponent
    sigma_dbh: float  # Standard deviation of error in ln(DBH)
    c0: float  # Biomass intercept in ln-space
    c1: float  # Biomass slope in ln-space
    c2: float
    wood_density: float
    sigma_agb: float  # Standard deviation of residual error in ln(AGB)


def load_carbon_parameters(forest_type: str = "tropical_moist") -> CarbonModelParams:
    """Loads allometric equation coefficients from config/carbon.yaml."""
    if not CARBON_CONFIG_PATH.exists():
        logger.warning(f"Carbon config not found at {CARBON_CONFIG_PATH}. Using fallback coefficients.")
        return CarbonModelParams(
            forest_type=forest_type,
            carbon_fraction=0.47,
            a=1.85,
            b=0.62,
            sigma_dbh=0.15,
            c0=-1.803,
            c1=2.148,
            c2=0.0,
            wood_density=0.60,
            sigma_agb=0.20,
        )

    with CARBON_CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    c_frac = float(cfg.get("carbon_fraction", 0.47))
    forests = cfg.get("forest_types", {})
    params_dict = forests.get(forest_type, forests.get("custom_uncalibrated", {}))

    c2dbh = params_dict.get("crown_to_dbh", {})
    dbh2agb = params_dict.get("dbh_to_agb", {})

    return CarbonModelParams(
        forest_type=forest_type,
        carbon_fraction=c_frac,
        a=float(c2dbh.get("a", 1.85)),
        b=float(c2dbh.get("b", 0.62)),
        sigma_dbh=float(c2dbh.get("sigma_err", 0.15)),
        c0=float(dbh2agb.get("c0", -1.803)),
        c1=float(dbh2agb.get("c1", 2.148)),
        c2=float(dbh2agb.get("c2", 0.0)),
        wood_density=float(dbh2agb.get("wood_density", 0.60)),
        sigma_agb=float(dbh2agb.get("sigma_err", 0.20)),
    )


def compute_tree_allometry_point(
    crown_area_sqm: float,
    params: Optional[CarbonModelParams] = None,
) -> Tuple[float, float, float]:
    """Computes point estimates of DBH (cm), AGB (kg), and Carbon (kg C).

    Args:
        crown_area_sqm: Crown Projection Area in m^2.
        params: Optional CarbonModelParams.

    Returns:
        Tuple of (dbh_cm, biomass_kg, carbon_kg).
    """
    if params is None:
        params = load_carbon_parameters("tropical_moist")

    cpa = max(1.0, crown_area_sqm)

    # 1. CPA -> DBH: DBH = a * CPA^b
    dbh = max(5.0, params.a * (cpa ** params.b))

    # 2. DBH -> AGB: ln(AGB) = c0 + c1*ln(DBH) + c2*(ln(DBH)^2)
    ln_dbh = np.log(dbh)
    ln_agb = params.c0 + params.c1 * ln_dbh + params.c2 * (ln_dbh ** 2)
    agb = max(10.0, np.exp(ln_agb))

    # 3. AGB -> Carbon: Carbon = AGB * carbon_fraction
    carbon = agb * params.carbon_fraction

    return round(float(dbh), 2), round(float(agb), 2), round(float(carbon), 2)


def run_monte_carlo_carbon_estimation(
    crown_areas_sqm: List[float],
    forest_type: str = "tropical_moist",
    n_draws: int = 1000,
    random_seed: int = 42,
) -> CarbonEstimateResult:
    """Runs 1,000 Monte Carlo draws propagating allometric uncertainty across detected trees.

    Args:
        crown_areas_sqm: List of crown projection areas in m^2.
        forest_type: Forest biome name matching config/carbon.yaml.
        n_draws: Number of Monte Carlo draws (default: 1000).
        random_seed: Seed for reproducible uncertainty distributions.

    Returns:
        CarbonEstimateResult containing mean carbon and 90% confidence bounds in kg and tonnes.
    """
    if not crown_areas_sqm:
        zero_interval = ConfidenceInterval(low=0.0, high=0.0, confidence_level=0.90)
        return CarbonEstimateResult(
            mean_carbon_kg=0.0,
            mean_carbon_tonnes=0.0,
            interval_kg=zero_interval,
            interval_tonnes=zero_interval,
            carbon_fraction=0.47,
        )

    params = load_carbon_parameters(forest_type)
    rng = np.random.default_rng(random_seed)

    areas = np.maximum(np.array(crown_areas_sqm, dtype=np.float64), 1.0)
    n_trees = len(areas)

    # Vectorized Monte Carlo: shape (n_draws, n_trees)
    # 1. CPA -> DBH error draws: ln(DBH) = ln(a) + b*ln(CPA) + eps_dbh
    base_ln_dbh = np.log(params.a) + params.b * np.log(areas)
    eps_dbh = rng.normal(loc=0.0, scale=params.sigma_dbh, size=(n_draws, n_trees))
    draw_ln_dbh = base_ln_dbh + eps_dbh

    # Clamp DBH to realistic botanical ranges (min 5cm, max 300cm)
    draw_ln_dbh = np.clip(draw_ln_dbh, np.log(5.0), np.log(300.0))

    # 2. DBH -> AGB error draws: ln(AGB) = c0 + c1*ln(DBH) + eps_agb
    base_ln_agb = params.c0 + params.c1 * draw_ln_dbh + params.c2 * (draw_ln_dbh ** 2)
    eps_agb = rng.normal(loc=0.0, scale=params.sigma_agb, size=(n_draws, n_trees))
    draw_ln_agb = base_ln_agb + eps_agb

    # Convert to dry biomass (kg)
    draw_agb = np.exp(draw_ln_agb)

    # 3. Biomass -> Carbon (kg C)
    draw_carbon_trees = draw_agb * params.carbon_fraction

    # Sum across all trees for each draw: shape (n_draws,)
    stand_totals_kg = np.sum(draw_carbon_trees, axis=1)

    mean_kg = float(np.mean(stand_totals_kg))
    low_kg = float(np.quantile(stand_totals_kg, 0.05))   # 5th percentile for 90% interval
    high_kg = float(np.quantile(stand_totals_kg, 0.95))  # 95th percentile

    mean_tonnes = mean_kg / 1000.0
    low_tonnes = low_kg / 1000.0
    high_tonnes = high_kg / 1000.0

    return CarbonEstimateResult(
        mean_carbon_kg=round(mean_kg, 1),
        mean_carbon_tonnes=round(mean_tonnes, 2),
        interval_kg=ConfidenceInterval(low=round(low_kg, 1), high=round(high_kg, 1), confidence_level=0.90),
        interval_tonnes=ConfidenceInterval(low=round(low_tonnes, 2), high=round(high_tonnes, 2), confidence_level=0.90),
        carbon_fraction=params.carbon_fraction,
    )
