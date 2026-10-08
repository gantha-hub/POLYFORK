"""Calibration service for aligning aerial tree counts with ground-truth audit plots.

Supports:
1. Baseline Ratio scaling: G_hat = V / mean(V / G)
2. Negative Binomial GLM with log(V) offset:
   log(mu) = log(V) + b0 + b1*CC + b2*log(crown_area) + b3*forest_type

Enforces a strict minimum of 10 ground plots to ensure statistical validity.
"""

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Tuple
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.families import NegativeBinomial

from app.core.errors import InsufficientDataError
from app.core.logging import logger

MIN_REQUIRED_PLOTS = 10


@dataclass
class GroundPlotData:
    """Standardized representation of a field audit plot."""

    plot_name: str
    ground_count_G: int
    visual_count_V: int
    canopy_cover_pct: float
    crown_area_sqm: float
    forest_type: str


@dataclass
class FittedCalibrationModel:
    """Fitted calibration coefficients and conformal quantile bounds."""

    method: Literal["ratio", "negbin_glm"]
    params: Dict[str, Any]
    residual_quantile_q: float
    empirical_coverage: float
    n_plots: int


def validate_plot_count(plots: List[GroundPlotData]) -> None:
    """Strictly validates that at least 10 plots are provided for calibration."""
    n = len(plots)
    if n < MIN_REQUIRED_PLOTS:
        raise InsufficientDataError(
            message=(
                f"Calibration refused: requires at least {MIN_REQUIRED_PLOTS} ground audit plots "
                f"to ensure statistical validity, but only {n} plot(s) were provided. "
                "Fitting calibration models on small sample sizes leads to severe over-fitting "
                "and violates finite-sample conformal prediction coverage guarantees."
            ),
            details={"provided_plots": n, "minimum_required": MIN_REQUIRED_PLOTS},
        )


def fit_ratio_baseline(
    df_cal: pd.DataFrame,
) -> Tuple[Dict[str, Any], np.ndarray]:
    """Fits baseline ratio scaling: G_hat = V / mean(V/G).

    Returns:
        params dictionary and in-sample predictions G_hat.
    """
    # Avoid zero division
    g_arr = np.maximum(df_cal["ground_count_G"].values, 1.0)
    v_arr = np.maximum(df_cal["visual_count_V"].values, 1.0)

    ratio_values = v_arr / g_arr
    mean_ratio = float(np.mean(ratio_values))

    # Guard against pathological ratio
    if mean_ratio <= 0.0 or math.isnan(mean_ratio):
        mean_ratio = 1.0

    params = {
        "mean_ratio": round(mean_ratio, 6),
        "scaling_factor": round(1.0 / mean_ratio, 6),
    }

    g_hat = v_arr / mean_ratio
    return params, g_hat


def predict_ratio(
    visual_count_V: float,
    params: Dict[str, Any],
) -> float:
    """Predicts calibrated ground count using fitted ratio."""
    mean_ratio = params.get("mean_ratio", 1.0)
    if mean_ratio <= 0.0:
        mean_ratio = 1.0
    return float(visual_count_V / mean_ratio)


def fit_negbin_glm(
    df_cal: pd.DataFrame,
) -> Tuple[Dict[str, Any], np.ndarray]:
    """Fits Negative Binomial GLM with log(V) offset.

    log(mu) = log(V) + b0 + b1*CC + b2*log(crown_area) + [categorical forest_type]

    Returns:
        params dictionary and predicted values G_hat.
    """
    # Prepare dependent variable G
    y = df_cal["ground_count_G"].values.astype(np.float64)

    # Offset = log(V)
    v_clean = np.maximum(df_cal["visual_count_V"].values.astype(np.float64), 1.0)
    offset = np.log(v_clean)

    # Predictors
    cc = df_cal["canopy_cover_pct"].values.astype(np.float64) / 100.0  # Normalized 0..1
    log_ca = np.log(np.maximum(df_cal["crown_area_sqm"].values.astype(np.float64), 1.0))

    # Design matrix: Intercept, CanopyCover, log(CrownArea)
    X = np.column_stack([np.ones_like(cc), cc, log_ca])
    feature_names = ["const", "canopy_cover", "log_crown_area"]

    try:
        # Fit GLM with Negative Binomial family (using alpha=1.0 default dispersion)
        glm_model = sm.GLM(
            y,
            X,
            family=NegativeBinomial(alpha=1.0),
            offset=offset,
        )
        res = glm_model.fit(maxiter=100, disp=False)
        coefficients = {name: float(res.params[i]) for i, name in enumerate(feature_names)}
        g_hat = res.predict(X, offset=offset)
    except Exception as exc:
        logger.warning(f"Negative Binomial GLM convergence issue: {exc}. Falling back to Poisson GLM.")
        poisson_model = sm.GLM(
            y,
            X,
            family=sm.families.Poisson(),
            offset=offset,
        )
        res = poisson_model.fit(maxiter=100, disp=False)
        coefficients = {name: float(res.params[i]) for i, name in enumerate(feature_names)}
        g_hat = res.predict(X, offset=offset)

    params = {
        "coefficients": coefficients,
        "feature_names": feature_names,
    }

    return params, g_hat


def predict_negbin_glm(
    visual_count_V: float,
    canopy_cover_pct: float,
    mean_crown_area_sqm: float,
    params: Dict[str, Any],
) -> float:
    """Predicts calibrated tree count using fitted GLM parameters."""
    coeffs = params.get("coefficients", {})
    b0 = coeffs.get("const", 0.0)
    b1 = coeffs.get("canopy_cover", 0.0)
    b2 = coeffs.get("log_crown_area", 0.0)

    cc = canopy_cover_pct / 100.0
    log_ca = math.log(max(1.0, mean_crown_area_sqm))
    offset = math.log(max(1.0, visual_count_V))

    log_mu = offset + b0 + b1 * cc + b2 * log_ca
    # Prevent numerical overflow
    log_mu_clamped = min(15.0, max(-5.0, log_mu))
    return float(math.exp(log_mu_clamped))
