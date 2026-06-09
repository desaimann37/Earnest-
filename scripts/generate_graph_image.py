"""
Generates a polished agent pipeline diagram for presentation.
Output: agent_pipeline.png
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_pipeline.png")

# ── Data ────────────────────────────────────────────────────────────────────

AGENTS = [
    {
        "name": "Ingestion Agent",
        "icon": "IN",
        "action": "Classifies & parses PDFs",
        "output": "Document index JSON",
        "color": "#1a3c5e",
    },
    {
        "name": "Financial Spreader",
        "icon": "P&L",
        "action": "Extracts 3-year income statement into DataFrame",
        "output": "spread.csv  |  metrics JSON",
        "color": "#1a4f7a",
    },
    {
        "name": "EBITDA Normalizer",
        "icon": "$+",
        "action": "Identifies add-backs from bank statements",
        "output": "ebitda_bridge.json",
        "color": "#1e6091",
    },
    {
        "name": "Concentration Analyzer",
        "icon": "%",
        "action": "Computes customer revenue concentration",
        "output": "concentration.json",
        "color": "#2874a6",
    },
    {
        "name": "Risk Flagger",
        "icon": "!",
        "action": "Synthesizes 5-7 ranked risk flags",
        "output": "risks.json",
        "color": "#2e86c1",
    },
    {
        "name": "Memo Writer",
        "icon": "QoE",
        "action": "Drafts full QoE memo with source citations",
        "output": "memo.md",
        "color": "#2196a6",
    },
    {
        "name": "PDF Exporter",
        "icon": "PDF",
        "action": "Renders polished PDF memorandum",
        "output": "memo.pdf",
        "color": "#148f77",
    },
]

INPUT_LABEL  = "P&L · Bank Statement · Customer List"
OUTPUT_LABEL = "Quality of Earnings Memorandum (PDF)"

# ── Layout ───────────────────────────────────────────────────────────────────

FIG_W, FIG_H = 13, 17
BOX_W, BOX_H = 8.5, 1.35
X_CENTER      = FIG_W / 2
TOP_PAD       = 1.2
GAP           = 0.42        # vertical gap between boxes
STEP          = BOX_H + GAP

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("#f8f9fa")

# ── Title ────────────────────────────────────────────────────────────────────

ax.text(X_CENTER, FIG_H - 0.45, "Earnest by Verity — Agent Pipeline",
        ha="center", va="center", fontsize=18, fontweight="bold",
        color="#1a3c5e",
        fontfamily="DejaVu Sans")
ax.text(X_CENTER, FIG_H - 0.85, "7-agent LangGraph sequence · claude-sonnet-4-6",
        ha="center", va="center", fontsize=10, color="#666666")

# thin title underline
ax.axhline(y=FIG_H - 1.05, xmin=0.05, xmax=0.95,
           color="#1a3c5e", linewidth=1.2, alpha=0.4)

# ── Input bubble ─────────────────────────────────────────────────────────────

in_y = FIG_H - TOP_PAD - 0.8
in_box = FancyBboxPatch(
    (X_CENTER - 4, in_y - 0.28), 8, 0.56,
    boxstyle="round,pad=0.08",
    facecolor="#e8f0f7", edgecolor="#1a3c5e", linewidth=1.5,
)
ax.add_patch(in_box)
ax.text(X_CENTER, in_y, f"INPUT:  {INPUT_LABEL}",
        ha="center", va="center", fontsize=10, color="#1a3c5e", fontweight="bold")

# arrow from input to first agent
first_agent_top = FIG_H - TOP_PAD - 0.8 - 0.28 - GAP - BOX_H + BOX_H
arrow_start_y   = in_y - 0.28
first_box_top_y = FIG_H - TOP_PAD - 1.5

ax.annotate("", xy=(X_CENTER, first_box_top_y + BOX_H + 0.04),
            xytext=(X_CENTER, arrow_start_y - 0.04),
            arrowprops=dict(arrowstyle="-|>", color="#1a3c5e",
                            lw=1.8, mutation_scale=14))

# ── Agent boxes ───────────────────────────────────────────────────────────────

box_left  = X_CENTER - BOX_W / 2
BADGE_W   = 1.6

for i, agent in enumerate(AGENTS):
    y_top = FIG_H - TOP_PAD - 1.5 - i * STEP
    y_mid = y_top - BOX_H / 2

    # Shadow
    shadow = FancyBboxPatch(
        (box_left + 0.06, y_top - BOX_H - 0.06), BOX_W, BOX_H,
        boxstyle="round,pad=0.12",
        facecolor="#cccccc", edgecolor="none", alpha=0.5, zorder=1
    )
    ax.add_patch(shadow)

    # Main box (white body)
    main_box = FancyBboxPatch(
        (box_left, y_top - BOX_H), BOX_W, BOX_H,
        boxstyle="round,pad=0.12",
        facecolor="white", edgecolor=agent["color"], linewidth=2.0, zorder=2
    )
    ax.add_patch(main_box)

    # Color badge (left strip)
    badge = FancyBboxPatch(
        (box_left, y_top - BOX_H), BADGE_W, BOX_H,
        boxstyle="round,pad=0.12",
        facecolor=agent["color"], edgecolor="none", zorder=3
    )
    ax.add_patch(badge)

    # Step number
    ax.text(box_left + 0.32, y_mid + 0.26,
            f"{i+1}", ha="center", va="center",
            fontsize=13, fontweight="bold", color="white", zorder=4)

    # Icon text
    ax.text(box_left + 0.32, y_mid - 0.22,
            agent["icon"], ha="center", va="center",
            fontsize=8, fontweight="bold", color="white", alpha=0.85, zorder=4)

    # Agent name
    ax.text(box_left + BADGE_W + 0.22, y_mid + 0.27,
            agent["name"], ha="left", va="center",
            fontsize=11, fontweight="bold", color="#1a3c5e", zorder=4)

    # Action
    ax.text(box_left + BADGE_W + 0.22, y_mid + 0.02,
            agent["action"], ha="left", va="center",
            fontsize=9, color="#444444", zorder=4)

    # Output pill
    pill = FancyBboxPatch(
        (box_left + BADGE_W + 0.18, y_top - BOX_H + 0.10),
        BOX_W - BADGE_W - 0.25, 0.32,
        boxstyle="round,pad=0.05",
        facecolor="#e8f0f7", edgecolor=agent["color"],
        linewidth=0.8, zorder=4
    )
    ax.add_patch(pill)
    ax.text(box_left + BADGE_W + 0.22 + (BOX_W - BADGE_W - 0.25) / 2,
            y_top - BOX_H + 0.26,
            f"→ {agent['output']}",
            ha="center", va="center",
            fontsize=8, color=agent["color"], fontstyle="italic", zorder=5)

    # Arrow to next agent (except last)
    if i < len(AGENTS) - 1:
        next_top = FIG_H - TOP_PAD - 1.5 - (i + 1) * STEP
        ax.annotate("",
                    xy=(X_CENTER, next_top + 0.04),
                    xytext=(X_CENTER, y_top - BOX_H - 0.04),
                    arrowprops=dict(arrowstyle="-|>", color="#1a3c5e",
                                    lw=1.8, mutation_scale=14),
                    zorder=2)

# ── Output bubble ─────────────────────────────────────────────────────────────

last_y = FIG_H - TOP_PAD - 1.5 - (len(AGENTS) - 1) * STEP - BOX_H
out_y  = last_y - GAP - 0.3

ax.annotate("",
            xy=(X_CENTER, out_y + 0.28 + 0.04),
            xytext=(X_CENTER, last_y - 0.04),
            arrowprops=dict(arrowstyle="-|>", color="#148f77",
                            lw=1.8, mutation_scale=14))

out_box = FancyBboxPatch(
    (X_CENTER - 4, out_y - 0.28), 8, 0.56,
    boxstyle="round,pad=0.08",
    facecolor="#d5f5e3", edgecolor="#148f77", linewidth=2.0,
)
ax.add_patch(out_box)
ax.text(X_CENTER, out_y, f"OUTPUT:  {OUTPUT_LABEL}",
        ha="center", va="center", fontsize=10.5,
        color="#148f77", fontweight="bold")

# ── LangGraph + model badge ───────────────────────────────────────────────────

ax.text(FIG_W - 0.2, 0.25,
        "Verity · Powered by LangGraph · Anthropic claude-sonnet-4-6",
        ha="right", va="center", fontsize=8, color="#aaaaaa")

# ── Save ─────────────────────────────────────────────────────────────────────

plt.tight_layout(pad=0)
plt.savefig(OUT, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {OUT}")
