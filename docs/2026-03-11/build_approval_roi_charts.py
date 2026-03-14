from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
BASELINE_CSV = ROOT / "work_sales_roi_portfolio_baseline_male_only.csv"
PROFILE_CSV = ROOT / "work_sales_work_profile_male_only.csv"
BRIDGE_PNG = ROOT / "approval_roi_bridge_27works.png"
THRESHOLD_PNG = ROOT / "approval_roi_threshold_cost_vs_floor.png"

SCENARIO = "all_12m"
PORTFOLIO_SIZE = 27
TRIALS = 20_000
SEED = 20260313
MONTHS = ["4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
MONTHLY_PLAN = [1, 2, 2, 3, 4, 3, 4, 3, 5]


def set_style() -> None:
    plt.rcParams.update(
        {
            "font.family": ["Malgun Gothic", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "#f6f3ef",
            "axes.facecolor": "#f6f3ef",
            "savefig.facecolor": "#f6f3ef",
        }
    )


def amount_to_eok(value: int) -> float:
    return value / 100_000_000


def amount_to_manwon_text(value: int) -> str:
    return f"{round(value / 10_000):,.0f}만원"


def amount_to_short_eok_text(value: int) -> str:
    return f"{amount_to_eok(value):.2f}억"


def load_baseline_row() -> pd.Series:
    baseline = pd.read_csv(BASELINE_CSV)
    return baseline.loc[baseline["scenario"] == SCENARIO].iloc[0]


def simulate_portfolio_totals() -> np.ndarray:
    profile = pd.read_csv(PROFILE_CSV)
    values = profile.loc[profile["observed_12m"] == "Y", "cum_12m_net_sales"].to_numpy(dtype=np.int64)
    rng = np.random.default_rng(SEED)
    totals = np.empty(TRIALS, dtype=np.int64)
    for idx in range(TRIALS):
        totals[idx] = rng.choice(values, size=PORTFOLIO_SIZE, replace=False).sum()
    return totals


def build_bridge_chart() -> None:
    fig, ax = plt.subplots(figsize=(16, 9), dpi=160)
    ax.set_xlim(0.25, 12.8)
    ax.set_ylim(0.0, 4.4)
    ax.axis("off")

    fig.text(0.055, 0.92, "2026년 최소 생산 목표 = 27작품", fontsize=28, fontweight="bold", color="#13294b")
    fig.text(
        0.055,
        0.86,
        "승인 범위가 먼저 정해지고, 비용과 ROI 비교는 이 27작품 포트폴리오를 기준 단위로 읽는다.",
        fontsize=14,
        color="#53657d",
    )

    band = FancyBboxPatch(
        (0.65, 0.85),
        8.55,
        2.0,
        boxstyle="round,pad=0.03,rounding_size=0.18",
        linewidth=1.5,
        edgecolor="#d8dee8",
        facecolor="#f9f7f3",
    )
    ax.add_patch(band)

    rng = np.random.default_rng(SEED)
    y_levels = np.array([1.16, 1.52, 1.88, 2.24, 2.60])
    top_points_x: list[float] = []
    top_points_y: list[float] = []
    cumulative = 0
    for idx, (month, count) in enumerate(zip(MONTHS, MONTHLY_PLAN), start=1):
        ax.plot([idx, idx], [1.02, 2.52], color="#dde3ea", linewidth=1.2, zorder=0)
        y_values = y_levels[:count] + rng.normal(0, 0.016, size=count)
        ax.scatter(
            np.repeat(idx, count),
            y_values,
            s=210,
            color="#4f7db8",
            alpha=0.92,
            edgecolors="white",
            linewidths=1.6,
            zorder=3,
        )
        top_points_x.append(idx)
        top_points_y.append(float(y_levels[count - 1]))
        cumulative += count
        ax.text(idx, 0.78, month, ha="center", va="center", fontsize=12, color="#425466")
        ax.text(idx, 0.58, f"{count}개", ha="center", va="center", fontsize=11, fontweight="bold", color="#4f7db8")
        ax.text(idx, 0.30, f"누적 {cumulative}작품", ha="center", va="center", fontsize=11, color="#64748b")

    ax.plot(top_points_x, top_points_y, color="#93b4db", linewidth=3.0, alpha=0.9, zorder=1)
    ax.scatter(top_points_x, top_points_y, s=26, color="#93b4db", zorder=2)

    ax.text(0.78, 2.92, "월별 생산 램프업 시나리오", fontsize=13, fontweight="bold", color="#475569")
    ax.text(
        0.78,
        2.64,
        "4월 1개, 5월 2개로 시작하고 뒤로 갈수록 물량을 미루는 하반기 집중형 배치여도 총 27작품이 된다.",
        fontsize=12,
        color="#64748b",
    )

    summary_box = FancyBboxPatch(
        (9.85, 1.02),
        2.45,
        1.9,
        boxstyle="round,pad=0.04,rounding_size=0.18",
        linewidth=2.0,
        edgecolor="#3d8f6b",
        facecolor="#dfeee6",
    )
    ax.add_patch(summary_box)
    ax.text(11.075, 2.45, "승인 판단 단위", ha="center", va="center", fontsize=13, color="#2f6f52")
    ax.text(11.075, 2.02, "27작품", ha="center", va="center", fontsize=28, fontweight="bold", color="#17324d")
    ax.text(11.075, 1.66, "= 초반 램프업", ha="center", va="center", fontsize=14, color="#35556f")
    ax.text(11.075, 1.38, "+ 하반기 집중", ha="center", va="center", fontsize=14, color="#35556f")

    ax.annotate(
        "이 27작품이 뒤의 ROI 비교 단위",
        xy=(9.1, 1.95),
        xytext=(9.8, 3.38),
        fontsize=13,
        color="#2f6f52",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#edf7f1", edgecolor="#8ac5a3"),
        arrowprops=dict(arrowstyle="->", linewidth=1.8, color="#5aa06f"),
    )

    ax.text(
        0.78,
        0.12,
        "운영 전환 1단계 = 2026-04~12 생산 계획. 평균은 월 3작품 수준이지만 실제 배치는 후반 집중형으로 흔들릴 수 있다.",
        fontsize=13,
        color="#5b6b7f",
    )

    fig.savefig(BRIDGE_PNG, bbox_inches="tight")
    plt.close(fig)


def build_threshold_chart() -> None:
    baseline_row = load_baseline_row()
    totals = simulate_portfolio_totals()

    percentiles = {
        "P10": int(baseline_row["p10_total_net_sales"]),
        "P25": int(baseline_row["p25_total_net_sales"]),
        "P50": int(baseline_row["p50_total_net_sales"]),
        "P75": int(baseline_row["p75_total_net_sales"]),
        "P90": int(np.percentile(totals, 90)),
    }

    fig, ax = plt.subplots(figsize=(16, 9), dpi=160)
    ax.set_xlim(0.0, 3.45)
    ax.set_ylim(0.0, 1.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#8a96a8")
    ax.grid(axis="x", color="#dbe2ea", linewidth=1.0)
    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.tick_params(axis="x", labelsize=12, colors="#55657c")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))

    fig.text(0.055, 0.92, "이 분포에서 이 선을 본다", fontsize=28, fontweight="bold", color="#13294b")
    fig.text(
        0.055,
        0.86,
        "남성향 60개월 실매출 기준 / 27작품 포트폴리오 / 출시 후 12개월 누적 순매출 분위",
        fontsize=14,
        color="#53657d",
    )

    cost_low = amount_to_eok(22_000_000)
    cost_high = amount_to_eok(29_000_000)
    ax.axvspan(cost_low, cost_high, ymin=0.08, ymax=0.84, color="#efc75e", alpha=0.42, zorder=0)
    ax.vlines([cost_low, cost_high], 0.10, 0.84, color="#ca9a20", linewidth=2.2, zorder=1)
    ax.text(
        (cost_low + cost_high) / 2,
        0.89,
        "총원가 밴드\n0.22~0.29억\n(2,200~2,900만원)",
        ha="center",
        va="top",
        fontsize=13,
        fontweight="bold",
        color="#7a5800",
    )

    sample_rng = np.random.default_rng(SEED + 17)
    shown = sample_rng.choice(totals, size=280, replace=False) / 100_000_000
    y = sample_rng.uniform(0.14, 0.66, size=shown.size)
    sizes = sample_rng.uniform(18, 52, size=shown.size)
    ax.scatter(shown, y, s=sizes, color="#6b7280", alpha=0.24, edgecolors="none", zorder=2)

    marker_style = {
        "P10": {"color": "#7c8fb5", "top": 0.60, "xytext": (0.08, 0.69), "ha": "left"},
        "P25": {"color": "#18885c", "top": 0.83, "xytext": (0.08, 0.90), "ha": "left"},
        "P50": {"color": "#5f6672", "top": 0.65, "xytext": (0.08, 0.74), "ha": "left"},
        "P75": {"color": "#345d96", "top": 0.79, "xytext": (0.08, 0.87), "ha": "left"},
        "P90": {"color": "#1f365c", "top": 0.68, "xytext": (-0.30, 0.77), "ha": "right"},
    }

    for name, value in percentiles.items():
        x_pos = amount_to_eok(value)
        style = marker_style[name]
        ax.vlines(x_pos, 0.10, style["top"], color=style["color"], linewidth=3.0 if name == "P25" else 2.0, zorder=4)
        ax.scatter(
            [x_pos],
            [style["top"]],
            s=260 if name == "P25" else 135,
            color=style["color"],
            edgecolors="white",
            linewidths=1.5,
            zorder=5,
        )

        if name == "P25":
            label = f"보수적 하한선(P25)\n{amount_to_short_eok_text(value)} / {amount_to_manwon_text(value)}"
            fontweight = "bold"
        else:
            label = f"{name}\n{amount_to_short_eok_text(value)}"
            fontweight = "normal"

        dx, dy = style["xytext"]
        ax.annotate(
            label,
            xy=(x_pos, style["top"]),
            xytext=(x_pos + dx, dy),
            textcoords="data",
            ha=style["ha"],
            va="center",
            fontsize=12.5,
            fontweight=fontweight,
            color=style["color"],
            arrowprops=dict(arrowstyle="-", color=style["color"], linewidth=1.1, shrinkA=4, shrinkB=4),
        )

    note_box = FancyBboxPatch(
        (0.03, 0.62),
        0.25,
        0.15,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.4,
        edgecolor="#9fb4d1",
        facecolor="#eef3fb",
        transform=ax.transAxes,
    )
    ax.add_patch(note_box)
    ax.text(0.05, 0.745, "총원가 초과 확률", transform=ax.transAxes, fontsize=13, fontweight="bold", color="#48627f")
    ax.text(
        0.05,
        0.665,
        f"2,200만원 기준 {float(baseline_row['pass_22m_rate']) * 100:.1f}%\n2,900만원 기준 {float(baseline_row['pass_29m_rate']) * 100:.1f}%",
        transform=ax.transAxes,
        fontsize=12.5,
        color="#48627f",
        linespacing=1.35,
    )

    ax.text(
        0.02,
        0.08,
        "회색 점 = 27작품 포트폴리오 20,000회 샘플 중 일부. 승인 판단선은 P25와 총원가 밴드를 같이 본다.",
        transform=ax.transAxes,
        fontsize=12.5,
        color="#5b6b7f",
    )
    ax.text(
        0.02,
        0.03,
        "자료 출처: 자사 내부 월별 순매출 추적 원자료(work_sales_monthly_60m.csv), 2021-02~2026-01 60개월. 남성향 필터: 포텐/올나이트노벨/프로무림.",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#6b7280",
    )
    ax.set_xlabel("출시 후 12개월 누적 순매출 (억원)", fontsize=14, color="#516072", labelpad=12)

    fig.savefig(THRESHOLD_PNG, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    set_style()
    build_bridge_chart()
    build_threshold_chart()


if __name__ == "__main__":
    main()
