"""
Validation of Stock_TCJ against Danmarks Statistik BYGB34 / BYGV06.

Derivation of validation points:
  - BYGB34 (boligareal, enhet: 1000 m²) × 1000 → total floor area in m²
  - Divided by BYGV06 (m²/dwelling, cohort average) → number of dwellings per cohort
  - Summed over all cohorts per dwelling type → total stock per type

For cohorts Før 1900, 1900-1904, 1905-1909, 1910-1914: BYGB34 data exists but
BYGV06 data starts only from 1916. The 1916 BYGV06 value is used as proxy for
these early cohorts (Stuehus 227, Parcelhus 164, Rekkehus 127, Etagehus 88 m²/dw).
This is a conservative assumption; actual pre-1916 dwellings may have been slightly
larger, so the estimated count here is a lower bound for those cohorts.

'Uoplyst' (unknown construction year) rows are excluded from the sum.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─── Load Stock_TCJ ──────────────────────────────────────────────────────────
data = np.load("Stock_TCJ.npz", allow_pickle=True)
Stock_TCJ_np = data["data"]          # shape: (T, C, J)
years        = data["years"]         # 1D array of ints, 1600–2100
types        = list(data["types"])   # e.g. ['Parcelhus', 'Rekkehus', 'Etagehus', 'Stuehus']

# Sum over cohort axis (axis=1) to get stock per type per year
stock_by_type = Stock_TCJ_np.sum(axis=1)   # shape: (T, J)

# ─── Validation points from BYGB34 / BYGV06 ──────────────────────────────────
# Manually entered values derived from stock_validation.xlsx.
# Unit: number of dwellings. Years: 2011, 2015, 2020, 2025.

validation = {
    "Stuehus": {
        2011: 195_201,
        2015: 195_717,
        2020: 195_231,
        2025: 195_002,
    },
    "Parcelhus": {
        2011: 1_102_339,
        2015: 1_125_887,
        2020: 1_156_177,
        2025: 1_182_906,
    },
    "Rekkehus": {
        2011: 489_181,
        2015: 503_774,
        2020: 528_510,
        2025: 567_066,
    },
    "Etagehus": {
        2011: 959_606,
        2015: 982_219,
        2020: 1_040_890,
        2025: 1_128_849,
    },
}

# Total across all types
validation["TOTAL"] = {
    yr: sum(validation[t][yr] for t in ["Stuehus", "Parcelhus", "Rekkehus", "Etagehus"])
    for yr in [2011, 2015, 2020, 2025]
}

# ─── Plotting ────────────────────────────────────────────────────────────────
colors = {
    "Parcelhus": "#2196F3",
    "Rekkehus":  "#FF9800",
    "Etagehus":  "#4CAF50",
    "Stuehus":   "#9C27B0",
}

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()

plot_types = ["Parcelhus", "Rekkehus", "Etagehus", "Stuehus"]

for ax_idx, t in enumerate(plot_types):
    ax = axes[ax_idx]
    j  = types.index(t)

    model_vals = stock_by_type[:, j]
    color      = colors[t]

    ax.plot(years, model_vals / 1e6, color=color, linewidth=2, label="Stock_TCJ model")

    # Validation scatter points
    val_yrs  = sorted(validation[t].keys())
    val_vals = [validation[t][yr] / 1e6 for yr in val_yrs]
    ax.scatter(val_yrs, val_vals, color="black", zorder=5,
               s=60, marker="D", label="BYGB34 / BYGV06")

    # Annotate each point with percentage deviation
    for yr, vv in zip(val_yrs, val_vals):
        yr_idx     = np.where(years == yr)[0]
        if len(yr_idx) == 0:
            continue
        model_at_yr = model_vals[yr_idx[0]] / 1e6
        pct_diff    = (model_at_yr - vv) / vv * 100
        ax.annotate(f"{pct_diff:+.1f}%",
                    xy=(yr, vv),
                    xytext=(8, 5), textcoords="offset points",
                    fontsize=8, color="dimgray")

    ax.set_title(t, fontsize=12, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Dwellings [millions]")
    ax.set_xlim(1900, 2030)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

# ─── Total panel ─────────────────────────────────────────────────────────────
ax_total = axes[4]
total_model = stock_by_type.sum(axis=1)   # sum over J

ax_total.plot(years, total_model / 1e6, color="steelblue", linewidth=2,
              label="Stock_TCJ total")

val_yrs  = sorted(validation["TOTAL"].keys())
val_vals = [validation["TOTAL"][yr] / 1e6 for yr in val_yrs]
ax_total.scatter(val_yrs, val_vals, color="black", zorder=5, s=60,
                 marker="D", label="BYGB34 / BYGV06 total")

for yr, vv in zip(val_yrs, val_vals):
    yr_idx = np.where(years == yr)[0]
    if len(yr_idx) == 0:
        continue
    model_at_yr = total_model[yr_idx[0]] / 1e6
    pct_diff    = (model_at_yr - vv) / vv * 100
    ax_total.annotate(f"{pct_diff:+.1f}%",
                      xy=(yr, vv),
                      xytext=(8, 5), textcoords="offset points",
                      fontsize=8, color="dimgray")

ax_total.set_title("ALL TYPES — total", fontsize=12, fontweight="bold")
ax_total.set_xlabel("Year")
ax_total.set_ylabel("Dwellings [millions]")
ax_total.set_xlim(1900, 2030)
ax_total.legend(fontsize=8)
ax_total.grid(alpha=0.3)

# ─── Summary table panel ─────────────────────────────────────────────────────
ax_tab = axes[5]
ax_tab.axis("off")

col_labels = ["Type", "Year", "Model [k]", "Stat [k]", "Diff [%]"]
rows_data  = []

for t in plot_types + ["TOTAL"]:
    if t == "TOTAL":
        j_vals = total_model
    else:
        j = types.index(t)
        j_vals = stock_by_type[:, j]

    for yr in [2011, 2020, 2025]:
        yr_idx = np.where(years == yr)[0]
        if len(yr_idx) == 0:
            continue
        m_val = j_vals[yr_idx[0]]
        s_val = validation[t][yr] if yr in validation[t] else np.nan
        pct   = (m_val - s_val) / s_val * 100 if s_val else np.nan
        rows_data.append([
            t if yr == 2011 else "",
            str(yr),
            f"{m_val/1000:,.0f}",
            f"{s_val/1000:,.0f}",
            f"{pct:+.1f}%"
        ])

table = ax_tab.table(
    cellText=rows_data,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
    bbox=[0, 0, 1, 1]
)
table.auto_set_font_size(False)
table.set_fontsize(8)
ax_tab.set_title("Validation summary", fontsize=11, fontweight="bold")

fig.suptitle(
    "Stock_TCJ validation against Danmarks Statistik (BYGB34 / BYGV06)\n"
    "Diamonds = registry-derived dwelling counts  |  % = model deviation from registry",
    fontsize=11
)
plt.tight_layout()
plt.savefig("Stock_TCJ_validation.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: Stock_TCJ_validation.png")
