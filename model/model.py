"""
========
Core Mesa 3 simulation model.

Research Question (B03-aligned)
--------------------------------
How do (i) fintech-led liquidity provision and (ii) agricultural production
diversity jointly shape the resilience of farmgate prices and smallholder
incomes to domestic supply shocks and international market disruptions in
Nigerian staple value chains (maize, sorghum, tomato)?

Model Architecture
------------------
  Agents  : Farmer × N, FintechProvider × 1, Trader × T
  Space   : NetworkGrid — regional nodes (North, Kano, South, Export)
            connected by stylised trade corridors
  Time    : Discrete steps ≈ one agricultural season (~3 months)
  Market  : Endogenous farmgate price via inverse supply function;
            trade shock applied exogenously each step
  Shocks  : Weather (correlated across farmers via shared z-score),
            domestic supply shock, Europe-linked trade demand shock

Key Parameters (sweep targets for experiments/)
-------------------------------------------------
  num_farmers          : population size
  fintech_penetration  : target credit uptake rate [0, 1]
  diversity_policy     : "none" | "incentive" | "mandate"
  shock_regime         : "baseline" | "climate_stress" | "trade_disruption"
                         | "compound"
  trade_openness       : fraction of produce eligible for export channel

Data Collection (DataCollector)
---------------------------------
  Model-level : mean farmgate prices, price volatility (CV), mean wealth,
                Gini coefficient, fintech penetration, PAR30,
                trade shock multiplier, weather z-score, diversity index.
  Agent-level : wealth, diversity_index, nutrition_score, has_credit,
                production per crop.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

import mesa
import mesa.space as space
import networkx as nx
import numpy as np
from mesa.datacollection import DataCollector

from .agents import (
    BASELINE_PRICES,
    CROPS,
    Farmer,
    FintechProvider,
    Trader,
    shannon_diversity,
)


# ---------------------------------------------------------------------------
# Gini helper
# ---------------------------------------------------------------------------

def gini_coefficient(values: List[float]) -> float:
    """Gini coefficient of a wealth vector; 0 = perfect equality."""
    arr = np.array(sorted(values), dtype=float)
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return (2 * np.dot(index, arr) / (n * arr.sum())) - (n + 1) / n


# ---------------------------------------------------------------------------
# KidashiModel
# ---------------------------------------------------------------------------

class KidashiModel(mesa.Model):
    """
    Main simulation model.

    Parameters
    ----------
    num_farmers : int
        Number of smallholder farmer agents. Default 500.
    num_traders : int
        Number of aggregator/processor agents. Default 10.
    fintech_penetration : float
        Target fraction of farmers with active credit [0, 1].
    diversity_policy : str
        "none"       – no policy intervention on crop mix.
        "incentive"  – diversified farmers receive a 5% price premium.
        "mandate"    – forced minimum portfolio floor raised to 0.20 per crop.
    shock_regime : str
        "baseline"          – mild random shocks only.
        "climate_stress"    – elevated weather shock variance.
        "trade_disruption"  – frequent large trade shock events.
        "compound"          – both climate and trade shocks elevated.
    trade_openness : float
        Share of total produce eligible for the export (Europe-linked) channel.
    seed : int | None
        RNG seed for reproducibility.
    """

    def __init__(
        self,
        num_farmers:         int = 500,
        num_traders:         int = 10,
        fintech_penetration: float = 0.40,
        diversity_policy:    str = "none",
        shock_regime:        str = "baseline",
        trade_openness:      float = 0.20,
        seed:                Optional[int] = None,
    ) -> None:
        super().__init__(seed=seed)

        # ----------------------------------------------------------------
        # Parameters
        # ----------------------------------------------------------------
        self.num_farmers = num_farmers
        self.num_traders = num_traders
        self.fintech_penetration = fintech_penetration
        self.diversity_policy = diversity_policy
        self.shock_regime = shock_regime
        self.trade_openness = trade_openness

        # ----------------------------------------------------------------
        # Shock configuration per regime
        # ----------------------------------------------------------------
        _shock_cfg = {
            "baseline":         {"weather_vol": 0.20, "trade_prob": 0.08, "trade_mag": 0.15},
            "climate_stress":   {"weather_vol": 0.45, "trade_prob": 0.08, "trade_mag": 0.15},
            "trade_disruption": {"weather_vol": 0.20, "trade_prob": 0.25, "trade_mag": 0.35},
            "compound":         {"weather_vol": 0.45, "trade_prob": 0.25, "trade_mag": 0.35},
        }
        cfg = _shock_cfg.get(shock_regime, _shock_cfg["baseline"])
        self._weather_vol:  float = cfg["weather_vol"]
        self._trade_prob:   float = cfg["trade_prob"]
        self._trade_mag:    float = cfg["trade_mag"]

        # ----------------------------------------------------------------
        # Fintech / credit parameters (calibrated from XchangeBox actuals)
        # ----------------------------------------------------------------
        # 12% yield gain via better inputs
        self.credit_yield_uplift:        float = 0.12
        # 55% spoilage reduction (TomatoPro)
        self.spoilage_reduction_fintech: float = 0.55

        # ----------------------------------------------------------------
        # Market state
        # ----------------------------------------------------------------
        self.expected_prices: Dict[str, float] = dict(BASELINE_PRICES)
        self.price_volatility: Dict[str, float] = {c: 0.15 for c in CROPS}
        self.market_volume:    Dict[str, float] = {c: 0.0 for c in CROPS}
        self.price_history:    Dict[str, List[float]] = {c: [] for c in CROPS}

        # Shock state
        self.current_weather_z:     float = 0.0   # shared weather signal
        self.trade_shock_multiplier: float = 1.0   # applied to export prices

        # ----------------------------------------------------------------
        # Trade network (stylised Nigeria → Europe corridor)
        # ----------------------------------------------------------------
        self.trade_network = self._build_trade_network()

        # ----------------------------------------------------------------
        # Spatial grid (agents placed on network grid)
        # ----------------------------------------------------------------
        # Simple proxy: 20×25 MultiGrid where each cell ≈ a sub-region
        self.grid = space.MultiGrid(20, 25, torus=False)

        # ----------------------------------------------------------------
        # Agents
        # ----------------------------------------------------------------
        self.farmers:          List[Farmer] = []
        self.traders:          List[Trader] = []
        self.fintech_provider: Optional[FintechProvider] = None

        self._create_agents()

        # ----------------------------------------------------------------
        # DataCollector
        # ----------------------------------------------------------------
        self.datacollector = DataCollector(
            model_reporters={
                # Prices
                "price_maize": lambda m: m._mean_recent_price("maize"),
                "price_sorghum": lambda m: m._mean_recent_price("sorghum"),
                "price_tomato": lambda m: m._mean_recent_price("tomato"),
                # Volatility (CV of last-N prices)
                "cv_maize": lambda m: m._price_cv("maize"),
                "cv_sorghum": lambda m: m._price_cv("sorghum"),
                "cv_tomato": lambda m: m._price_cv("tomato"),
                # Incomes / wealth
                "mean_wealth": lambda m: np.mean([f.wealth for f in m.farmers]),
                "median_wealth": lambda m: float(np.median([f.wealth for f in m.farmers])),
                "gini_wealth": lambda m: gini_coefficient([f.wealth for f in m.farmers]),
                # Fintech
                "fintech_rate": lambda m: sum(f.has_credit for f in m.farmers) / max(1, len(m.farmers)),
                "par30": lambda m: m.fintech_provider.portfolio_at_risk if m.fintech_provider else 0.0,
                # Diversity
                "mean_diversity_index": lambda m: np.mean([f.diversity_index for f in m.farmers]),
                # Nutrition
                "mean_nutrition": lambda m: np.mean([f.nutrition_score for f in m.farmers]),
                "pct_food_secure": lambda m: sum(f.nutrition_score >= 0.8 for f in m.farmers) / max(1, len(m.farmers)),
                # Shocks
                "weather_z": lambda m: m.current_weather_z,
                "trade_shock_mult": lambda m: m.trade_shock_multiplier,
                # Time
                "step": lambda m: m.time,
            },
            agent_reporters={
                "type": lambda a: type(a).__name__,
                "wealth": lambda a: a.wealth if isinstance(a, Farmer) else None,
                "diversity_index": lambda a: a.diversity_index if isinstance(a, Farmer) else None,
                "nutrition_score": lambda a: a.nutrition_score if isinstance(a, Farmer) else None,
                "has_credit": lambda a: int(a.has_credit) if isinstance(a, Farmer) else None,
                "prod_maize": lambda a: a.production.get("maize", 0) if isinstance(a, Farmer) else None,
                "prod_tomato": lambda a: a.production.get("tomato", 0) if isinstance(a, Farmer) else None,
                "prod_sorghum": lambda a: a.production.get("sorghum", 0) if isinstance(a, Farmer) else None,
            },
        )

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _build_trade_network(self) -> nx.DiGraph:
        """
        Stylised value-chain network:
          North_farm → Kano_market → Lagos_hub → EU_market
          North_farm → Abuja_hub   → Lagos_hub
        """
        G = nx.DiGraph()
        nodes = ["north_farm", "kano_market",
                 "abuja_hub", "lagos_hub", "eu_market"]
        edges = [
            ("north_farm",  "kano_market", {"weight": 1.0, "mode": "truck"}),
            ("north_farm",  "abuja_hub",   {"weight": 1.2, "mode": "truck"}),
            ("kano_market", "lagos_hub",   {"weight": 1.5, "mode": "truck"}),
            ("abuja_hub",   "lagos_hub",   {"weight": 1.1, "mode": "truck"}),
            ("lagos_hub",   "eu_market",   {"weight": 3.0, "mode": "ship"}),
        ]
        G.add_nodes_from(nodes)
        G.add_edges_from([(u, v, d) for u, v, d in edges])
        return G

    def _create_agents(self) -> None:
        """Instantiate all agents and place on grid."""

        # --- FintechProvider ---
        fp = FintechProvider(self)
        self.fintech_provider = fp

        # --- Farmers ---
        for _ in range(self.num_farmers):
            # Heterogeneous endowments (log-normal farm size: NBS 2021)
            farm_size = float(self.rng.lognormal(
                mean=0.7, sigma=0.5))   # median ~2 ha
            farm_size = np.clip(farm_size, 0.5, 10.0)
            risk_av = float(self.rng.uniform(0.20, 0.85))
            wealth = float(self.rng.lognormal(
                mean=11.5, sigma=0.8))  # median ~100k NGN
            region = "north" if self.rng.random() < 0.65 else "south"

            f = Farmer(
                self,
                farm_size_ha=farm_size,
                risk_aversion=risk_av,
                initial_wealth=wealth,
                region=region,
            )

            # Apply diversity policy: raise floor if mandated
            if self.diversity_policy == "mandate":
                f.crop_portfolio = {c: 1 / len(CROPS) for c in CROPS}

            # Place on grid
            x = self.rng.integers(0, self.grid.width)
            y = self.rng.integers(0, self.grid.height)
            self.grid.place_agent(f, (int(x), int(y)))
            self.farmers.append(f)

        # --- Traders ---
        specialisations = ["maize", "sorghum", "tomato"]
        for i in range(self.num_traders):
            spec = specialisations[i % len(specialisations)]
            cap = float(self.rng.uniform(300, 1500))
            t = Trader(self, capacity_mt=cap, specialisation=spec)
            x = self.rng.integers(0, self.grid.width)
            y = self.rng.integers(0, self.grid.height)
            self.grid.place_agent(t, (int(x), int(y)))
            self.traders.append(t)

    # ------------------------------------------------------------------
    # Price & market methods
    # ------------------------------------------------------------------

    def get_expected_price(self, crop: str) -> float:
        """Current expected price for crop (NGN/MT)."""
        return self.expected_prices.get(crop, BASELINE_PRICES[crop])

    def get_farmgate_price(self, crop: str, farmer: Farmer) -> float:
        """
        Endogenous farmgate price.

        Mechanism: inverse supply (higher aggregate supply → lower price),
        modulated by trade shock and diversity policy premium.

        P_t = P_baseline * (1 / (1 + λ·S_t)) * trade_mult
              × diversity_premium × distress_adjustment
        """
        # Aggregate supply approximation: expected production
        total_supply = sum(
            f.farm_size_ha *
            f.crop_portfolio.get(crop, 0) * np.mean((1.2, 2.5))
            for f in self.farmers
        )

        base = self.expected_prices[crop]
        lam = 5e-5             # price flexibility parameter
        inv_sup = 1.0 / (1.0 + lam * total_supply)
        price = base * inv_sup * self.trade_shock_multiplier

        # Diversity premium (incentive policy)
        if self.diversity_policy == "incentive" and farmer.diversity_index > 0.9:
            price *= 1.05

        # floor: 25% of baseline
        price = max(BASELINE_PRICES[crop] * 0.25, price)
        self.price_history[crop].append(price)
        return price

    # ------------------------------------------------------------------
    # Shock generation
    # ------------------------------------------------------------------

    def _apply_weather_shock(self) -> None:
        """
        Draw a shared weather z-score (drought/flood signal).
        Severe events: |z| > 1.5 (≈ 13% probability under Gaussian).
        Volatility scaled by shock regime.
        """
        self.current_weather_z = float(self.rng.normal(0, self._weather_vol))

        # Propagate to expected prices (yield damage → supply contraction)
        if self.current_weather_z < -1.0:   # drought signal
            for crop in CROPS:
                self.expected_prices[crop] *= (1.0 +
                                               0.05 * abs(self.current_weather_z))
        elif self.current_weather_z > 1.5:  # bumper harvest
            for crop in CROPS:
                self.expected_prices[crop] *= 0.97

        # Revert toward baseline gradually (mean-reverting)
        for crop in CROPS:
            self.expected_prices[crop] = (
                0.92 * self.expected_prices[crop] +
                0.08 * BASELINE_PRICES[crop]
            )

    def _apply_trade_shock(self) -> None:
        """
        Stochastic trade shock: European import demand disruption,
        tariff change, or global commodity price spike.
        Probability and magnitude drawn from shock regime config.
        """
        if self.rng.random() < self._trade_prob:
            direction = 1.0 if self.rng.random() < 0.40 else -1.0   # 40% upside, 60% downside
            magnitude = self.rng.uniform(0.0, self._trade_mag)
            self.trade_shock_multiplier = 1.0 + direction * magnitude
        else:
            # Revert toward no-shock
            self.trade_shock_multiplier = (
                0.80 * self.trade_shock_multiplier + 0.20 * 1.0
            )
        self.trade_shock_multiplier = np.clip(
            self.trade_shock_multiplier, 0.50, 1.80)

    def _update_price_volatility(self) -> None:
        """Rolling coefficient of variation (CV) over last 8 steps."""
        window = 8
        for crop in CROPS:
            hist = self.price_history[crop][-window:]
            if len(hist) >= 2:
                mu = np.mean(hist)
                sig = np.std(hist)
                self.price_volatility[crop] = sig / mu if mu > 0 else 0.0

    # ------------------------------------------------------------------
    # DataCollector helpers
    # ------------------------------------------------------------------

    def _mean_recent_price(self, crop: str, n: int = 3) -> float:
        hist = self.price_history.get(crop, [])
        return float(np.mean(hist[-n:])) if hist else BASELINE_PRICES[crop]

    def _price_cv(self, crop: str, n: int = 12) -> float:
        hist = self.price_history.get(crop, [])
        if len(hist) < 2:
            return 0.0
        subset = hist[-n:]
        mu = np.mean(subset)
        return float(np.std(subset) / mu) if mu > 0 else 0.0

       # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """
        One simulation season with explicit staged order.

        Academic/policy logic:
          1. Weather and trade shocks occur.
          2. Fintech provider disburses credit before production.
          3. Farmers produce with or without credit-enabled yield/spoilage effects.
          4. Farmers allocate harvest between aggregator and local market channels.
          5. Traders procure from aggregator-channel supply and clear inventory.
          6. Farmers sell remaining local/direct-market supply.
          7. Farmers service debt.
          8. Farmers adapt crop portfolio for the next season.
          9. Model indicators are collected.
          10. Within-step market accumulators are reset.
        """

        # 1. Apply exogenous shocks
        self._apply_weather_shock()
        self._apply_trade_shock()
        self._update_price_volatility()

        # 2. Fintech phase: credit arrives before production
        if self.fintech_provider is not None:
            self.fintech_provider.disburse()
            self.fintech_provider.update_par()

        # 3. Production phase
        farmers_prod = list(self.farmers)
        self.rng.shuffle(farmers_prod)
        for farmer in farmers_prod:
            farmer.produce()

        # 4. Sales channel allocation phase
        farmers_allocate = list(self.farmers)
        self.rng.shuffle(farmers_allocate)
        for farmer in farmers_allocate:
            farmer.allocate_sales_channels()

        # 5. Trader procurement and market clearing phase
        traders = list(self.traders)
        self.rng.shuffle(traders)
        for trader in traders:
            trader.procure()
            trader.sell_inventory()

        # 6. Farmer local/direct sales phase
        farmers_sell = list(self.farmers)
        self.rng.shuffle(farmers_sell)
        for farmer in farmers_sell:
            farmer.sell()

        # 7. Debt service phase
        farmers_debt = list(self.farmers)
        self.rng.shuffle(farmers_debt)
        for farmer in farmers_debt:
            farmer.service_debt()

        # 8. Portfolio adaptation for next season
        farmers_adapt = list(self.farmers)
        self.rng.shuffle(farmers_adapt)
        for farmer in farmers_adapt:
            farmer.decide_portfolio()

        # 9. Collect data
        self.datacollector.collect(self)

        # 10. Reset within-step market volume
        self.market_volume = {c: 0.0 for c in CROPS}
