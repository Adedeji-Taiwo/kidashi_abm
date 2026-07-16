"""
=========
Agent definitions for the ABM:
  Fintech-Led Liquidity Provision & Farmgate Price Resilience
  in Nigerian Staple Value Chains (KidashiABM).

Agents
------
  Farmer          – Heterogeneous smallholder. Decides crop portfolio,
                    produces under stochastic yield shocks, sells across
                    market channels; eligible for Kidashi / Farm-to-Factory
                    liquidity products.
  FintechProvider – XchangeBox-inspired liquidity agent. Evaluates trust-
                    circle creditworthiness, disburses credit, collects
                    repayments, tracks portfolio quality.
  Trader          – Aggregator / processor node (maize miller, tomato paste
                    processor). Clears inventory across local and regional
                    markets; transmits trade shocks downstream.

Design Notes
------------
  * Mesa 3.5 API: agents register automatically on __init__; no unique_id
    required in constructor. Spatial placement handled externally in model.
  * All monetary units in Nigerian Naira (NGN). Quantities in metric tons.
  * Shannon Diversity Index (H') computed per farmer for portfolio tracking.
  * TomatoPro stochastic spoilage logic embedded in Trader.step().
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict, List

import mesa
import numpy as np

if TYPE_CHECKING:
    from .model import KidashiModel


# ---------------------------------------------------------------------------
# Constants / calibration anchors (informed by XchangeBox field data)
# ---------------------------------------------------------------------------

CROPS: List[str] = ["maize", "sorghum", "tomato"]

# Baseline farmgate prices (NGN/metric ton) – calibrated to 2023 CBN/NBS data
BASELINE_PRICES: Dict[str, float] = {
    "maize":   310_000,
    "sorghum": 280_000,
    "tomato":  420_000,
}

# Typical yield ranges (MT/ha) drawn from IITA on-farm trial data
YIELD_RANGE: Dict[str, tuple] = {
    "maize":   (1.2, 3.5),
    "sorghum": (0.9, 2.8),
    "tomato":  (8.0, 22.0),
}

# Yield shock std-dev (fraction of mean) – calibrated to CHIRPS/ERA5 variability
YIELD_VOL: Dict[str, float] = {
    "maize":   0.22,
    "sorghum": 0.19,
    "tomato":  0.31,   # higher: perishable, climate-sensitive
}

# Post-harvest spoilage rate without liquidity (from TomatoPro baseline)
SPOILAGE_RATE_NO_FINTECH: Dict[str, float] = {
    "maize":   0.10,
    "sorghum": 0.08,
    # 55% reduction achieved via liquidity → 0.35 * (1-0.55) = 0.158
    "tomato":  0.35,
}

# Kidashi / Farm-to-Factory credit product parameters (XchangeBox actuals)
CREDIT_FLOOR_NGN = 50_000
CREDIT_CEILING_NGN = 500_000
PAYMENT_CYCLE_DAYS_LEGACY = 75   # 60-90 day average pre-fintech
PAYMENT_CYCLE_DAYS_FINTECH = 2.5  # <72 hours post-fintech


# ---------------------------------------------------------------------------
# Helper: Shannon Diversity Index
# ---------------------------------------------------------------------------

def shannon_diversity(portfolio: Dict[str, float]) -> float:
    """H' = -sum(p_i * ln(p_i)) for crop shares p_i > 0."""
    total = sum(portfolio.values())
    if total == 0:
        return 0.0
    shares = [v / total for v in portfolio.values() if v > 0]
    return -sum(p * math.log(p) for p in shares if p > 0)


# ---------------------------------------------------------------------------
# Farmer
# ---------------------------------------------------------------------------

class Farmer(mesa.Agent):
    """
    Heterogeneous smallholder agent.

    Behavioral rules
    ----------------
    1. decide_portfolio()  – Adaptive expected-utility portfolio allocation
                             (EV of crop income minus variance penalty scaled
                             by risk aversion). Minimum diversity floor.
    2. produce()           – Stochastic yield with weather-correlated shocks.
                             Fintech credit unlocks better input timing
                             (fertiliser, certified seed), raising mean yield.
    3. sell()              – Multi-channel: local spot, aggregator, or export.
                             Fintech reduces distress-sale discount (faster
                             payment cycle mirrors Kidashi liquidity effect).
    4. service_debt()      – Repay outstanding credit; default if insolvent.
    5. step()              – Sequence: produce → sell → service_debt →
                             adapt portfolio.

    Parameters
    ----------
    model        : KidashiModel
    farm_size_ha : float  – Cultivated area (ha). Drawn from log-normal
                            calibrated to NBS Agricultural Survey (2021).
    risk_aversion: float  – Coefficient [0, 1]. High → more conservative
                            portfolio choices under uncertainty.
    initial_wealth: float – Starting wealth (NGN).
    region       : str    – "north" | "south". Affects yield distributions
                            and market access.
    """

    def __init__(
        self,
        model: "KidashiModel",
        farm_size_ha: float = 2.0,
        risk_aversion: float = 0.5,
        initial_wealth: float = 150_000.0,
        region: str = "north",
    ) -> None:
        super().__init__(model)

        # --- Endowments ---
        self.farm_size_ha = farm_size_ha
        self.risk_aversion = risk_aversion
        self.wealth = initial_wealth
        self.region = region

        # --- Production ---
        # Initial portfolio: diversified baseline (maize-dominant in North)
        self.crop_portfolio: Dict[str, float] = {
            "maize":   0.55,
            "sorghum": 0.30,
            "tomato":  0.15,
        }
        self.production:     Dict[str, float] = {c: 0.0 for c in CROPS}
        self.spoilage:       Dict[str, float] = {c: 0.0 for c in CROPS}

        # --- Sales channel allocation ---
        # Quantity reserved for trader/aggregator procurement
        self.aggregator_supply: Dict[str, float] = {c: 0.0 for c in CROPS}

        # Quantity sold directly/local spot market
        self.local_supply: Dict[str, float] = {c: 0.0 for c in CROPS}

        # --- Fintech state ---
        self.has_credit:        bool = False
        self.credit_outstanding: float = 0.0
        self.credit_disbursed:   float = 0.0
        self.payment_cycle_days: float = PAYMENT_CYCLE_DAYS_LEGACY
        self.consecutive_defaults: int = 0

        # --- Trade channel ---
        # 0 = local spot, 1 = aggregator, 2 = regional/export
        self.primary_channel: int = 0

        # --- Tracking ---
        self.income_history:  List[float] = []
        self.diversity_index: float = shannon_diversity(self.crop_portfolio)
        self.nutrition_score: float = 1.0   # proxy: 0 = severe insecurity

    # ------------------------------------------------------------------
    # 1. Portfolio decision
    # ------------------------------------------------------------------

    def decide_portfolio(self) -> None:
        """
        Mean-variance expected utility maximisation (simplified, adaptive).

        EU(crop) = E[price] * E[yield] * area_share
                   - risk_aversion * Var[price] * E[yield]^2

        Shares normalised; floor of 0.10 enforces minimum diversity
        (representing production diversity as a resilience strategy per B03).
        """
        model = self.model
        eu: Dict[str, float] = {}

        for crop in CROPS:
            ep = model.get_expected_price(crop)
            ey = np.mean(YIELD_RANGE[crop])
            var = (model.price_volatility.get(crop, 0.15) * ep) ** 2
            eu[crop] = ep * ey - self.risk_aversion * var * (ey ** 2) * 1e-9

        # Softmax-style normalisation with floor
        min_eu = min(eu.values())
        shifted = {c: max(0, v - min_eu + 1e-6) for c, v in eu.items()}
        total = sum(shifted.values())
        raw = {c: v / total for c, v in shifted.items()}

        # Diversity floor: each crop ≥ 10 % — iterative clamp to preserve sum=1
        FLOOR = 0.10
        portfolio = dict(raw)
        for _ in range(10):  # iterate until convergence
            clamped = {c: max(FLOOR, v) for c, v in portfolio.items()}
            total_c = sum(clamped.values())
            portfolio = {c: v / total_c for c, v in clamped.items()}
            if all(v >= FLOOR - 1e-9 for v in portfolio.values()):
                break
        self.crop_portfolio = portfolio
        self.diversity_index = shannon_diversity(self.crop_portfolio)

    # ------------------------------------------------------------------
    # 2. Production
    # ------------------------------------------------------------------

    def produce(self) -> None:
        """
        Stochastic yield generation correlated with model-level weather shock.

        Fintech credit effect: better input timing (fertiliser delivery,
        certified seed) raises realized yield by model.credit_yield_uplift.
        Calibrated from XchangeBox / TomatoPro baseline (18.6% profit
        uplift → ~12% yield uplift after price effects).
        """
        model = self.model
        weather_z = model.current_weather_z  # shared correlated shock

        for crop in CROPS:
            share = self.crop_portfolio[crop]
            area_ha = self.farm_size_ha * share
            y_lo, y_hi = YIELD_RANGE[crop]
            base_y = self.model.rng.uniform(y_lo, y_hi)

            # Correlated weather shock + idiosyncratic noise
            idio_z = self.model.rng.standard_normal()
            rho = 0.60  # weather-yield correlation
            shock_z = rho * weather_z + math.sqrt(1 - rho ** 2) * idio_z
            shock = 1.0 + YIELD_VOL[crop] * shock_z
            # floor: catastrophic but not zero
            shock = max(0.05, shock)

            yield_mt = area_ha * base_y * shock

            # Fintech credit → better inputs
            if self.has_credit:
                yield_mt *= (1.0 + model.credit_yield_uplift)

            # Post-harvest spoilage (TomatoPro-inspired)
            sp_rate = SPOILAGE_RATE_NO_FINTECH[crop]
            if self.has_credit:
                sp_rate *= (1.0 - model.spoilage_reduction_fintech)
            spoiled = yield_mt * sp_rate

            self.production[crop] = max(0.0, yield_mt - spoiled)
            self.spoilage[crop] = spoiled

    def allocate_sales_channels(self) -> None:
        """
        Split harvested production into:
        1. Aggregator/trader channel
        2. Local/direct market channel

        Fintech-enabled farmers are assumed to have stronger access to
        structured buyers and Farm-to-Factory style procurement channels.
        """

        aggregator_share = 0.60 if self.has_credit else 0.30

        for crop in CROPS:
            qty = self.production.get(crop, 0.0)

            # Safety guard against NaN or negative production
            if qty is None or not np.isfinite(qty) or qty <= 0:
                self.aggregator_supply[crop] = 0.0
                self.local_supply[crop] = 0.0
                continue

            self.aggregator_supply[crop] = float(qty * aggregator_share)
            self.local_supply[crop] = float(qty * (1.0 - aggregator_share))

    # ------------------------------------------------------------------
    # 3. Sales
    # ------------------------------------------------------------------

    def sell(self) -> None:
        """
        Sell only the local/direct-market share of production.

        The aggregator/trader share is handled separately by Trader.procure().
        This prevents double-selling of the same harvest.
        """
        model = self.model
        income = 0.0

        for crop in CROPS:
            qty = self.local_supply.get(crop, 0.0)

            # Safety guard
            if qty is None or not np.isfinite(qty) or qty <= 0:
                self.local_supply[crop] = 0.0
                continue

            price = model.get_farmgate_price(crop, self)

            # Safety guard for price
            if price is None or not np.isfinite(price) or price <= 0:
                price = BASELINE_PRICES[crop]

            cycle_ratio = self.payment_cycle_days / PAYMENT_CYCLE_DAYS_LEGACY
            distress_disc = 0.20 * min(1.0, cycle_ratio)
            effective_price = price * (1.0 - distress_disc)

            # Safety guard for effective price
            if not np.isfinite(effective_price) or effective_price <= 0:
                effective_price = BASELINE_PRICES[crop] * 0.75

            revenue = qty * effective_price

            if np.isfinite(revenue):
                income += revenue
                model.market_volume[crop] = model.market_volume.get(
                    crop, 0.0) + qty

            # Local supply has now been sold
            self.local_supply[crop] = 0.0

        if np.isfinite(income):
            self.wealth += income

        # Final wealth guard
        if not np.isfinite(self.wealth):
            self.wealth = 5_000.0

        self.income_history.append(income if np.isfinite(income) else 0.0)
        self._update_nutrition_score(income if np.isfinite(income) else 0.0)

    # ------------------------------------------------------------------
    # 4. Debt service
    # ------------------------------------------------------------------

    def service_debt(self) -> None:
        """
        Simple credit repayment (one-period). Default if insolvent:
        credit revoked, wealth floored, default logged on provider.
        """
        if not self.has_credit or self.credit_outstanding <= 0:
            return
        repay = min(self.credit_outstanding, max(0.0, self.wealth * 0.25))
        self.wealth -= repay
        self.credit_outstanding -= repay

        if self.credit_outstanding <= 0:
            self.credit_outstanding = 0.0
            self.has_credit = False
            self.consecutive_defaults = 0

        elif self.wealth <= 0:
            # Default
            self.consecutive_defaults += 1
            self.model.fintech_provider.record_default()
            self.has_credit = False
            self.credit_outstanding = 0.0
            self.wealth = max(5_000, self.wealth)

    # ------------------------------------------------------------------
    # 5. Nutrition proxy
    # ------------------------------------------------------------------

    def _update_nutrition_score(self, income: float) -> None:
        """
        Simplified nutrition score: household caloric adequacy proxy.
        Score = min(1, income / subsistence_threshold).
        """
        SUBSISTENCE = 180_000.0

        if income is None or not np.isfinite(income) or income < 0:
            income = 0.0

        raw = income / SUBSISTENCE

        alpha = 0.4
        updated = alpha * min(1.0, raw) + (1 - alpha) * self.nutrition_score

        if np.isfinite(updated):
            self.nutrition_score = updated
        else:
            self.nutrition_score = 0.0

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> None:
        self.produce()
        self.sell()
        self.service_debt()
        self.decide_portfolio()


# ---------------------------------------------------------------------------
# FintechProvider
# ---------------------------------------------------------------------------

class FintechProvider(mesa.Agent):
    """
    XchangeBox-inspired liquidity agent.

    Products modelled
    -----------------
    Kidashi trust-circle credit  – Group-based (5–8 farmers) lending.
                                   Default risk pooled within circle.
    Farm-to-Factory invoice       – Processor-linked receivables financing.
                                   Disbursed to Trader agents; repaid on
                                   payment receipt.

    Underwriting logic
    ------------------
    Creditworthiness score combines:
      (a) Wealth percentile among peers
      (b) Crop diversity (higher H' → lower risk → higher score)
      (c) Consecutive default history (disqualifying threshold = 2)
    """

    def __init__(self, model: "KidashiModel") -> None:
        super().__init__(model)

        self.total_disbursed:   float = 0.0
        self.total_repaid:      float = 0.0
        self.active_loans:      int = 0
        self.cumulative_defaults: int = 0
        self.portfolio_at_risk: float = 0.0   # PAR30 proxy

    # ------------------------------------------------------------------
    # Creditworthiness scoring
    # ------------------------------------------------------------------

    def credit_score(self, farmer: Farmer, wealth_pct: float) -> float:
        """
        Score ∈ [0, 1]. Combine three signals.

        Parameters
        ----------
        wealth_pct : farmer's wealth percentile (0-1) among all farmers.
        """
        # (a) Wealth
        w_score = wealth_pct

        # (b) Diversity bonus: H' normalised by ln(n_crops)
        max_h = math.log(len(CROPS))
        d_score = farmer.diversity_index / max_h if max_h > 0 else 0.0

        # (c) Default penalty
        def_penalty = min(1.0, farmer.consecutive_defaults * 0.5)

        score = 0.50 * w_score + 0.35 * d_score - 0.15 * def_penalty
        return max(0.0, min(1.0, score))

    # ------------------------------------------------------------------
    # Disbursement round
    # ------------------------------------------------------------------

    def disburse(self) -> None:
        """
        Evaluate all unfinanced farmers; approve if credit score ≥ threshold.
        Credit amount is score-scaled between floor and ceiling.
        Penetration target is set by model.fintech_penetration.
        """
        model = self.model
        farmers = model.farmers
        n = len(farmers)
        if n == 0:
            return

        # Check current penetration
        current_rate = sum(1 for f in farmers if f.has_credit) / n
        if current_rate >= model.fintech_penetration:
            return  # target already met

        # Wealth percentile look-up: build sorted wealth array once
        all_wealths = sorted(f.wealth for f in farmers)

        eligible = [f for f in farmers if not f.has_credit
                    and f.consecutive_defaults < 2]

        for farmer in eligible:
            # Re-check penetration after each disbursement
            current_n_financed = sum(1 for f in farmers if f.has_credit)
            if current_n_financed / n >= model.fintech_penetration:
                break

            # Wealth percentile via bisect-style search
            w = farmer.wealth
            rank = sum(1 for ww in all_wealths if ww <= w)
            w_pct = rank / max(1, n)

            score = self.credit_score(farmer, w_pct)
            THRESHOLD = 0.25   # inclusive threshold (trust-circle model)

            if score >= THRESHOLD:
                amount = CREDIT_FLOOR_NGN + score * \
                    (CREDIT_CEILING_NGN - CREDIT_FLOOR_NGN)
                farmer.wealth += amount
                farmer.has_credit = True
                farmer.credit_outstanding = amount * 1.05   # 5% flat charge
                farmer.credit_disbursed = amount
                farmer.payment_cycle_days = PAYMENT_CYCLE_DAYS_FINTECH

                self.total_disbursed += amount
                self.active_loans += 1

    def record_default(self) -> None:
        self.cumulative_defaults += 1
        self.active_loans = max(0, self.active_loans - 1)

    # ------------------------------------------------------------------
    # Portfolio At Risk (PAR30) proxy
    # ------------------------------------------------------------------

    def update_par(self) -> None:
        farmers = self.model.farmers
        at_risk = sum(f.credit_outstanding for f in farmers
                      if f.has_credit and f.consecutive_defaults > 0)
        total = sum(f.credit_outstanding for f in farmers if f.has_credit)
        self.portfolio_at_risk = at_risk / total if total > 0 else 0.0

    def step(self) -> None:
        self.disburse()
        self.update_par()


# ---------------------------------------------------------------------------
# Trader / Processor
# ---------------------------------------------------------------------------

class Trader(mesa.Agent):
    """
    Aggregator and processor node.

    Role
    ----
    Buys surplus from farmers at slightly below farmgate price, sells into
    regional or export markets. Transmits trade-shock multiplier on export
    price changes (Europe-linked demand shocks).

    TomatoPro logic: stochastic spoilage at processor level modelled via
    two-point scenario generation (analogous to two-stage recourse).
    """

    def __init__(
        self,
        model: "KidashiModel",
        capacity_mt: float = 500.0,
        specialisation: str = "maize",
    ) -> None:
        super().__init__(model)

        self.capacity_mt = capacity_mt
        self.specialisation = specialisation   # primary commodity
        self.inventory:  Dict[str, float] = {c: 0.0 for c in CROPS}
        self.revenue:    float = 0.0

        # Invoice financing state (Farm-to-Factory)
        self.has_invoice_finance: bool = False
        self.receivable_outstanding: float = 0.0

    # ------------------------------------------------------------------
    # Procurement
    # ------------------------------------------------------------------
    def procure(self) -> None:
        """
        Buy up to capacity from farmers' aggregator-channel supply.

        Farmers reserve part of their harvest for structured buyers.
        This avoids double-counting because local/direct sales are handled
        separately in Farmer.sell().
        """
        model = self.model
        budget = self.capacity_mt * \
            model.get_expected_price(self.specialisation)

        if not np.isfinite(budget) or budget <= 0:
            return

        spent = 0.0

        candidates = list(model.rng.choice(
            model.farmers, size=min(30, len(model.farmers)), replace=False
        ))

        for farmer in candidates:
            qty = farmer.aggregator_supply.get(self.specialisation, 0.0)

            # Safety guard
            if qty is None or not np.isfinite(qty) or qty <= 0 or spent >= budget:
                farmer.aggregator_supply[self.specialisation] = 0.0
                continue

            price = model.get_farmgate_price(
                self.specialisation, farmer) * 0.90

            # Safety guard for price
            if price is None or not np.isfinite(price) or price <= 0:
                price = BASELINE_PRICES[self.specialisation] * 0.90

            affordable = min(qty, (budget - spent) / max(1.0, price))

            if not np.isfinite(affordable) or affordable <= 0:
                continue

            cost = affordable * price

            if not np.isfinite(cost) or cost <= 0:
                continue

            self.inventory[self.specialisation] += affordable

            # Reduce only the aggregator-channel supply
            farmer.aggregator_supply[self.specialisation] = max(
                0.0,
                farmer.aggregator_supply[self.specialisation] - affordable
            )

            farmer.wealth += cost

            # Wealth guard
            if not np.isfinite(farmer.wealth):
                farmer.wealth = 5_000.0

            spent += cost

            model.market_volume[self.specialisation] = model.market_volume.get(
                self.specialisation, 0.0
            ) + affordable

    # ------------------------------------------------------------------
    # Market clearing / stochastic spoilage
    # ------------------------------------------------------------------

    def sell_inventory(self) -> None:
        """
        Clear inventory to regional or export market.
        Two-scenario spoilage (high / low demand) — TomatoPro-style VSS logic.
        """
        for crop, qty in self.inventory.items():
            if qty <= 0:
                continue

            # Export price = baseline + trade shock multiplier
            base_price = BASELINE_PRICES[crop]
            trade_mult = self.model.trade_shock_multiplier
            export_price = base_price * trade_mult

            # Two-point stochastic scenario for spoilage
            if self.model.rng.random() < 0.5:    # high-demand scenario
                spoilage_frac = 0.05
                price_premium = 1.10
            else:                                  # low-demand / congestion
                spoilage_frac = 0.20
                price_premium = 0.85

            realized_qty = qty * (1.0 - spoilage_frac)
            self.revenue += realized_qty * export_price * price_premium
            self.inventory[crop] = 0.0

    def step(self) -> None:
        self.procure()
        self.sell_inventory()
