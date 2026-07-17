# KidashiABM
## Agent-Based Modelling of Fintech-Led Liquidity Provision and Farmgate Price Resilience in Nigerian Staple Value Chains

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Mesa 3.5](https://img.shields.io/badge/mesa-3.5-green.svg)](https://mesa.readthedocs.io/)
[![Tests](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-Streamlit-FF4B4B.svg)](https://kidashiabm.streamlit.app/)

**Live showcase & interactive simulator:** [kidashiabm.streamlit.app](https://kidashiabm.streamlit.app/) - configure a scenario and run KidashiModel from the browser, no installation required.

---

### Overview

This repository contains an Agent-Based Model (ABM) developed to investigate a central question at the intersection of fintech innovation and food systems resilience:

> **How do fintech-led liquidity provision and agricultural production diversity jointly shape farmgate price resilience and smallholder welfare under domestic supply shocks and international market disruptions?**

The model is directly informed by operational experience at **XchangeBox Solutions Ltd.** (Kano/Northern Nigeria), where the *Kidashi* trust-circle credit product and *Farm-to-Factory* invoice financing demonstrably reduced smallholder payment cycles from 60–90 days to under 72 hours. The *TomatoPro* stochastic optimisation tool provided calibration anchors for post-harvest spoilage reduction (55%) and profit uplift (18.6%) under financial liquidity.

---

### Research Design

#### Agents

| Agent | Count | Key Behaviours |
|-------|-------|----------------|
| `Farmer` | 100–1000 | Adaptive mean-variance portfolio allocation (maize/sorghum/tomato); stochastic production with weather-correlated shocks; multi-channel sales with distress-discount mechanism |
| `FintechProvider` | 1 | Trust-circle credit scoring; Kidashi/Farm-to-Factory disbursement logic; Portfolio-at-Risk (PAR30) tracking |
| `Trader` | 5–20 | Aggregator/processor procurement; TomatoPro-style two-scenario spoilage; export-channel price transmission |

#### Market Mechanism

Farmgate prices form **endogenously** via an inverse supply function modulated by:
- Aggregate production across all farmer agents
- An exogenous **trade shock multiplier** (Europe-linked demand disruptions)
- Fintech-enabled reduction in distress-sale discounts

#### Shock Regimes

| Regime | Weather Volatility | Trade Shock Probability | Magnitude |
|--------|--------------------|-------------------------|-----------|
| `baseline` | Low (σ=0.20) | Low (8%) | ±15% |
| `climate_stress` | High (σ=0.45) | Low (8%) | ±15% |
| `trade_disruption` | Low (σ=0.20) | High (25%) | ±35% |
| `compound` | High (σ=0.45) | High (25%) | ±35% |

#### Diversity Policies

- **`none`** — No intervention; portfolio shaped by expected utility alone.
- **`incentive`** — Diversified farmers (Shannon H' above threshold) receive a 5% price premium.
- **`mandate`** — Minimum crop share floor raised to equal weighting across all three crops.

---

### Key Model Features

- **Shannon Diversity Index (H')** computed per farmer at each step; used as both a policy lever and a credit-scoring signal.
- **Gini coefficient** of farmer wealth collected by Mesa DataCollector for distributional analysis.
- **Nutrition proxy score** (caloric adequacy) derived from farm income relative to a 5-person household subsistence threshold (WFP 2023 estimate for Northern Nigeria).
- **Correlated weather shocks** across farmers via a shared z-score (ρ = 0.60), with idiosyncratic noise, replicating the spatial structure of CHIRPS/ERA5 rainfall fields used in the author's subnational yield forecasting work.
- **Full reproducibility**: all runs seeded; identical seeds produce bit-identical results.

---

### Repository Structure

```
kidashi_abm/
│
├── model/
│   ├── __init__.py
│   ├── agents.py          # Farmer, FintechProvider, Trader agents
│   └── model.py           # KidashiModel: grid, shocks, market, DataCollector
│
├── components/
│   ├── __init__.py
│   └── live_figure.py     # FIG 01 -- client-side live canvas animation
│
├── experiments/
│   ├── __init__.py
│   ├── batch_run.py       # 7-scenario batch runner; penetration sweep
│   └── sensitivity.py     # Sobol global sensitivity analysis (SALib)
│
├── analysis/
│   ├── __init__.py
│   └── plot_results.py    # 8 publication-quality figures + summary table
│
├── tests/
│   ├── __init__.py
│   └── test_model.py      # 39 unit + integration tests (pytest)
│
├── data/
│   └── synthetic/         # Batch run CSVs (generated at runtime)
│
├── analysis/figures/      # PNG figures (generated at runtime)
├── results/                # Demo run outputs
│
├── app.py                  # KidashiSim showcase + interactive Streamlit simulator
├── run_model.py             # Single-scenario CLI entry point
├── KidashiSim_User_Manual.pdf
├── requirements.txt
├── .gitignore
└── README.md
```

---

### Quick Start

Prefer not to install anything? The [hosted simulator](https://kidashiabm.streamlit.app/) runs the same model in your browser - open the Case Studies page and click **Launch simulator** on the live Nigeria card.

```bash
# 1. Clone and install
git clone https://github.com/yourusername/kidashi_abm.git
cd kidashi_abm
pip install -r requirements.txt

# 2. Run a single demo (30 seasons, 300 farmers, 40% fintech penetration)
python run_model.py

# 3. Custom scenario: compound shock + diversity incentive
python run_model.py --steps 40 --farmers 500 --fintech 0.5 \
                    --policy incentive --shock compound

# 4. Run all 7 policy × shock scenarios (quick: 2 reps × 20 steps)
python -m experiments.batch_run --quick

# 5. Generate figures from batch results
python -m analysis.plot_results

# 6. Run test suite
pytest tests/ -v

# 7. Or launch the showcase + simulator locally
streamlit run app.py
```

**Expected quick-start output (run_model.py):**
```
Step  5 | P_maize=298,000 NGN | wealth=44.2M | fintech=21.5% | H'=0.639
Step 10 | P_maize=295,000 NGN | wealth=95.4M | fintech=28.0% | H'=0.645
...
╔══════════════════════════════════════════════════════╗
║  Mean farmer wealth              208.40M NGN         ║
║  Gini (wealth inequality)        0.329               ║
║  Fintech penetration (mean)      16.8%               ║
║  Shannon diversity H' (mean)     0.639               ║
╚══════════════════════════════════════════════════════╝
```

---

### Experiment Scenarios

| ID | Label | Fintech | Policy | Shock |
|----|-------|---------|--------|-------|
| S1 | Baseline | 0% | None | Baseline |
| S2 | Fintech only | 40% | None | Baseline |
| S3 | Diversity only | 0% | Incentive | Baseline |
| S4 | Combined | 40% | Incentive | Baseline |
| S5 | Compound shock | 40% | Incentive | Compound |
| S6 | Trade disruption | 40% | Incentive | Trade Disruption |
| S7 | Climate stress | 40% | Incentive | Climate Stress |

Each scenario runs with N replications (default: 5) using different RNG seeds. The **penetration sweep** (`--sweep`) varies credit uptake from 0% to 70% under compound shocks, tracing the dose-response curve for price volatility reduction.

---

### Sensitivity Analysis

Global sensitivity analysis uses the **Saltelli sampler** and **Sobol first-order (S1) and total-effect (ST) indices** via [SALib](https://salib.readthedocs.io/):

```bash
# Full run (N=512, ~6000 model evaluations)
python -m experiments.sensitivity --n 512

# Quick test (N=64)
python -m experiments.sensitivity --n 64
```

Parameters analysed: `fintech_penetration`, `risk_aversion_mean`, `trade_shock_prob`, `weather_vol`, `credit_yield_uplift`.

Output metrics: mean terminal wealth, maize price CV, fintech uptake rate, nutrition score.

---

### Calibration & Data Sources

| Parameter | Value | Source |
|-----------|-------|--------|
| Maize farmgate price baseline | 310,000 NGN/MT | CBN / NBS Commodity Price Data (2023) |
| Tomato farmgate price baseline | 420,000 NGN/MT | CBN / NBS (2023) |
| Maize yield range | 1.2–3.5 MT/ha | IITA on-farm trial data (BASICS-II programme) |
| Tomato spoilage (no fintech) | 35% | TomatoPro baseline (XchangeBox, 2025) |
| Spoilage reduction (with fintech) | 55% | TomatoPro validated result (SUS 82.4) |
| Credit yield uplift | 12% | Estimated from 18.6% profit uplift, TomatoPro |
| Payment cycle (no fintech) | 75 days | XchangeBox field data (Kano/Jigawa, 2025) |
| Payment cycle (with fintech) | 2.5 days | Kidashi product (<72 hours) |
| Farm size distribution | Log-normal (μ=0.7, σ=0.5 ha) | NBS Agricultural Survey (2021) |
| Initial wealth distribution | Log-normal (μ=11.5, σ=0.8 NGN) | Calibrated to NBS household data |
| Weather-yield correlation (ρ) | 0.60 | ERA5-Land/CHIRPS yield |
| Subsistence threshold | 180,000 NGN/season | WFP Northern Nigeria (2023) |

All parameters representing XchangeBox operational data are anonymised and used under professional confidentiality; only aggregate/published values are reported here.

---


### Author

**Taiwo Adedeji Michael**
M.Sc. Agribusiness and Innovation, Mohammed VI Polytechnic University (UM6P)
Agri-Food Systems & Financial Inclusion Specialist, XchangeBox Solutions Ltd.

---

### License

MIT License. See [LICENSE](LICENSE) for details.

---

### Acknowledgements

Methodological inspiration: Mesa framework (Project Mesa), SALib sensitivity toolkit, and the agent-based food systems modelling literature (AgriPoliS, CRAFTY, APSIM-linked ABMs). Field calibration grounded in XchangeBox Solutions operational product data.