"""Kartu 4:5 untuk #Day6 Belajar Data Olahraga: Egy Maulana Vikri.
Pakai player_season_summary.csv & player_match_summary.csv (Super League 2025/26).
Fakta 2026/27 & ASEAN Cup diambil dari berita (iNews, VIVA, detik), bukan dari dataset.
Jalankan: python make_cards.py -> hasil di folder output/
Butuh di data/: player_season_summary.csv, player_match_summary.csv, egy_shotmap_2526.csv
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)

# ---------- gaya (sama dengan social_cards.py) ----------
FONT = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
BG, INK, MUTED, LINE, GREY = "#F4F0E6", "#1B1F3B", "#6E6B63", "#DDD7C9", "#C2BCAE"
ACC = "#B5541C"            # aksen Egy
LIGHT = "#E3C9B8"          # aksen versi terang
plt.rcParams.update({
    "font.family": FONT, "text.color": INK, "axes.edgecolor": GREY, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13,
    "axes.spines.top": False, "axes.spines.right": False, "axes.facecolor": BG,
    "figure.facecolor": BG, "savefig.facecolor": BG,
})
W, H, DPI = 8, 10, 135  # 1080 x 1350 px
TAGS = "#SuperLeague #Timnas #DewaUnited"


def card(kicker, headline, sub, source="Data: SofaScore via @ulik.data.bola  ·  Viz: Belajar Baca Data"):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    fig.text(.07, .955, f"{kicker}  ·  #Day6", fontsize=12, color=MUTED, fontweight="bold", va="top")
    fig.text(.93, .955, TAGS, fontsize=11, color=MUTED, va="top", ha="right")
    fig.text(.07, .925, headline, fontsize=36 if "\n" in headline else 50, fontweight="black", va="top", linespacing=1.05)
    fig.text(.07, .80 if "\n" in headline else .835, sub, fontsize=15, color=MUTED, va="top", linespacing=1.35)
    fig.add_artist(plt.Line2D([.07, .93], [.065, .065], color=INK, lw=1.2))
    fig.text(.07, .04, source, fontsize=10.5, color=MUTED, va="center")
    return fig


def f(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def save(fig, name):
    fig.savefig(OUT / name, dpi=DPI)
    plt.close(fig)
    print("saved", OUT / name)


# ---------- data ----------
ps = pd.read_csv(DATA / "player_season_summary.csv")
pm = pd.read_csv(DATA / "player_match_summary.csv")
EGY = "Egy Maulana Vikri"
s = ps[ps.player == EGY].iloc[0]
m = pm[pm.player == EGY].copy()
m["peran"] = m.is_starter.map({True: "Starter", False: "Pengganti"})
split = m.groupby("peran").agg(menit=("minutes_played", "sum"), shots=("shots", "sum"),
                               drib=("successful_dribbles", "sum"), kp=("key_passes", "sum"),
                               rating=("rating", "mean"), laga=("match_id", "size"))
for c in ["shots", "drib", "kp"]:
    split[c + "90"] = split[c] / split.menit * 90

# Kartu 1 = poster (lihat make_poster.py)

# ======================= KARTU 2 — shot map 36 tembakan =======================
# egy_shotmap_2526.csv diambil lewat Console Chrome (lihat egy_shotmap_console.js).
# Koordinat SofaScore: x = jarak dari garis gawang (% panjang lapangan),
# y = posisi melebar (% lebar), y > 50 = sisi kanan dilihat dari penyerang.
PL, PW = 105, 68
sh = pd.read_csv(DATA / "egy_shotmap_2526.csv").merge(
    m[["match_id", "opponent", "is_starter", "round"]], on="match_id", how="left")
sh["d"] = sh.x / 100 * PL                 # meter dari garis gawang
sh["w"] = sh.y / 100 * PW                 # meter dari sisi kiri
sh["dist_m"] = ((sh.d) ** 2 + (sh.w - PW / 2) ** 2) ** .5
sh["in_box"] = (sh.d <= 16.5) & (sh.w.between(PW / 2 - 20.16, PW / 2 + 20.16))
RES = {"save": ("Diselamatkan kiper", INK), "block": ("Terblok", ACC), "miss": ("Melenceng", GREY)}


def half_pitch(ax, depth=32):
    """Setengah lapangan vertikal, gawang di atas. Sumbu: horizontal = lebar (m), vertikal = jarak dari gawang."""
    kw = dict(color=GREY, lw=1.3, zorder=1)
    ax.plot([0, PW, PW, 0, 0], [0, 0, depth, depth, 0], **kw)
    ax.plot([PW/2-20.16, PW/2-20.16, PW/2+20.16, PW/2+20.16], [0, 16.5, 16.5, 0], **kw)
    ax.plot([PW/2-9.16, PW/2-9.16, PW/2+9.16, PW/2+9.16], [0, 5.5, 5.5, 0], **kw)
    ax.plot([PW/2-3.66, PW/2-3.66, PW/2+3.66, PW/2+3.66], [0, -1.8, -1.8, 0], color=INK, lw=2, zorder=1)
    ax.scatter(PW/2, 11, s=8, color=GREY, zorder=1)
    t = np.linspace(0, 2 * np.pi, 200)
    ax_, ay_ = PW/2 + 9.15 * np.cos(t), 11 + 9.15 * np.sin(t)
    k = ay_ > 16.5
    ax.plot(ax_[k], ay_[k], **kw)
    ax.set_xlim(-1.5, PW + 1.5); ax.set_ylim(depth + .5, -3)   # gawang di atas
    ax.set_aspect("equal"); ax.axis("off")


def plot_shots(ax, df, smin=60, smax=1500):
    for r, (label, col) in RES.items():
        d = df[df.result == r]
        ax.scatter(d.w, d.d, s=smin + d.xg / .7 * smax, color=col, alpha=.9 if r != "miss" else .75,
                   edgecolor=BG, lw=1.4, zorder=3)


fig = card("SUPER LEAGUE 2025/26", "36 tembakan,\n0 gol",
           "Setiap titik = satu tembakan Egy. Makin besar\ntitiknya, makin besar peluang golnya (xG).")
ax = fig.add_axes([.07, .31, .86, .45])
half_pitch(ax)
plot_shots(ax, sh)
top = sh.sort_values("xg").iloc[-1]
ax.annotate(f"Peluang terbesar: xG {f(top.xg, 2)}\nvs {top.opponent}, diselamatkan",
            (top.w, top.d), xytext=(PW * .02, 9), fontsize=11.5, color=INK, fontweight="bold", va="center",
            arrowprops=dict(arrowstyle="-", color=INK, lw=1))
# legenda
for j, (r, (label, col)) in enumerate(RES.items()):
    n = int((sh.result == r).sum())
    x = .07 + j * .30
    fig.text(x, .29, str(n), fontsize=34, fontweight="black", color=col if col != GREY else MUTED, va="top")
    fig.text(x, .225, label, fontsize=12.5, color=MUTED, va="top")
fig.add_artist(plt.Line2D([.07, .93], [.18, .18], color=LINE, lw=1))
inb, outb = sh[sh.in_box], sh[~sh.in_box]
fig.text(.07, .16, f"Dari luar kotak penalti: {len(outb)} tembakan, hanya {int((outb.result == 'save').sum())} yang mengarah ke gawang.",
         fontsize=12.5, va="top")
fig.text(.07, .118, f"Total xG {f(sh.xg.sum(), 2)}: seharusnya sekitar 3 gol.", fontsize=12.5, color=MUTED, va="top")
save(fig, "day6_2_shotmap.png")

# ======================= KARTU 3 — profil supersub =======================
st, sb = split.loc["Starter"], split.loc["Pengganti"]
fig = card("SUPER LEAGUE 2025/26", "Lebih eksplosif\ndari bangku cadangan",
           f"Per 90 menit: saat starter ({int(st.laga)} laga) vs saat masuk\nsebagai pengganti ({int(sb.laga)} laga).",
           source="Data: SofaScore via @ulik.data.bola  ·  ASEAN Cup: detik  ·  Viz: Belajar Baca Data")
rows = [("Tembakan", st.shots90, sb.shots90), ("Dribel sukses", st.drib90, sb.drib90), ("Key passes", st.kp90, sb.kp90)]
ax = fig.add_axes([.07, .37, .86, .30])
ax.set_xlim(0, 5.2); ax.set_ylim(-.6, len(rows) - .3); ax.axis("off")
for i, (lbl, a, b) in enumerate(rows):
    y = len(rows) - 1 - i
    ax.text(0, y + .38, lbl, fontsize=15, fontweight="bold", va="center")
    ax.plot([a, b], [y, y], color=LINE, lw=5, solid_capstyle="round", zorder=1)
    ax.scatter(a, y, s=320, color=GREY, zorder=2)
    ax.scatter(b, y, s=320, color=ACC, zorder=3)
    if abs(b - a) > .3:
        ax.text(a, y - .3, f(a), ha="center", fontsize=13, color=MUTED, va="center")
        ax.text(b, y - .3, f(b), ha="center", fontsize=13, color=ACC, fontweight="bold", va="center")
    else:
        ax.text(b + .25, y, f"{f(a)} vs {f(b)}", fontsize=13, color=MUTED, va="center")
fig.text(.07, .695, "●", color=GREY, fontsize=15, va="center"); fig.text(.10, .695, "Starter", fontsize=13, color=MUTED, va="center")
fig.text(.25, .695, "●", color=ACC, fontsize=15, va="center"); fig.text(.28, .695, "Pengganti", fontsize=13, color=MUTED, va="center")

fig.add_artist(plt.Line2D([.07, .93], [.33, .33], color=LINE, lw=1))
fig.text(.07, .305, "PROFIL YANG SAMA DI FIFA ASEAN CUP 2026", fontsize=12, color=MUTED, fontweight="bold", va="top")
fig.text(.07, .265, "2 kali masuk dari bangku cadangan, total 36 menit:", fontsize=14, va="top")
fig.text(.07, .225, "•  vs Bangladesh: umpan panjang yang berujung gol (pre-assist)", fontsize=14, va="top")
fig.text(.07, .19, "•  Final vs Thailand: terlibat di gol penyama kedudukan", fontsize=14, va="top")
fig.text(.07, .125, f"Catatan: menit sebagai pengganti hanya {int(sb.menit)}. Rating rata-ratanya tetap lebih\n"
         f"tinggi saat starter ({f(st.rating, 2)} vs {f(sb.rating, 2)}).",
         fontsize=11, color=MUTED, style="italic", va="top", linespacing=1.35)
save(fig, "day6_3_supersub.png")


# ======================= KARTU 4 — starter vs pengganti (shot map) =======================
fig = card("SUPER LEAGUE 2025/26", "Dari bangku cadangan,\nmenembak dari lebih jauh",
           "Saat masuk sebagai pengganti, Egy lebih sering menembak,\ntapi dari posisi yang lebih sulit.")
for j, (is_st, label) in enumerate([(True, "Saat starter"), (False, "Saat pengganti")]):
    d = sh[sh.is_starter == is_st]
    x0 = .07 + j * .45
    ax = fig.add_axes([x0, .43, .41, .27])
    half_pitch(ax)
    plot_shots(ax, d, smin=30, smax=800)
    fig.text(x0, .705, label, fontsize=16, fontweight="bold", va="bottom")
    stats = [(str(len(d)), "tembakan"),
             (f"{round(d.in_box.mean() * 100)}%", "dari dalam kotak penalti"),
             (f"{f(d.dist_m.mean())} m", "rata-rata jarak ke gawang"),
             (f(d.xg.mean(), 2), "xG per tembakan")]
    for i, (v, lbl) in enumerate(stats):
        y = .40 - i * .068
        fig.text(x0, y, v, fontsize=20, fontweight="black", color=ACC if not is_st else INK, va="top")
        fig.text(x0 + .17, y - .01, lbl, fontsize=11.5, color=MUTED, va="top")
for k, (r, (label, col)) in enumerate(RES.items()):
    fig.text(.07 + k * .25, .1, "●", color=col, fontsize=14, va="center")
    fig.text(.10 + k * .25, .1, label, fontsize=11, color=MUTED, va="center")
save(fig, "day6_4_starter_vs_pengganti.png")
