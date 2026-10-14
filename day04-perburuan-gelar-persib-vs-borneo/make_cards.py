"""#Day4: perburuan gelar Borneo vs Persib + kamus xG (3 kartu).
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


# ======================= DAY 4 — kartu 1 =======================
fig = card("Day4", "SUPER LEAGUE 2025/26", "79 = 79",
           "Borneo FC dan Persib finis dengan poin\nsama setelah 34 laga.", "#SuperLeague #Persib #BorneoFC")
ax = fig.add_axes([.10, .13, .74, .60])
for t, d in tm.groupby("team"):
    if t not in (B, P, "Persija Jakarta"):
        ax.plot(d.match_no, d.cum_pts, color=GREY, lw=1, alpha=.6)
for t, c, dy in [("Persija Jakarta", PERSIJA, 0), (P, PERSIB, 9), (B, BORNEO, -9)]:
    d = tm[tm.team == t]
    ax.plot(d.match_no, d.cum_pts, color=c, lw=3.4, solid_capstyle="round")
    ax.scatter(d.match_no.iloc[-1], d.cum_pts.iloc[-1], s=80, color=c, edgecolor=BG, lw=2.5, zorder=5)
    ax.annotate(f"{t.split()[0]}  {d.cum_pts.iloc[-1]}", (d.match_no.iloc[-1], d.cum_pts.iloc[-1]),
                xytext=(10, dy), textcoords="offset points", va="center", color=c, fontsize=14, fontweight="bold")
ax.set_xlim(1, 34); ax.set_ylim(0, 86)
ax.set_xticks([1, 10, 20, 30, 34]); ax.grid(axis="x", visible=False)
ax.set_xlabel("Laga ke-"); ax.set_ylabel("Poin kumulatif")
ax.text(1.5, 82, "Abu-abu = 15 tim lain", fontsize=11, color=MUTED, va="top")
save(fig, "day4_1_title_race.png")

# ======================= DAY 4 — kartu 2 =======================
lo = int(gap.idxmin())
fig = card("Day4", "SUPER LEAGUE 2025/26", "Tertinggal 8 poin,\nlalu berbalik memimpin",
           "Selisih poin keduanya setelah jumlah laga yang sama.\nKotak abu-abu = poin sama.", "#SuperLeague #Persib #BorneoFC")
ax = fig.add_axes([.12, .325, .82, .38])
ax.bar(gap.index, gap.values, width=.72,
       color=[PERSIB if v > 0 else BORNEO if v < 0 else GREY for v in gap])
ax.axhline(0, color=INK, lw=1)
seri = gap[gap == 0]
ax.scatter(seri.index, seri.values, marker="s", s=55, color="#9C968A", zorder=3)
ax.set_ylim(-10.5, 6.5); ax.set_xlim(.3, 34.7); ax.grid(axis="x", visible=False)
ax.set_xticks([1, 10, 20, 30, 34]); ax.set_xlabel("Laga ke-")
ax.text(lo + .9, gap.min() - .5, f"−8 di laga ke-{lo}", fontsize=13, color=BORNEO, fontweight="bold", va="top")
ax.text(21, 4.6, "+4: Persib di depan", fontsize=13, color=PERSIB, fontweight="bold", va="bottom")
ax.text(.3, 6.2, "▲ Persib unggul", fontsize=11, color=PERSIB, va="top")
ax.text(.3, -10.2, "▼ Borneo unggul", fontsize=11, color=BORNEO, va="bottom")

# strip head-to-head
fig.text(.07, .245, "HEAD-TO-HEAD", fontsize=12, color=MUTED, fontweight="bold")
for i, (_, r) in enumerate(h2h.iterrows()):
    x = .07 + i * .44
    home = r.side == "home"
    score = f"Persib {r.goals_for}–{r.goals_against} Borneo" if home else f"Borneo {r.goals_against}–{r.goals_for} Persib"
    fig.patches.append(plt.Rectangle((x, .105), .42, .12, transform=fig.transFigure,
                                     facecolor="white", edgecolor=LINE, lw=1))
    fig.text(x + .025, .195, f"Pekan {r['round']}  ·  {'kandang Persib' if home else 'kandang Borneo'}",
             fontsize=11, color=MUTED, va="center")
    fig.text(x + .025, .145, score, fontsize=18, fontweight="bold", va="center")
save(fig, "day4_2_points_gap.png")


# ======================= DAY 4 — kartu 3 (kamus: apa itu xG?) =======================
fig = card("Day4", "KAMUS DATA", "Apa itu xG?",
           "Expected goals: seberapa besar peluang sebuah\ntembakan jadi gol, dalam angka 0 sampai 1.",
           "#BelajarDataOlahraga")
examples = [("Penalti", 76), ("1 lawan 1\ndengan kiper", 35), ("Tembakan dari\nluar kotak", 4)]
for k, (label, n) in enumerate(examples):
    x0 = .07 + k * .30
    fig.text(x0, .715, label, fontsize=15, fontweight="bold", va="top", linespacing=1.15)
    ax = fig.add_axes([x0, .43, .24, .24 * W / H])
    ax.set_xlim(-.5, 9.5); ax.set_ylim(-.5, 9.5); ax.axis("off")
    for i in range(100):
        r, c = divmod(i, 10)
        ax.scatter(c, 9 - r, s=46, marker="o", color=INK if i < n else LINE, lw=0)
    fig.text(x0, .40, f"≈ {n/100:.2f}".replace(".", ","), fontsize=30, fontweight="black", va="top")
    fig.text(x0, .345, f"kira-kira {n} dari 100\ntembakan seperti ini jadi gol", fontsize=12, color=MUTED, va="top", linespacing=1.3)
fig.add_artist(plt.Line2D([.07, .93], [.255, .255], color=LINE, lw=1))
fig.text(.07, .235, "xG TIM = jumlah xG semua tembakannya", fontsize=12, color=MUTED, fontweight="bold", va="top")
fig.text(.07, .195, f"Persib rata-rata mengumpulkan {q.loc[P].xg_for:.2f} xG per laga:".replace(".", ","),
         fontsize=15, va="top")
fig.text(.07, .158, "peluangnya “bernilai” hampir 2 gol setiap pertandingan.", fontsize=15, va="top")
fig.text(.07, .10, "Angka contoh di atas adalah ilustrasi; nilai pastinya berbeda tergantung model xG.",
         fontsize=11, color=MUTED, style="italic", va="top")
save(fig, "day4_3_kamus_xg.png")

