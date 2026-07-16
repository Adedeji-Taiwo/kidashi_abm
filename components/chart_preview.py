from model.model import KidashiModel
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")


# ---- palette lifted straight from app.py's :root CSS variables ----
C_BG = "#0a2c32"
C_GRID = "#1c4a50"
C_TEXT = "#dcecEB"
C_MUTED = "#93b3b1"
C_GOLD = "#f2b84b"
C_CYAN = "#7edfe0"
C_GREEN = "#3fbd7a"
C_ORANGE = "#eba654"


def themed_fig(figsize=(9, 3.2)):
    fig, ax = plt.subplots(figsize=figsize, dpi=140)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.tick_params(colors=C_MUTED, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color=C_GRID, linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    return fig, ax


def style_legend(ax):
    leg = ax.legend(
        loc="upper right", frameon=True, fontsize=8.5, labelcolor=C_TEXT,
        handlelength=1.4,
    )
    leg.get_frame().set_facecolor(C_BG)
    leg.get_frame().set_edgecolor(C_GRID)
    leg.get_frame().set_alpha(0.88)
    return leg


def scaled_formatter(max_val):
    if max_val >= 1_000_000:
        return FuncFormatter(lambda x, _: f"{x/1_000_000:,.1f}M"), "NGN, millions"
    if max_val >= 1_000:
        return FuncFormatter(lambda x, _: f"{x/1_000:,.0f}k"), "NGN, thousands"
    return FuncFormatter(lambda x, _: f"{x:,.0f}"), "NGN"


def chart_prices(model_df, path):
    fig, ax = themed_fig()
    fmt, _ = scaled_formatter(
        model_df[["price_maize", "price_sorghum", "price_tomato"]].values.max())
    ax.plot(model_df["step"], model_df["price_maize"],
            color=C_GOLD, linewidth=2, label="Maize")
    ax.plot(model_df["step"], model_df["price_sorghum"],
            color=C_CYAN, linewidth=2, label="Sorghum")
    ax.plot(model_df["step"], model_df["price_tomato"],
            color=C_GREEN, linewidth=2, label="Tomato")
    ax.yaxis.set_major_formatter(fmt)
    ax.set_xlabel("Step (season)", color=C_MUTED, fontsize=9)
    ax.set_ylabel("Farmgate price (NGN/MT)", color=C_MUTED, fontsize=9)
    style_legend(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def chart_wealth(model_df, path):
    fig, ax = themed_fig()
    fmt, _ = scaled_formatter(model_df["mean_wealth"].values.max())
    ax.plot(model_df["step"], model_df["mean_wealth"],
            color=C_ORANGE, linewidth=2.2)
    ax.fill_between(
        model_df["step"], model_df["mean_wealth"], color=C_ORANGE, alpha=0.08)
    ax.yaxis.set_major_formatter(fmt)
    ax.set_xlabel("Step (season)", color=C_MUTED, fontsize=9)
    ax.set_ylabel("Mean farmer wealth (NGN)", color=C_MUTED, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def chart_diversity(model_df, path):
    fig, ax = themed_fig()
    ax.plot(model_df["step"], model_df["mean_diversity_index"],
            color=C_GREEN, linewidth=2.2)
    ax.fill_between(
        model_df["step"], model_df["mean_diversity_index"], color=C_GREEN, alpha=0.08)
    ax.set_xlabel("Step (season)", color=C_MUTED, fontsize=9)
    ax.set_ylabel("Mean diversity index (H\u2032)", color=C_MUTED, fontsize=9)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    model = KidashiModel(
        num_farmers=120, num_traders=10, fintech_penetration=0.40,
        diversity_policy="incentive", shock_regime="compound",
        trade_openness=0.20, seed=42,
    )
    for _ in range(40):
        model.step()
    model_df = model.datacollector.get_model_vars_dataframe()

    chart_prices(model_df, "/home/claude/kidashi_test/preview_prices.png")
    chart_wealth(model_df, "/home/claude/kidashi_test/preview_wealth.png")
    chart_diversity(
        model_df, "/home/claude/kidashi_test/preview_diversity.png")
    print("done")
