"""
Single-scenario entry point for the Kidashi ABM.
Usage: python run_model.py --shock_regime climate_stress --fintech_penetration 0.3
"""
import argparse
from model.model import KidashiModel


def main():
    parser = argparse.ArgumentParser(
        description="Run one scenario of the Kidashi ABM")
    parser.add_argument("--steps", type=int, default=40,
                        help="Number of simulation steps (seasons)")
    parser.add_argument("--num_farmers", type=int, default=500,
                        help="Number of farmer agents")
    parser.add_argument("--num_traders", type=int, default=10,
                        help="Number of trader agents")
    parser.add_argument("--fintech_penetration", type=float, default=0.40,
                        help="Fraction of farmers with active credit [0, 1]")
    parser.add_argument("--diversity_policy", type=str, default="none",
                        choices=["none", "incentive", "mandate"],
                        help="Crop diversification policy regime")
    parser.add_argument("--shock_regime", type=str, default="baseline",
                        choices=["baseline", "climate_stress",
                                 "trade_disruption", "compound"],
                        help="Shock regime for the simulation")
    parser.add_argument("--trade_openness", type=float, default=0.20,
                        help="Share of produce eligible for export channel")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    model = KidashiModel(
        num_farmers=args.num_farmers,
        num_traders=args.num_traders,
        fintech_penetration=args.fintech_penetration,
        diversity_policy=args.diversity_policy,
        shock_regime=args.shock_regime,
        trade_openness=args.trade_openness,
        seed=args.seed,
    )

    for _ in range(args.steps):
        model.step()

    # Retrieve data
    model_df = model.datacollector.get_model_vars_dataframe()
    agent_df = model.datacollector.get_agent_vars_dataframe()

    # Print headline figures
    print("=== Simulation Complete ===")
    print(
        f"Steps: {args.steps}, Farmers: {args.num_farmers}, Traders: {args.num_traders}")
    print(f"Fintech penetration: {args.fintech_penetration}")
    print(f"Diversity policy: {args.diversity_policy}")
    print(f"Shock regime: {args.shock_regime}")
    print(f"Trade openness: {args.trade_openness}")

    if "wealth" in agent_df.columns:
        print(f"Final mean farmer wealth: {agent_df['wealth'].mean():.2f}")
    if "income" in agent_df.columns:
        print(f"Final mean farmer income: {agent_df['income'].mean():.2f}")
    if "default" in agent_df.columns:
        print(f"Number of defaults: {agent_df['default'].sum()}")

    print("===========================")

    # Optionally save
    # model_df.to_csv("results/demo_run_model.csv")
    # agent_df.to_csv("results/demo_run_agents.csv")


if __name__ == "__main__":
    main()
