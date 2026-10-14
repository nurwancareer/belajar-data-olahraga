"""#Day5: Borneo vs Persib lewat xG (4 kartu, kartu 4 landscape).
Jalankan dari mana saja:  python make_cards.py   -> hasil di folder output/
Butuh data/team_match_summary.csv (lihat data/README.md).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import *  # noqa: E402,F403  (gaya, warna, card(), DATA)

save = make_saver(HERE / "output")

# ---------- data (sama dengan notebook) ----------
tm = pd.read_csv(DATA / "team_match_summary.csv", parse_dates=["match_date"])
tm = tm.sort_values(["team", "match_date"]).reset_index(drop=True).copy()
tm["match_no"] = tm.groupby("team").cumcount() + 1
tm["cum_pts"] = tm.groupby("team").points.cumsum()
tm["xgd"] = tm.xg_for - tm.xg_against
tm["xgd_roll5"] = tm.groupby("team").xgd.transform(lambda s: s.rolling(5, min_periods=3).mean())

q = (tm.dropna(subset=["xg_for", "xg_against"]).groupby("team")
       .agg(xg_for=("xg_for", "mean"), xg_against=("xg_against", "mean"),
            gf=("goals_for", "mean"), ga=("goals_against", "mean")))
q = q.join(tm.groupby("team").points.sum().rename("pts"))
q["xgd"] = q.xg_for - q.xg_against
q["keeping"] = q.xg_against - q.ga
q["finishing"] = q.gf - q.xg_for

B, P = "Borneo FC Samarinda", "Persib Bandung"
side = lambda t: tm[tm.team == t].set_index("match_no")
gap = side(P).cum_pts - side(B).cum_pts
h2h = tm[(tm.team == P) & (tm.opponent == B)].sort_values("match_date")


# ======================= DAY 5 — kartu 1 (angka besar) =======================
bk, pk = q.loc[B], q.loc[P]
fig = card("Day5", "BORNEO VS PERSIB", "Proses vs efisiensi",
           "Poin sama, tapi cara mendapatkannya berbeda.", "#SuperLeague #xG #BorneoFC")
fig.text(.07, .70, f"+{bk.keeping:.2f}", fontsize=120, fontweight="black", color=BORNEO, va="top")
fig.text(.07, .505, "gol per laga lebih sedikit dari ekspektasi:\nBorneo kebobolan "
         f"{bk.ga:.2f} padahal xG lawan {bk.xg_against:.2f}.\nTertinggi di liga.",
         fontsize=15, va="top", linespacing=1.4)

rows = [("Selisih xG per laga", pk.xgd, bk.xgd, "{:+.2f}"),
        ("xG lawan per laga", pk.xg_against, bk.xg_against, "{:.2f}"),
        ("Gol − xG per laga", pk.finishing, bk.finishing, "{:+.2f}")]
y0 = .345
fig.text(.52, y0 + .035, "PERSIB", fontsize=12, color=PERSIB, fontweight="bold", ha="center")
fig.text(.78, y0 + .035, "BORNEO", fontsize=12, color=BORNEO, fontweight="bold", ha="center")
for i, (lbl, pv, bv, f) in enumerate(rows):
    y = y0 - i * .075
    fig.add_artist(plt.Line2D([.07, .93], [y + .025, y + .025], color=LINE, lw=1))
    fig.text(.07, y - .012, lbl, fontsize=14, color=MUTED, va="center")
    fig.text(.52, y - .012, f.format(pv), fontsize=22, fontweight="bold", ha="center", va="center")
    fig.text(.78, y - .012, f.format(bv), fontsize=22, fontweight="bold", ha="center", va="center")
fig.text(.07, .095, "Persib unggul di kualitas peluang. Borneo unggul di finishing dan pertahanan.",
         fontsize=12, color=MUTED)
save(fig, "day5_1_big_number.png")

# ======================= DAY 5 — kartu 2 (kuadran) =======================
fig = card("Day5", "SUPER LEAGUE 2025/26", "Siapa paling\ndominan?",
           "xG for vs xG against per laga. Ukuran titik = total poin.", "#SuperLeague #xG")
ax = fig.add_axes([.13, .14, .80, .60])
mx, my = q.xg_for.mean(), q.xg_against.mean()
ax.axvline(mx, color=GREY, lw=1.2, ls="--"); ax.axhline(my, color=GREY, lw=1.2, ls="--")
col = {P: PERSIB, B: BORNEO, "Persija Jakarta": PERSIJA}
s = 60 + (q.pts - q.pts.min()) / (q.pts.max() - q.pts.min()) * 520
ax.scatter(q.xg_for, q.xg_against, s=s, c=[col.get(t, "#9C968A") for t in q.index],
           edgecolor=BG, lw=2, zorder=3)
for t in col:
    r = q.loc[t]
    ax.annotate(t.split()[0], (r.xg_for, r.xg_against), xytext=(0, 18 if t != B else -22),
                textcoords="offset points", ha="center", fontsize=15, fontweight="bold", color=col[t])
ax.set_ylim(2.85, .45); ax.set_xlim(.88, 2.1)
ax.set_xlabel("xG for per laga  →  lebih banyak peluang")
ax.set_ylabel("xG against per laga  (atas = lebih sedikit)")
kw = dict(transform=ax.transAxes, fontsize=12, color=MUTED, style="italic")
ax.text(.98, .98, "Menyerang & bertahan\nbagus", ha="right", va="top", **kw)
ax.text(.02, .02, "Bermasalah di dua sisi", ha="left", va="bottom", **kw)
ax.text(.98, .02, "Terbuka", ha="right", va="bottom", **kw)
ax.text(.02, .98, "Pasif tapi solid", ha="left", va="top", **kw)
save(fig, "day5_2_xg_quadrant.png")

# ======================= DAY 5 — kartu 3 (rolling) =======================
fig = card("Day5", "BORNEO VS PERSIB", "xG minus,\ntetap menang",
           "Rata-rata 5 laga: xG for − xG against.\nDi atas 0 = peluang lebih baik dari lawan.",
           "#SuperLeague #xG #BorneoFC")
ax = fig.add_axes([.12, .14, .82, .55])
ax.axvspan(14, 26, color=BORNEO, alpha=.08, lw=0)
ax.text(20, -1.85, "Laga 14–26: xG Borneo\nmayoritas di bawah 0", ha="center", fontsize=12,
        color=BORNEO, fontweight="bold", va="bottom")
for t, c in [(P, PERSIB), (B, BORNEO)]:
    d = tm[tm.team == t]
    ax.plot(d.match_no, d.xgd_roll5, color=c, lw=3.4, solid_capstyle="round")
ax.axhline(0, color=INK, lw=1)
ax.set_ylim(-1.95, 2.1); ax.set_xlim(3, 34); ax.grid(axis="x", visible=False)
ax.set_xticks([5, 10, 15, 20, 25, 30, 34]); ax.set_xlabel("Laga ke-")
ax.text(4, 1.9, "Persib", color=PERSIB, fontsize=15, fontweight="bold", va="top")
ax.text(4, .35, "Borneo", color=BORNEO, fontsize=15, fontweight="bold", va="top")
save(fig, "day5_3_rolling_xgd.png")


# ======================= DAY 5 — kartu 4 (over/under, landscape) =======================
POS, NEG = "#55524B", "#CFC8B8"   # netral: positif gelap, negatif terang (warna tim khusus 3 tim fokus)
FOCUS = {P: PERSIB, B: BORNEO, "Persija Jakarta": PERSIJA}
SHORT = {"Borneo FC Samarinda": "Borneo", "Persib Bandung": "Persib", "Persija Jakarta": "Persija",
         "Persebaya Surabaya": "Persebaya", "Java United FC": "Java Utd", "Bali United FC": "Bali Utd",
         "Dewa United FC": "Dewa Utd", "Madura United FC": "Madura Utd", "Bhayangkara Presisi Lampung FC": "Bhayangkara",
         "Arema FC": "Arema", "PSIM Yogyakarta": "PSIM", "PSBS Biak": "PSBS", "PSM Makassar": "PSM",
         "Persis Solo": "Persis", "Persik Kediri": "Persik", "Persita Tangerang": "Persita",
         "Persijap Jepara": "Persijap", "Semen Padang FC": "Semen Padang"}

WW, WH = 12, 7.5   # 1620 x 1012 px, landscape
fig = plt.figure(figsize=(WW, WH), dpi=DPI)
fig.text(.05, .95, "SUPER LEAGUE 2025/26  ·  #Day5", fontsize=12, color=MUTED, fontweight="bold", va="top")
fig.text(.95, .95, "#SuperLeague #xG #BorneoFC", fontsize=11, color=MUTED, va="top", ha="right")
fig.text(.05, .915, "Borneo menang di efisiensi", fontsize=34, fontweight="black", va="top")
fig.text(.05, .835, "Selisih gol aktual dengan ekspektasi (xG), per laga. Positif = lebih baik dari ekspektasi.",
         fontsize=14, color=MUTED, va="top")
fig.add_artist(plt.Line2D([.05, .95], [.075, .075], color=INK, lw=1.2))
fig.text(.05, .045, "Data: SofaScore via @ulik.data.bola  ·  Viz: Belajar Baca Data", fontsize=11, color=MUTED, va="center")

o = q.sort_values("finishing")
labels = [SHORT.get(t, t) for t in o.index]
axes = [fig.add_axes([.15, .13, .36, .58]), fig.add_axes([.59, .13, .36, .58])]
panels = [("finishing", "Finishing", "gol − xG"), ("keeping", "Pertahanan", "xG lawan − kebobolan")]
for ax, (col, title, formula) in zip(axes, panels):
    v = o[col]
    colors = [FOCUS.get(t, POS if x > 0 else NEG) for t, x in v.items()]
    ax.barh(range(len(v)), v.values, height=.66, color=colors)
    ax.axvline(0, color=INK, lw=1)
    ax.set_yticks(range(len(v)))
    ax.set_yticklabels(labels if ax is axes[0] else [""] * len(v), fontsize=12)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(v.min() - .14, v.max() + .14)
    x0 = ax.get_position().x0
    fig.text(x0, .765, title, fontsize=16, fontweight="bold", va="bottom")
    fig.text(x0, .76, formula + " per laga", fontsize=12, color=MUTED, va="top")
    for i, (t, x) in enumerate(v.items()):
        foc = t in FOCUS
        ax.text(x + (.012 if x >= 0 else -.012), i, f"{x:+.2f}", va="center", ha="left" if x >= 0 else "right",
                fontsize=11 if not foc else 12, color=FOCUS.get(t, MUTED), fontweight="bold" if foc else "normal")
for lbl in axes[0].get_yticklabels():
    for t, c in FOCUS.items():
        if lbl.get_text() == SHORT[t]:
            lbl.set_color(c); lbl.set_fontweight("bold")
# keterangan warna
fig.text(.665, .045, "■", color=POS, fontsize=13, va="center"); fig.text(.68, .045, "di atas ekspektasi", fontsize=11, color=MUTED, va="center")
fig.text(.81, .045, "■", color=NEG, fontsize=13, va="center"); fig.text(.825, .045, "di bawah ekspektasi", fontsize=11, color=MUTED, va="center")
save(fig, "day5_4_over_under.png")
