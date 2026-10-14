"""Gaya kartu bersama untuk seri #Belajar Data Olahraga (kartu 1080x1350 px).
Dipakai oleh make_cards.py di folder day04 dan day05.
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# ---------- gaya ----------
FONT = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
BG, INK, MUTED, LINE, GREY = "#F4F0E6", "#1B1F3B", "#6E6B63", "#DDD7C9", "#C2BCAE"
PERSIB, BORNEO, PERSIJA = "#2A64C8", "#8B1E1E", "#F28C28"
plt.rcParams.update({
    "font.family": FONT, "text.color": INK, "axes.edgecolor": GREY, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13,
    "axes.labelsize": 13, "axes.spines.top": False, "axes.spines.right": False,
    "axes.facecolor": BG, "figure.facecolor": BG, "axes.grid": True, "grid.color": LINE,
    "grid.linewidth": 1, "savefig.facecolor": BG,
})
W, H, DPI = 8, 10, 135  # 1080 x 1350 px


def card(day, kicker, headline, sub, hashtags):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    fig.text(.07, .955, f"{kicker}  ·  #{day}", fontsize=12, color=MUTED, fontweight="bold", va="top")
    fig.text(.07, .925, headline, fontsize=36 if "\n" in headline else 54, fontweight="black", va="top", linespacing=1.05)
    fig.text(.07, .80 if "\n" in headline else .825, sub, fontsize=15, color=MUTED, va="top", linespacing=1.35)
    fig.add_artist(plt.Line2D([.07, .93], [.065, .065], color=INK, lw=1.2))
    fig.text(.07, .04, "Data: SofaScore via @ulik.data.bola  ·  Viz: Belajar Baca Data", fontsize=11, color=MUTED, va="center")
    fig.text(.93, .955, hashtags, fontsize=11, color=MUTED, va="top", ha="right")
    return fig



def make_saver(out_dir):
    """Kembalikan fungsi save(fig, name) yang menyimpan ke out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

    def save(fig, name):
        fig.savefig(out_dir / name, dpi=DPI)
        plt.close(fig)
        print("saved", out_dir / name)
    return save
