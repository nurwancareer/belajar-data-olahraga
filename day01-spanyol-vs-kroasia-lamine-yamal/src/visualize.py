"""
Visualisasi pertandingan dari data SofaScore.

Dua output:
1. buat_match_report     : skor + insight + shotmap kedua tim (statistik di dalam lapangan) + xG flow
2. buat_shotmap_per_tim  : dua setengah lapangan vertikal berdampingan, satu per tim

Keduanya mendukung bahasa Indonesia (bahasa="id") dan Inggris (bahasa="en").
"""
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import to_rgb
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle
from mplsoccer import Pitch, VerticalPitch

# ---------------------------------------------------------------- palet warna
BG = "#f6f3ee"        # latar off-white
INK = "#1b1b1b"       # teks utama
MUTED = "#8a857c"     # teks sekunder
LINE = "#c9c3b8"      # garis lapangan
GRID = "#e4dfd6"      # grid grafik
PANEL = "#ece7df"     # latar kotak legend


# ---------------------------------------------------------------- font
def _pilih_font():
    """Pakai font condensed pertama yang terinstal; kalau tidak ada, DejaVu Sans."""
    kandidat = ["Barlow Condensed", "Oswald", "Roboto Condensed", "Arial Narrow", "DejaVu Sans"]
    tersedia = {f.name for f in font_manager.fontManager.ttflist}
    nama = next((k for k in kandidat if k in tersedia), "DejaVu Sans")
    stretch = "condensed" if nama == "DejaVu Sans" else "normal"
    return (FontProperties(family=nama, weight="bold", stretch=stretch),
            FontProperties(family=nama, weight="normal", stretch=stretch))


FONT_TEBAL, FONT_BIASA = _pilih_font()


def _f(tebal=True, size=12):
    fp = (FONT_TEBAL if tebal else FONT_BIASA).copy()
    fp.set_size(size)
    return fp


# ---------------------------------------------------------------- teks per bahasa
TEKS = {
    "id": {
        "gol": "GOL", "xg": "xG", "tembakan": "TEMBAKAN", "tepat": "TEPAT SASARAN",
        "possession": "PENGUASAAN BOLA", "passing": "AKURASI OPERAN",
        "serangan_home": "← SERANGAN {tim}", "serangan_away": "SERANGAN {tim} →",
        "goal": "Gol", "save": "Diselamatkan kiper", "block": "Diblok", "miss": "Melenceng",
        "flow_judul": "xG FLOW",
        "data": "Data", "viz": "Visualisasi",
        "insight": ("{unggul} unggul xG {xg_u} berbanding {xg_k} dari {shot_u} tembakan, "
                    "sementara {kalah} melepaskan {shot_k} tembakan."),
        "desimal": ",",
        "sm_judul": "{tim} – Shot Map",
        "sm_sub": "Semua tembakan open-play & set piece",
        "sm_ringkas": "{gol} gol  ·  {shot} tembakan  ·  {xg} xG",
        "sm_hasil": "Hasil",
    },
    "en": {
        "gol": "GOALS", "xg": "xG", "tembakan": "SHOTS", "tepat": "SHOTS ON TARGET",
        "possession": "POSSESSION", "passing": "PASS ACCURACY",
        "serangan_home": "← {tim} ATTACKING", "serangan_away": "{tim} ATTACKING →",
        "goal": "Goal", "save": "Saved", "block": "Blocked", "miss": "Off target",
        "flow_judul": "xG FLOW",
        "data": "Data", "viz": "Viz",
        "insight": ("{unggul} led the xG battle {xg_u} to {xg_k} from {shot_u} shots, "
                    "while {kalah} managed {shot_k}."),
        "desimal": ".",
        "sm_judul": "{tim} – Shot Map",
        "sm_sub": "Includes all open-play and set piece shots",
        "sm_ringkas": "{gol} goals  ·  {shot} shots  ·  {xg} xG",
        "sm_hasil": "Outcome",
    },
}


# ---------------------------------------------------------------- helpers data
def get_stat(stats_json, key, period="ALL"):
    """Ambil satu item statistik SofaScore berdasarkan 'key' (mis. 'ballPossession')."""
    for p in (stats_json or {}).get("statistics", []):
        if p["period"] != period:
            continue
        for g in p["groups"]:
            for item in g["statisticsItems"]:
                if item.get("key") == key:
                    return item
    return None


def persen_dari_teks(teks):
    """'412/468 (88%)' -> 88"""
    m = re.search(r"(\d+)%", str(teks))
    return int(m.group(1)) if m else None


def nama_pendek(nama):
    """'Lamine Yamal' -> 'Yamal', 'Dion Drena Beljo' -> 'Drena Beljo'."""
    bagian = str(nama).split()
    return " ".join(bagian[1:]) if len(bagian) > 1 else str(nama)


def label_menit(baris):
    """63' atau 90+1'."""
    tambahan = baris.get("addedTime")
    if pd.notna(tambahan) and tambahan:
        return f"{int(baris['time'])}+{int(tambahan)}'"
    return f"{int(baris['time'])}'"


def fmt_angka(nilai, fmt, desimal=","):
    """Format angka dengan pemisah desimal sesuai bahasa (1,82 atau 1.82)."""
    return fmt.format(nilai).replace(".", desimal)


def siapkan_tembakan(df_shots):
    """Tambah kolom xg bersih dan menit numerik (injury time ditambahkan)."""
    df = df_shots.copy()
    df["xg"] = df["xg"].fillna(0)
    tambahan = df["addedTime"].fillna(0).astype(float) if "addedTime" in df else 0
    df["menit"] = df["time"] + tambahan
    return df


def ringkas_tim(d):
    return {
        "gol": int((d["shotType"] == "goal").sum()),
        "xg": d["xg"].sum(),
        "tembakan": len(d),
        "tepat": int(d["shotType"].isin(["goal", "save"]).sum()),
    }


def ukuran_font_nama(nama, dasar=40):
    """Kecilkan font kalau nama tim panjang supaya tidak menabrak skor."""
    return dasar if len(nama) <= 10 else max(24, dasar * 10 / len(nama))


# ---------------------------------------------------------------- helpers gambar
def plot_tembakan(pitch, ax, d, warna, ukuran, bg=BG):
    """Marker berdasarkan hasil: gol (penuh), save (cincin bertitik), block (x), sisanya (pudar)."""
    for tipe in ["miss", "post", "block", "save", "goal"]:
        s = d[d["shotType"] == tipe]
        if s.empty:
            continue
        if tipe == "goal":
            pitch.scatter(s["x"], s["y"], s=ukuran(s["xg"]), color=warna,
                          edgecolors=bg, linewidth=1.2, ax=ax, zorder=5)
        elif tipe == "save":
            pitch.scatter(s["x"], s["y"], s=ukuran(s["xg"]), facecolors="none",
                          edgecolors=warna, linewidth=1.6, ax=ax, zorder=4)
            pitch.scatter(s["x"], s["y"], s=14, color=warna, ax=ax, zorder=4)
        elif tipe == "block":
            pitch.scatter(s["x"], s["y"], s=ukuran(s["xg"]) * 0.45, marker="x",
                          color=warna, linewidth=1.8, ax=ax, zorder=4)
        else:
            pitch.scatter(s["x"], s["y"], s=ukuran(s["xg"]), facecolors="none",
                          edgecolors=warna, linewidth=1.2, alpha=0.55, ax=ax, zorder=3)


def gambar_legend_hasil(ax, T, x_mulai, y, jarak, warna=INK, fs=11):
    """Legend 4 jenis hasil tembakan dalam koordinat sumbu 0-1."""
    item = [
        ("goal", dict(s=150, color=warna)),
        ("save", dict(s=150, facecolors="none", edgecolors=warna, linewidth=1.6)),
        ("block", dict(s=70, marker="x", color=warna, linewidth=1.8)),
        ("miss", dict(s=150, facecolors="none", edgecolors=warna, linewidth=1.2, alpha=0.55)),
    ]
    x = x_mulai
    for kunci, kw in item:
        ax.scatter(x, y, **kw)
        if kunci == "save":
            ax.scatter(x, y, s=8, color=warna)
        ax.text(x + 0.018, y, T[kunci], va="center", fontproperties=_f(False, fs), color=INK)
        x += jarak[kunci]


def isi_gradasi(ax, xs, ys, warna, alpha_atas=0.3):
    """Arsiran gradasi di bawah garis tangga: pekat di bawah garis, memudar ke sumbu."""
    verts = [(xs[0], 0)]
    for i in range(len(xs) - 1):
        verts += [(xs[i], ys[i]), (xs[i + 1], ys[i])]
    verts += [(xs[-1], 0)]
    poly = Polygon(verts, closed=True, facecolor="none", edgecolor="none")
    ax.add_patch(poly)
    r, g, b = to_rgb(warna)
    grad = np.zeros((256, 1, 4))
    grad[:, 0, :3] = (r, g, b)
    grad[:, 0, 3] = np.linspace(0, alpha_atas, 256)
    im = ax.imshow(grad, extent=[xs[0], xs[-1], 0, max(max(ys), 1e-6)],
                   origin="lower", aspect="auto", zorder=1)
    im.set_clip_path(poly)


# ================================================================ 1. MATCH REPORT
def buat_match_report(df_shots, stats_json,
                      home_name, away_name,
                      home_color="#c60b1e", away_color="#2b4c9b",
                      skor_home=None, skor_away=None,
                      subjudul="", insight=None,
                      pembuat=None, sumber="SofaScore",
                      bahasa="id", simpan=None):
    """
    Match report: header skor, insight, shotmap kedua tim dengan panel statistik
    di tengah bawah lapangan, legend, dan grafik xG flow.
    """
    if bahasa not in TEKS:
        raise ValueError(f"bahasa harus salah satu dari {list(TEKS)}")
    T, des = TEKS[bahasa], TEKS[bahasa]["desimal"]

    df = siapkan_tembakan(df_shots)
    home = df[df["isHome"] == True].copy()
    away = df[df["isHome"] == False].copy()
    # home menyerang gawang KIRI, away menyerang gawang KANAN
    home["x"] = home["playerCoordinates.x"] * 1.2
    home["y"] = home["playerCoordinates.y"] * 0.8
    away["x"] = 120 - away["playerCoordinates.x"] * 1.2
    away["y"] = 80 - away["playerCoordinates.y"] * 0.8
    h, a = ringkas_tim(home), ringkas_tim(away)
    skor_home = h["gol"] if skor_home is None else skor_home
    skor_away = a["gol"] if skor_away is None else skor_away

    # ---------- baris statistik ----------
    baris = [
        (T["gol"], skor_home, skor_away, "{:.0f}"),
        (T["xg"], h["xg"], a["xg"], "{:.2f}"),
        (T["tembakan"], h["tembakan"], a["tembakan"], "{:.0f}"),
        (T["tepat"], h["tepat"], a["tepat"], "{:.0f}"),
    ]
    pos = get_stat(stats_json, "ballPossession")
    if pos:
        baris.append((T["possession"], pos["homeValue"], pos["awayValue"], "{:.0f}%"))
    pas = get_stat(stats_json, "accuratePasses")
    if pas:
        hp, ap = persen_dari_teks(pas.get("home")), persen_dari_teks(pas.get("away"))
        if hp is not None and ap is not None:
            baris.append((T["passing"], hp, ap, "{:.0f}%"))

    # ---------- susunan halaman (tinggi tiap blok dalam inci) ----------
    W = 13
    blok = [("header", 1.75), ("insight", 0.55), ("pitch", 8.1), ("legend", 0.55),
            ("flow_title", 0.55), ("flow", 2.9), ("footer", 0.55)]
    H = sum(t for _, t in blok)
    posisi, atas = {}, 0.0
    for nama, tinggi in blok:
        posisi[nama] = (1 - (atas + tinggi) / H, tinggi / H)
        atas += tinggi

    def y_di(blok_nama, frac):
        bawah, tinggi = posisi[blok_nama]
        return bawah + tinggi * frac

    fig = plt.figure(figsize=(W, H))
    fig.set_facecolor(BG)

    # ---------- header: turnamen + skor ----------
    fig.text(0.5, y_di("header", 0.80), subjudul.upper(), ha="center",
             fontproperties=_f(False, 12), color=MUTED)
    yh = y_di("header", 0.33)
    fig.text(0.30, yh, home_name.upper(), ha="right", va="center",
             fontproperties=_f(True, ukuran_font_nama(home_name)), color=home_color)
    fig.text(0.70, yh, away_name.upper(), ha="left", va="center",
             fontproperties=_f(True, ukuran_font_nama(away_name)), color=away_color)
    fig.text(0.5, yh, f"{skor_home} – {skor_away}", ha="center", va="center",
             fontproperties=_f(True, 54), color=INK)

    # ---------- insight ----------
    if insight is None:
        unggul, kalah = (home_name, away_name) if h["xg"] >= a["xg"] else (away_name, home_name)
        su, sk = (h, a) if unggul == home_name else (a, h)
        insight = T["insight"].format(
            unggul=unggul, kalah=kalah,
            xg_u=fmt_angka(su["xg"], "{:.2f}", des), xg_k=fmt_angka(sk["xg"], "{:.2f}", des),
            shot_u=su["tembakan"], shot_k=sk["tembakan"],
        )
    fig.text(0.5, y_di("insight", 0.45), insight, ha="center", va="center",
             fontsize=12.5, color="#444444", style="italic")

    # ---------- lapangan ----------
    bawah, tinggi = posisi["pitch"]
    ax = fig.add_axes([0.04, bawah, 0.92, tinggi])
    pitch = Pitch(pitch_type="statsbomb", pitch_color=BG, line_color=LINE, linewidth=1,
                  goal_type="box", pad_top=0.5, pad_bottom=0.5)
    pitch.draw(ax=ax)

    def ukuran(xg):
        return xg * 1400 + 70

    for d, warna, sisi in [(home, home_color, "kiri"), (away, away_color, "kanan")]:
        plot_tembakan(pitch, ax, d, warna, ukuran)
        # label gol: nama + menit, diarahkan ke tengah lapangan
        for _, r in d[d["shotType"] == "goal"].iterrows():
            dx = 1.6 if sisi == "kiri" else -1.6
            ax.text(r["x"] + dx, r["y"] - 1.7,
                    f"{nama_pendek(r['player.name'])} {label_menit(r)}",
                    fontproperties=_f(True, 10), color=warna, zorder=6,
                    ha="left" if sisi == "kiri" else "right")

    ax.text(2, 78, T["serangan_home"].format(tim=home_name.upper()),
            fontproperties=_f(True, 10), color=MUTED, va="center")
    ax.text(118, 78, T["serangan_away"].format(tim=away_name.upper()),
            fontproperties=_f(True, 10), color=MUTED, va="center", ha="right")

    # ---------- panel statistik: di dalam lapangan, tengah bawah ----------
    x0, lebar, t_bar, jarak = 41, 38, 2.9, 3.9
    y_terbawah = 79 - 2.2 - t_bar / 2 - 1.5
    y_teratas = y_terbawah - (len(baris) - 1) * jarak
    ax.add_patch(FancyBboxPatch((x0 - 1.2, y_teratas - t_bar / 2 - 1.2), lebar + 2.4,
                                (len(baris) - 1) * jarak + t_bar + 2.4,
                                boxstyle="round,pad=0,rounding_size=1",
                                facecolor=BG, edgecolor="none", zorder=5))
    for i, (label, hv, av, fmt) in enumerate(baris):
        y = y_teratas + i * jarak
        total = (hv or 0) + (av or 0)
        porsi = hv / total if total else 0.5
        ax.add_patch(Rectangle((x0, y - t_bar / 2), lebar * porsi, t_bar, color=home_color, zorder=6))
        ax.add_patch(Rectangle((x0 + lebar * porsi, y - t_bar / 2), lebar * (1 - porsi), t_bar,
                               color=away_color, zorder=6))
        kw = dict(va="center", color="white", zorder=7)
        ax.text(x0 + lebar * 0.025, y, fmt_angka(hv, fmt, des), ha="left",
                fontproperties=_f(True, 12), **kw)
        ax.text(x0 + lebar * 0.975, y, fmt_angka(av, fmt, des), ha="right",
                fontproperties=_f(True, 12), **kw)
        ax.text(x0 + lebar / 2, y, label, ha="center", fontproperties=_f(True, 9.5), **kw)

    # ---------- legend ----------
    bawah, tinggi = posisi["legend"]
    lg = fig.add_axes([0.08, bawah, 0.84, tinggi])
    lg.set_xlim(0, 1)
    lg.set_ylim(0, 1)
    lg.axis("off")
    gambar_legend_hasil(lg, T, 0.012, 0.5,
                        {"goal": 0.16, "save": 0.2, "block": 0.16, "miss": 0.16})
    lg.text(0.78, 0.5, "xG", va="center", fontproperties=_f(True, 11), color=INK)
    for i, v in enumerate([0.1, 0.3, 0.6]):
        lg.scatter(0.83 + i * 0.055, 0.5, s=ukuran(v), facecolors="none",
                   edgecolors=MUTED, linewidth=1.1)

    # ---------- xG flow ----------
    fig.text(0.08, y_di("flow_title", 0.3), T["flow_judul"], fontproperties=_f(True, 15), color=INK)
    bawah, tinggi = posisi["flow"]
    axf = fig.add_axes([0.08, bawah + tinggi * 0.1, 0.78, tinggi * 0.9])
    axf.set_facecolor(BG)
    menit_akhir = max(90, df["menit"].max() + 1)
    y_maks = max(h["xg"], a["xg"], 0.1) * 1.12

    for d, warna, nama_tim in [(home, home_color, home_name), (away, away_color, away_name)]:
        d = d.sort_values("menit")
        kum = d["xg"].cumsum()
        xs = [0] + d["menit"].tolist() + [menit_akhir]
        ys = [0] + kum.tolist()
        ys = ys + [ys[-1]]
        isi_gradasi(axf, xs, ys, warna)
        axf.step(xs, ys, where="post", color=warna, linewidth=2.6, zorder=3)
        for idx, r in d[d["shotType"] == "goal"].iterrows():
            yv = kum.loc[idx]
            axf.scatter(r["menit"], yv, s=55, color=warna, edgecolors=BG, linewidth=1.2, zorder=4)
            ke_kiri = r["menit"] >= 15
            axf.annotate(f"{nama_pendek(r['player.name'])} {label_menit(r)}", (r["menit"], yv),
                         xytext=(-5 if ke_kiri else 5, 7), textcoords="offset points",
                         ha="right" if ke_kiri else "left",
                         fontproperties=_f(True, 11), color=warna, zorder=5)
        axf.text(menit_akhir + 0.8, ys[-1], f"{nama_tim}  {fmt_angka(ys[-1], '{:.2f}', des)}",
                 color=warna, va="center", fontproperties=_f(True, 12))

    axf.axvline(45, color=LINE, linestyle=":", linewidth=1, zorder=2)
    axf.set_xlim(0, menit_akhir)
    axf.set_ylim(0, y_maks)
    axf.set_xticks([0, 15, 30, 45, 60, 75, 90])
    axf.set_xticklabels([f"{m}'" for m in [0, 15, 30, 45, 60, 75, 90]])
    axf.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt_angka(v, "{:.2f}", des)))
    axf.grid(axis="y", color=GRID, zorder=0)
    axf.tick_params(colors=MUTED, labelsize=9)
    for s in ["top", "right", "left"]:
        axf.spines[s].set_visible(False)
    axf.spines["bottom"].set_color(LINE)

    # ---------- footer ----------
    fig.text(0.08, y_di("footer", 0.35), f"{T['data']}: {sumber}",
             fontproperties=_f(False, 9.5), color=MUTED)
    if pembuat:
        fig.text(0.92, y_di("footer", 0.35), pembuat.upper(), ha="right",
                 fontproperties=_f(True, 10.5), color=INK)

    if simpan:
        fig.savefig(simpan, dpi=200, facecolor=BG)
    return fig, (ax, axf)


# ================================================================ 2. SHOT MAP PER TIM
def buat_shotmap_per_tim(df_shots, home_name, away_name,
                         home_color="#c60b1e", away_color="#2b4c9b",
                         judul_pertandingan="", bahasa="id",
                         pembuat=None, sumber="SofaScore",
                         warna_bg=BG, simpan=None):
    """
    Dua setengah lapangan vertikal berdampingan (home kiri, away kanan), tema terang.
    Legend hasil tembakan dan skala xG berada di dalam lapangan.
    """
    if bahasa not in TEKS:
        raise ValueError(f"bahasa harus salah satu dari {list(TEKS)}")
    T, des = TEKS[bahasa], TEKS[bahasa]["desimal"]

    df = siapkan_tembakan(df_shots)
    # kedua tim digambar menyerang ke atas
    df["x"] = 120 - df["playerCoordinates.x"] * 1.2
    df["y"] = df["playerCoordinates.y"] * 0.8

    def ukuran(xg):
        return xg * 900 + 40

    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color=warna_bg,
                          line_color=LINE, linewidth=1, goal_type="box", pad_bottom=0.5)
    fig, axs = plt.subplots(1, 2, figsize=(16, 9))
    fig.set_facecolor(warna_bg)

    for ax, is_home, tim, warna in [(axs[0], True, home_name, home_color),
                                    (axs[1], False, away_name, away_color)]:
        pitch.draw(ax=ax)
        d = df[df["isHome"] == is_home]
        plot_tembakan(pitch, ax, d, warna, ukuran, bg=warna_bg)

        # label gol: nama + menit
        for _, r in d[d["shotType"] == "goal"].iterrows():
            pitch.annotate(f"{nama_pendek(r['player.name'])} {label_menit(r)}",
                           xy=(r["x"], r["y"]), xytext=(r["x"] - 2.4, r["y"]), ax=ax,
                           ha="center", va="top", fontproperties=_f(True, 10),
                           color=warna, zorder=6)

        # judul panel
        r = ringkas_tim(d)
        ringkas = T["sm_ringkas"].format(gol=r["gol"], shot=r["tembakan"],
                                         xg=fmt_angka(r["xg"], "{:.2f}", des))
        if bahasa == "en":
            ringkas = ringkas.replace("1 goals", "1 goal").replace(" 1 shots", " 1 shot")
        ax.set_title(T["sm_judul"].format(tim=tim), color=warna, pad=36,
                     fontproperties=_f(True, 24))
        ax.text(0.5, 1.05, T["sm_sub"], transform=ax.transAxes, ha="center",
                fontproperties=_f(False, 10.5), color=MUTED)
        ax.text(0.5, 1.015, ringkas, transform=ax.transAxes, ha="center",
                fontproperties=_f(True, 12), color=INK)

        # legend di dalam lapangan, dekat garis tengah
        lg = ax.inset_axes([0.08, 0.035, 0.84, 0.17])
        lg.set_xlim(0, 1)
        lg.set_ylim(0, 1)
        lg.axis("off")
        for y0 in (0.55, 0.0):
            lg.add_patch(FancyBboxPatch((0, y0 + 0.04), 1, 0.38,
                                        boxstyle="round,pad=0,rounding_size=0.04",
                                        facecolor=PANEL, edgecolor="none"))
        lg.text(0.03, 0.78, T["sm_hasil"], fontproperties=_f(True, 11), color=INK, va="center")
        jarak = ({"goal": 0.13, "save": 0.27, "block": 0.15, "miss": 0.0} if bahasa == "id"
                 else {"goal": 0.15, "save": 0.17, "block": 0.2, "miss": 0.0})
        gambar_legend_hasil(lg, T, 0.2, 0.78, jarak, warna=warna, fs=10)
        lg.text(0.03, 0.23, "xG", fontproperties=_f(True, 11), color=INK, va="center")
        for i, v in enumerate([0.25, 0.5, 0.75, 1.0]):
            xc = 0.25 + i * 0.19
            lg.scatter(xc, 0.23, s=ukuran(v), facecolors="none", edgecolors=MUTED, linewidth=1)
            label = "1" if v == 1 else "{:.2f}".format(v).rstrip("0")
            if bahasa == "en":
                label = label.lstrip("0")          # gaya Inggris: .25 .5 .75
            lg.text(xc + 0.06, 0.23, label.replace(".", des), fontproperties=_f(False, 10),
                    color=INK, va="center")

    # footer
    if judul_pertandingan:
        fig.text(0.5, 0.03, judul_pertandingan, ha="center", fontproperties=_f(False, 11), color=MUTED)
    kredit = f"{T['data']}: {sumber}" + (f"  ·  {T['viz']}: {pembuat}" if pembuat else "")
    fig.text(0.98, 0.03, kredit, ha="right", fontproperties=_f(False, 9.5), color=MUTED)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.85, bottom=0.07, wspace=0.06)

    if simpan:
        fig.savefig(simpan, dpi=200, facecolor=warna_bg, bbox_inches="tight", pad_inches=0.4)
    return fig, axs


# ================================================================ wrapper dari folder data
def _muat_pertandingan(raw_folder):
    from pathlib import Path
    from src.process import info_pertandingan, muat_raw

    raw_folder = Path(raw_folder)
    data = muat_raw(raw_folder)
    info = info_pertandingan(data["event"])
    df = pd.json_normalize(data["shotmap"]["shotmap"])
    stats = data["statistics"] or {"statistics": []}
    return raw_folder, info, df, stats


def _folder_figur(figures_dir):
    from pathlib import Path
    folder = Path(figures_dir or Path(__file__).resolve().parents[1] / "reports" / "figures")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def report_dari_raw(raw_folder, figures_dir=None, **kwargs):
    """
    Match report langsung dari folder data/raw/<pertandingan>/.
    Nama tim, skor, turnamen, dan tanggal diambil otomatis dari event.json.
    Parameter tambahan (bahasa, warna, insight, pembuat, dll.) diteruskan ke buat_match_report.
    """
    raw_folder, info, df, stats = _muat_pertandingan(raw_folder)
    simpan = _folder_figur(figures_dir) / f"{raw_folder.name}.png"
    kwargs.setdefault("subjudul", "  ·  ".join(x for x in [info.get("tournament"), info.get("date")] if x))
    kwargs.setdefault("skor_home", info.get("home_score"))
    kwargs.setdefault("skor_away", info.get("away_score"))
    fig, axes = buat_match_report(df, stats, info.get("home", "Home"), info.get("away", "Away"),
                                  simpan=simpan, **kwargs)
    print(f"Report tersimpan di: {simpan}")
    return fig, axes


def shotmap_per_tim_dari_raw(raw_folder, figures_dir=None, **kwargs):
    """Shot map per tim langsung dari folder data/raw/<pertandingan>/."""
    raw_folder, info, df, _ = _muat_pertandingan(raw_folder)
    simpan = _folder_figur(figures_dir) / f"{raw_folder.name}_shotmap.png"
    if info.get("home_score") is not None:
        bagian = [f"{info['home']} {info['home_score']}-{info['away_score']} {info['away']}",
                  info.get("tournament"), info.get("date")]
        kwargs.setdefault("judul_pertandingan", "  ·  ".join(x for x in bagian if x))
    fig, axs = buat_shotmap_per_tim(df, info.get("home", "Home"), info.get("away", "Away"),
                                    simpan=simpan, **kwargs)
    print(f"Shot map tersimpan di: {simpan}")
    return fig, axs
