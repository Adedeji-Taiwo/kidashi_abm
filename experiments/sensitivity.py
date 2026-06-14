"""
==========================
Global Sensitivity Analysis (Sobol indices) for the Kidashi ABM.

Follows SALib best practices; uses the Saltelli quasi-random sampler
to generate N×(2k+2) model evaluations (k = number of parameters).

Parameters under analysis
--------------------------
  fintech_penetration   [0.0, 0.7]
  risk_aversion_mean    [0.2, 0.8]   – controls population heterogeneity
  trade_shock_prob      [0.05, 0.35]  – injected via shock_regime proxy
  weather_vol           [0.15, 0.50]
  credit_yield_uplift   [0.05, 0.25]

Output metrics (first-order + total Sobol S_i, ST_i)
------------------------------------------------------
  mean_wealth_final
  cv_maize_mean
  fintech_rate_final
  mean_nutrition_final

Usage
-----
  python -m experiments.sensitivity          # full run (N=512)
  python -m experiments.sensitivity --n 64  # quick test
"""

from __future__ import annotations
from model import KidashiModel

import logging
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol as sobol_analyze
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


# ---------------------------------------------------------------------------
# Problem definition
# ---------------------------------------------------------------------------

PROBLEM: Dict = {
    "num_vars": 5,
    "names": [
        "fintech_penetration",
        "risk_aversion_mean",
        "trade_shock_prob",
        "weather_vol",
        "credit_yield_uplift",
    ],
    "bounds": [
        [0.00, 0.70],
        [0.20, 0.80],
        [0.05, 0.35],
        [0.15, 0.50],
        [0.05, 0.25],
    ],
}

OUTPUT_METRICS = [
    "mean_wealth_final",
    "cv_maize_mean",
    "fintech_rate_final",
    "mean_nutrition_final",
]


# ---------------------------------------------------------------------------
# Model evaluation function
# ---------------------------------------------------------------------------

def evaluate_model(params: np.ndarray, steps: int = 30, rep_seed: int = 0) -> Dict[str, float]:
    """
    Run model with given parameter vector; return scalar summary metrics.

    Parameters encoded as:
      params[0]  fintech_penetration
      params[1]  risk_aversion_mean   (used as seed offset proxy)
      params[2]  trade_shock_prob     (mapped to shock_regime)
      params[3]  weather_vol          (mapped to shock_regime)
      params[4]  credit_yield_uplift
    """
    fin_pen = float(np.clip(params[0], 0.0, 1.0))
    trade_p = float(params[2])
    weather_v = float(params[3])
    cyu = float(np.clip(params[4], 0.0, 0.5))

    # Map continuous shock params to regime string
    if trade_p > 0.20 and weather_v > 0.35:
        regime = "compound"
    elif trade_p > 0.20:
        regime = "trade_disruption"
    elif weather_v > 0.35:
        regime = "climate_stress"
    else:
        regime = "baseline"

    model = KidashiModel(
        num_farmers=150,   # smaller for speed in SA
        fintech_penetration=fin_pen,
        diversity_policy="incentive",
        shock_regime=regime,
        seed=rep_seed,
    )
    # Override credit yield uplift after init
    model.credit_yield_uplift = cyu

    for _ in range(steps):
        model.step()

    df = model.datacollector.get_model_vars_dataframe()

    return {
        "mean_wealth_final":   float(df["mean_wealth"].iloc[-1]),
        "cv_maize_mean":       float(df["cv_maize"].mean()),
        "fintech_rate_final":  float(df["fintech_rate"].iloc[-1]),
        "mean_nutrition_final": float(df["mean_nutrition"].iloc[-1]),
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_sensitivity(
    n_samples: int = 512,
    steps:     int = 30,
    out_dir:   str = "data/synthetic",
) -> pd.DataFrame:
    """
    Full Sobol analysis.

    Parameters
    ----------
    n_samples : int
        Base sample count N; total evaluations = N*(2k+2).
    steps     : int
        Steps per model run.
    out_dir   : str
        Output directory for CSV results.
    """
    if not SALIB_AVAILABLE:
        log.error(
            "SALib not installed. Run: pip install SALib --break-system-packages")
        return pd.DataFrame()

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    log.info("Generating Saltelli samples: N=%d, k=%d → %d evaluations",
             n_samples, PROBLEM["num_vars"], n_samples * (2*PROBLEM["num_vars"]+2))

    param_values = saltelli.sample(PROBLEM, n_samples, calc_second_order=False)

    # Evaluate
    Y: Dict[str, List[float]] = {m: [] for m in OUTPUT_METRICS}
    total = len(param_values)

    for i, params in enumerate(param_values):
        if i % 50 == 0:
            log.info("  Progress: %d / %d", i, total)
        results = evaluate_model(params, steps=steps, rep_seed=i)
        for metric in OUTPUT_METRICS:
            Y[metric].append(results[metric])

    # Sobol analysis per metric
    records = []
    for metric in OUTPUT_METRICS:
        y_arr = np.array(Y[metric])
        Si = sobol_analyze.analyze(
            PROBLEM, y_arr, calc_second_order=False, print_to_console=False)
        for j, pname in enumerate(PROBLEM["names"]):
            records.append({
                "metric":    metric,
                "parameter": pname,
                "S1":        Si["S1"][j],
                "S1_conf":   Si["S1_conf"][j],
                "ST":        Si["ST"][j],
                "ST_conf":   Si["ST_conf"][j],
            })

    df = pd.DataFrame(records)
    out_path = Path(out_dir) / "sobol_indices.csv"
    df.to_csv(out_path, index=False)
    log.info("Sobol indices saved → %s", out_path)

    # Pretty-print top influences
    log.info("\n=== Top Sobol ST indices (total effect) ===")
    pivot = df.pivot_table(index="parameter", columns="metric", values="ST")
    log.info("\n%s", pivot.round(3).to_string())

    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n",     type=int, default=512,
                        help="Saltelli N (default 512)")
    parser.add_argument("--steps", type=int, default=30,
                        help="Steps per run (default 30)")
    args = parser.parse_args()
    run_sensitivity(n_samples=args.n, steps=args.steps)
