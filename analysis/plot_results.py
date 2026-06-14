"""
========================
Kidashi ABM – Plot Results
========================

Figures produced
----------------
  Fig 1  – Farmgate price dynamics under scenarios (maize, mean ± 1 SD band)
  Fig 2  – Price volatility (CV) across scenarios, boxplot
  Fig 3  – Mean farmer wealth trajectory (all scenarios)
  Fig 4  – Gini coefficient of wealth over time (equity lens)
  Fig 5  – Food security: % households above nutrition threshold
  Fig 6  – Fintech penetration vs. price CV (dose-response scatter)
  Fig 7  – Compound shock resilience: wealth recovery curves
  Fig 8  – Diversity index distribution by scenario (violin)

All figures saved to analysis/figures/.

Usage
-----
  python -m analysis.plot_results                       # uses latest CSV
  python -m analysis.plot_results --csv path/to/file.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# ---------------------------------------------------------------------------
# Aesthetics — minimal, academic palette
# ---------------------------------------------------------------------------

PALETTE = {
    "S1_baseline":         "#1f77b4",   # blue
    "S2_fintech_only":     "#ff7f0e",   # orange
    "S3_diversity_only":   "#2ca02c",   # green
    "S4_combined":         "#d62728",   # red
    "S5_compound_shock":   "#9467bd",   # purple
    "S6_trade_disruption": "#8c564b",   # brown
    "S7_climate_stress":   "#e377c2",   # pink
}

SCENARIO_LABELS = {
    "S1_baseline":         "Baseline",
    "S2_fintech_only":     "Fintech (40%)",
    "S3_diversity_only":   "Diversity Incentive",
    "S4_combined":         "Fintech + Diversity",
    "S5_compound_shock":   "Combined + Compound Shock",
    "S6_trade_disruption": "Combined + Trade Disruption",
    "S7_climate_stress":   "Combined + Climate Stress",
}

mpl.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        10,
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "figure.dpi":       150,
    "savefig.dpi":      200,
    "savefig.bbox":     "tight",
})


# ---------------------------------------------------------------------------
# Helper: load data
# ---------------------------------------------------------------------------

def load_results(csv_path: str | None = None) -> pd.DataFrame:
    if csv_path and Path(csv_path).exists():
        return pd.read_csv(csv_path)
    default = Path("data/synthetic/batch_results_latest.csv")
    if default.exists():
        return pd.read_csv(default)
    raise FileNotFoundError(
        "No batch results found. Run: python -m experiments.batch_run --quick"
    )


def agg_mean_sd(df: pd.DataFrame, y_col: str) -> pd.DataFrame:
    """Aggregate over reps: mean ± std per (scenario, step)."""
    return (
        df.groupby(["scenario_id", "step"])[y_col]
        .agg(["mean", "std"])
        .reset_index()
    )


# ---------------------------------------------------------------------------
# Individual figure functions
# ---------------------------------------------------------------------------

def fig1_price_dynamics(df: pd.DataFrame, out_dir: Path) -> None:
    """Maize farmgate price: mean trajectory + uncertainty band."""
    agg = agg_mean_sd(df, "price_maize")
    fig, ax = plt.subplots(figsize=(8, 4.5))

    for sid, gdf in agg.groupby("scenario_id"):
        color = PALETTE.get(sid, "#888")
        label = SCENARIO_LABELS.get(sid, sid)
        ax.plot(gdf["step"], gdf["mean"], color=color, label=label, lw=1.8)
        ax.fill_between(
            gdf["step"],
            gdf["mean"] - gdf["std"].fillna(0),
            gdf["mean"] + gdf["std"].fillna(0),
            color=color, alpha=0.10,
        )

    ax.set_xlabel("Simulation Step (Season)")
    ax.set_ylabel("Farmgate Price – Maize (NGN/MT)")
    ax.set_title(
        "Fig 1  Maize Farmgate Price Dynamics under Policy × Shock Scenarios")
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "fig1_price_dynamics_maize.png")
    plt.close(fig)
    log.info("Fig 1 saved.")


def fig2_price_volatility(df: pd.DataFrame, out_dir: Path) -> None:
    """CV of maize price: boxplot across all steps per scenario."""
    fig, ax = plt.subplots(figsize=(9, 4.5))

    data_by_scenario = [
        df[df["scenario_id"] == sid]["cv_maize"].dropna().values
        for sid in SCENARIO_LABELS
        if sid in df["scenario_id"].values
    ]
    labels = [
        SCENARIO_LABELS[sid]
        for sid in SCENARIO_LABELS
        if sid in df["scenario_id"].values
    ]

    bp = ax.boxplot(
        data_by_scenario,
        patch_artist=True,
        medianprops=dict(color="black", lw=2),
        whiskerprops=dict(lw=1),
        capprops=dict(lw=1),
    )
    colors = [PALETTE.get(sid, "#888")
              for sid in SCENARIO_LABELS if sid in df["scenario_id"].values]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)

    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Coefficient of Variation (CV) – Maize Price")
    ax.set_title("Fig 2  Maize Price Volatility by Scenario")
    fig.tight_layout()
    fig.savefig(out_dir / "fig2_price_volatility_boxplot.png")
    plt.close(fig)
    log.info("Fig 2 saved.")


def fig3_wealth_trajectory(df: pd.DataFrame, out_dir: Path) -> None:
    """Mean farmer wealth over time, all scenarios."""
    agg = agg_mean_sd(df, "mean_wealth")
    fig, ax = plt.subplots(figsize=(8, 4.5))

    for sid, gdf in agg.groupby("scenario_id"):
        ax.plot(
            gdf["step"],
            gdf["mean"] / 1e6,
            color=PALETTE.get(sid, "#888"),
            label=SCENARIO_LABELS.get(sid, sid),
            lw=1.8,
        )

    ax.set_xlabel("Simulation Step (Season)")
    ax.set_ylabel("Mean Farmer Wealth (Million NGN)")
    ax.set_title("Fig 3  Wealth Accumulation Trajectories")
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "fig3_wealth_trajectories.png")
    plt.close(fig)
    log.info("Fig 3 saved.")


def fig4_gini(df: pd.DataFrame, out_dir: Path) -> None:
    """Gini coefficient of wealth (equity / inequality lens)."""
    agg = agg_mean_sd(df, "gini_wealth")
    fig, ax = plt.subplots(figsize=(8, 4))

    for sid, gdf in agg.groupby("scenario_id"):
        ax.plot(
            gdf["step"],
            gdf["mean"],
            color=PALETTE.get(sid, "#888"),
            label=SCENARIO_LABELS.get(sid, sid),
            lw=1.8,
        )
        ax.fill_between(
            gdf["step"],
            (gdf["mean"] - gdf["std"].fillna(0)).clip(0),
            (gdf["mean"] + gdf["std"].fillna(0)).clip(0, 1),
            color=PALETTE.get(sid, "#888"), alpha=0.10,
        )

    ax.set_xlabel("Simulation Step (Season)")
    ax.set_ylabel("Gini Coefficient (Wealth)")
    ax.set_title("Fig 4  Wealth Inequality (Gini) over Time")
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "fig4_gini_wealth.png")
    plt.close(fig)
    log.info("Fig 4 saved.")


def fig5_food_security(df: pd.DataFrame, out_dir: Path) -> None:
    """% farmers above nutrition threshold per scenario × step."""
    agg = agg_mean_sd(df, "pct_food_secure")
    fig, ax = plt.subplots(figsize=(8, 4.5))

    for sid, gdf in agg.groupby("scenario_id"):
        ax.plot(
            gdf["step"],
            gdf["mean"] * 100,
            color=PALETTE.get(sid, "#888"),
            label=SCENARIO_LABELS.get(sid, sid),
            lw=1.8,
        )

    ax.axhline(80, color="grey", lw=1, ls="--", label="80% threshold")
    ax.set_xlabel("Simulation Step (Season)")
    ax.set_ylabel("% Farmers Food-Secure (Nutrition ≥ 0.8)")
    ax.set_title("Fig 5  Food Security Rate by Scenario")
    ax.set_ylim(0, 105)
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "fig5_food_security.png")
    plt.close(fig)
    log.info("Fig 5 saved.")


def fig6_dose_response(df: pd.DataFrame, out_dir: Path) -> None:
    """
    Fintech penetration rate vs. price CV (dose-response).
    Uses end-of-run values for each rep × scenario.
    """
    last_step = df.groupby(["scenario_id", "rep"])["step"].max().reset_index()
    terminal = df.merge(last_step, on=["scenario_id", "rep", "step"])

    fig, ax = plt.subplots(figsize=(6, 5))
    scatter = ax.scatter(
        terminal["fintech_rate"] * 100,
        terminal["cv_maize"] * 100,
        c=[list(PALETTE.values())[i % len(PALETTE)]
           for i, sid in enumerate(terminal["scenario_id"])],
        alpha=0.65,
        s=40,
        edgecolors="none",
    )

    # Trend line
    x = terminal["fintech_rate"].values
    y = terminal["cv_maize"].values
    if len(x) > 2:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs * 100, p(xs) * 100, "k--", lw=1.2, label="OLS trend")

    ax.set_xlabel("Fintech Credit Penetration (%)")
    ax.set_ylabel("Maize Price Volatility – CV (%)")
    ax.set_title(
        "Fig 6  Dose-Response: Fintech Penetration → Price Volatility")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig6_dose_response.png")
    plt.close(fig)
    log.info("Fig 6 saved.")


def fig7_compound_shock_recovery(df: pd.DataFrame, out_dir: Path) -> None:
    """
    Wealth recovery after compound shock events.
    Compare S4 (combined, mild shocks) vs. S5 (combined, compound shock).
    """
    focus = ["S4_combined", "S5_compound_shock"]
    sub = df[df["scenario_id"].isin(focus)]
    if sub.empty:
        log.warning("Fig 7: S4/S5 not in data, skipping.")
        return

    agg = agg_mean_sd(sub, "mean_wealth")
    fig, ax = plt.subplots(figsize=(8, 4.5))

    for sid, gdf in agg.groupby("scenario_id"):
        ax.plot(
            gdf["step"],
            gdf["mean"] / 1e6,
            color=PALETTE.get(sid, "#888"),
            label=SCENARIO_LABELS.get(sid, sid),
            lw=2,
        )
        ax.fill_between(
            gdf["step"],
            (gdf["mean"] - gdf["std"].fillna(0)) / 1e6,
            (gdf["mean"] + gdf["std"].fillna(0)) / 1e6,
            color=PALETTE.get(sid, "#888"), alpha=0.15,
        )

    ax.set_xlabel("Simulation Step (Season)")
    ax.set_ylabel("Mean Wealth (Million NGN)")
    ax.set_title(
        "Fig 7  Wealth Resilience: Fintech+Diversity under Compound Shock")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "fig7_compound_shock_recovery.png")
    plt.close(fig)
    log.info("Fig 7 saved.")


def fig8_diversity_violin(df: pd.DataFrame, out_dir: Path) -> None:
    """Violin plot of diversity index at final step per scenario."""
    last_step = df.groupby(["scenario_id", "rep"])["step"].max().reset_index()
    terminal = df.merge(last_step, on=["scenario_id", "rep", "step"])

    sids = [s for s in SCENARIO_LABELS if s in terminal["scenario_id"].values]
    data = [terminal[terminal["scenario_id"] == s]["mean_diversity_index"].dropna().values
            for s in sids]
    labels = [SCENARIO_LABELS[s] for s in sids]
    colors = [PALETTE.get(s, "#888") for s in sids]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    parts = ax.violinplot(
        data,
        showmedians=True,
        showextrema=True,
    )
    for pc, color in zip(parts["bodies"], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.65)

    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Shannon Diversity Index (H')")
    ax.set_title("Fig 8  Crop Portfolio Diversity at End of Simulation")
    fig.tight_layout()
    fig.savefig(out_dir / "fig8_diversity_violin.png")
    plt.close(fig)
    log.info("Fig 8 saved.")


# ---------------------------------------------------------------------------
# Summary statistics table
# ---------------------------------------------------------------------------

def summary_table(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """
    Terminal-step summary statistics across scenarios.
    Saved as CSV (can be formatted as LaTeX with df.to_latex()).
    """
    last_step = df.groupby(["scenario_id", "rep"])["step"].max().reset_index()
    terminal = df.merge(last_step, on=["scenario_id", "rep", "step"])

    metrics = [
        "mean_wealth", "gini_wealth", "cv_maize", "cv_tomato",
        "fintech_rate", "mean_diversity_index", "pct_food_secure",
        "mean_nutrition",
    ]

    rows = []
    for sid in SCENARIO_LABELS:
        sub = terminal[terminal["scenario_id"] == sid]
        if sub.empty:
            continue
        row = {"scenario": SCENARIO_LABELS[sid]}
        for m in metrics:
            if m in sub.columns:
                row[f"{m}_mean"] = sub[m].mean()
                row[f"{m}_sd"] = sub[m].std()
        rows.append(row)

    tbl = pd.DataFrame(rows)
    out_path = out_dir / "summary_table.csv"
    tbl.to_csv(out_path, index=False)
    log.info("Summary table saved → %s", out_path)
    return tbl


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(csv_path: str | None = None) -> None:
    out_dir = Path("analysis/figures")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_results(csv_path)
    log.info("Loaded %d rows from batch results.", len(df))

    fig1_price_dynamics(df, out_dir)
    fig2_price_volatility(df, out_dir)
    fig3_wealth_trajectory(df, out_dir)
    fig4_gini(df, out_dir)
    fig5_food_security(df, out_dir)
    fig6_dose_response(df, out_dir)
    fig7_compound_shock_recovery(df, out_dir)
    fig8_diversity_violin(df, out_dir)
    summary_table(df, out_dir)

    log.info("All figures saved to %s/", out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=None,
                        help="Path to batch_results CSV")
    args = parser.parse_args()
    main(args.csv)
