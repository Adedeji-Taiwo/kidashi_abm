"""
========================
Batch experiment runner for the Kidashi ABM.

Scenarios
---------
Four policy × shock combinations, each replicated REPS times:

  S1  Baseline         – no fintech, no diversity policy, mild shocks
  S2  Fintech only     – 40% credit penetration, no diversity policy
  S3  Diversity only   – no fintech, diversity incentive policy
  S4  Combined         – fintech + diversity incentive
  S5  Compound shock   – fintech + diversity, compound shock regime
  S6  Trade disruption – fintech + diversity, trade disruption regime
  S7  Climate stress   – fintech + diversity, climate stress regime

Results saved to data/synthetic/batch_results.csv for analysis/.

Usage
-----
  python -m experiments.batch_run          # full run (≈3-5 min)
  python -m experiments.batch_run --quick  # 2 reps × 20 steps for CI testing
"""

from __future__ import annotations
from model import KidashiModel

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure project root on path when run as script
sys.path.insert(0, str(Path(__file__).parent.parent))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "scenario_id":         "S1_baseline",
        "label":               "No Fintech / No Policy / Mild Shocks",
        "fintech_penetration": 0.00,
        "diversity_policy":    "none",
        "shock_regime":        "baseline",
    },
    {
        "scenario_id":         "S2_fintech_only",
        "label":               "Fintech (40%) / No Policy / Mild Shocks",
        "fintech_penetration": 0.40,
        "diversity_policy":    "none",
        "shock_regime":        "baseline",
    },
    {
        "scenario_id":         "S3_diversity_only",
        "label":               "No Fintech / Diversity Incentive / Mild Shocks",
        "fintech_penetration": 0.00,
        "diversity_policy":    "incentive",
        "shock_regime":        "baseline",
    },
    {
        "scenario_id":         "S4_combined",
        "label":               "Fintech (40%) + Diversity Incentive / Mild Shocks",
        "fintech_penetration": 0.40,
        "diversity_policy":    "incentive",
        "shock_regime":        "baseline",
    },
    {
        "scenario_id":         "S5_compound_shock",
        "label":               "Fintech + Diversity / Compound Shock",
        "fintech_penetration": 0.40,
        "diversity_policy":    "incentive",
        "shock_regime":        "compound",
    },
    {
        "scenario_id":         "S6_trade_disruption",
        "label":               "Fintech + Diversity / Trade Disruption",
        "fintech_penetration": 0.40,
        "diversity_policy":    "incentive",
        "shock_regime":        "trade_disruption",
    },
    {
        "scenario_id":         "S7_climate_stress",
        "label":               "Fintech + Diversity / Climate Stress",
        "fintech_penetration": 0.40,
        "diversity_policy":    "incentive",
        "shock_regime":        "climate_stress",
    },
]

# Fintech penetration sweep (used in sweep analysis)
PENETRATION_LEVELS = [0.00, 0.10, 0.20, 0.30, 0.40, 0.55, 0.70]


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_single(
    scenario_params: dict,
    steps: int,
    rep: int,
    num_farmers: int = 300,
) -> pd.DataFrame:
    """
    Run one model instance and return its model-level time series as a
    DataFrame augmented with scenario metadata and rep index.
    """
    seed = rep * 1000 + hash(scenario_params["scenario_id"]) % 1000

    model = KidashiModel(
        num_farmers=num_farmers,
        fintech_penetration=scenario_params["fintech_penetration"],
        diversity_policy=scenario_params["diversity_policy"],
        shock_regime=scenario_params["shock_regime"],
        seed=seed % (2**31),
    )

    for _ in range(steps):
        model.step()

    df = model.datacollector.get_model_vars_dataframe().reset_index(drop=True)
    df["rep"] = rep
    df["scenario_id"] = scenario_params["scenario_id"]
    df["label"] = scenario_params["label"]
    df["fintech_pen"] = scenario_params["fintech_penetration"]
    df["div_policy"] = scenario_params["diversity_policy"]
    df["shock_regime"] = scenario_params["shock_regime"]
    return df


def run_batch(
    steps:       int = 40,
    reps:        int = 5,
    num_farmers: int = 300,
    out_dir:     str = "data/synthetic",
) -> pd.DataFrame:
    """
    Run all scenarios × reps and save consolidated CSV.

    Parameters
    ----------
    steps       : simulation steps per run (≈ seasons)
    reps        : independent replications per scenario
    num_farmers : agents per run
    out_dir     : output directory for CSV
    """
    os.makedirs(out_dir, exist_ok=True)
    all_dfs = []
    total = len(SCENARIOS) * reps

    for s_idx, scenario in enumerate(SCENARIOS):
        for rep in range(reps):
            run_num = s_idx * reps + rep + 1
            log.info(
                "[%d/%d] %s | rep=%d",
                run_num, total, scenario["scenario_id"], rep
            )
            df = run_single(scenario, steps=steps, rep=rep,
                            num_farmers=num_farmers)
            all_dfs.append(df)

    results = pd.concat(all_dfs, ignore_index=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(out_dir) / f"batch_results_{ts}.csv"
    results.to_csv(out_path, index=False)
    log.info("Results saved → %s  (%d rows)", out_path, len(results))

    # Also write latest alias for downstream analysis
    latest_path = Path(out_dir) / "batch_results_latest.csv"
    results.to_csv(latest_path, index=False)

    return results


def run_penetration_sweep(
    steps:       int = 40,
    reps:        int = 5,
    num_farmers: int = 300,
    out_dir:     str = "data/synthetic",
) -> pd.DataFrame:
    """
    Sweep fintech penetration rate across PENETRATION_LEVELS under compound
    shock to map the dose-response curve for resilience metrics.
    """
    os.makedirs(out_dir, exist_ok=True)
    all_dfs = []

    for pen in PENETRATION_LEVELS:
        for rep in range(reps):
            log.info("Penetration sweep | pen=%.2f | rep=%d", pen, rep)
            params = {
                "scenario_id":         f"sweep_pen_{pen:.2f}",
                "label":               f"Penetration={pen:.0%}",
                "fintech_penetration": pen,
                "diversity_policy":    "incentive",
                "shock_regime":        "compound",
            }
            df = run_single(params, steps=steps, rep=rep,
                            num_farmers=num_farmers)
            all_dfs.append(df)

    results = pd.concat(all_dfs, ignore_index=True)
    out_path = Path(out_dir) / "penetration_sweep_latest.csv"
    results.to_csv(out_path, index=False)
    log.info("Penetration sweep saved → %s", out_path)
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Kidashi ABM Batch Runner")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 2 reps × 20 steps (CI / demo)",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run fintech penetration sweep instead of scenario batch",
    )
    parser.add_argument(
        "--farmers",
        type=int,
        default=300,
        help="Number of farmer agents per run (default: 300)",
    )
    args = parser.parse_args()

    if args.quick:
        steps, reps = 20, 2
        log.info("Quick mode: %d steps × %d reps", steps, reps)
    else:
        steps, reps = 40, 5

    if args.sweep:
        run_penetration_sweep(steps=steps, reps=reps, num_farmers=args.farmers)
    else:
        run_batch(steps=steps, reps=reps, num_farmers=args.farmers)
