"""Poster pembuka #Day6 (menggantikan kartu 1): gaya poster Brunson, 1080x1350.
Butuh di photos/: egy_dewa.png (foto JawaPos.com), egy_timnas.png (foto KOMPAS.com/Adil Nursalam).
Font Anton & Inter ada di folder fonts/ (lisensi OFL).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
NAVY, NAVY2 = (18, 24, 56), (30, 38, 82)
WHITE, MUTED = (245, 242, 232), (170, 174, 200)
ACC = (242, 140, 56)          # oranye Egy versi terang (kontras di latar gelap)
GREYDOT = (78, 86, 128)

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"
PHOTOS = HERE / "photos"
anton = lambda s: ImageFont.truetype(str(FONTS / "Anton-Regular.ttf"), s)


def inter(weight, size):
    f = ImageFont.truetype(str(FONTS / "Inter.ttf"), size)
    f.set_variation_by_name(weight)          # Regular / Medium / Bold
    return f

img = Image.new("RGB", (W, H), NAVY)
d = ImageDraw.Draw(img)

# ---------- foto utama (JawaPos.com) dengan gradasi ke navy ----------
ph = Image.open(PHOTOS / "egy_dewa.png").convert("RGB")
ph = ph.crop((0, 0, 900, 675)).resize((W, int(675 * W / 900)))          # fokus ke Egy (kiri)
PH_H = ph.height                                                          # 810
img.paste(ph, (0, 0))
grad = Image.new("L", (1, PH_H))
for y in range(PH_H):
    t = max(0, (y - PH_H * .35) / (PH_H * .62))                          # mulai pudar di 45% tinggi foto
    grad.putpixel((0, y), int(255 * min(1, t ** 1.1)))
img.paste(Image.new("RGB", (W, PH_H), NAVY), (0, 0), grad.resize((W, PH_H)))
top = Image.new("L", (1, 140))
for y in range(140):
    top.putpixel((0, y), int(150 * (1 - y / 140)))
img.paste(Image.new("RGB", (W, 140), NAVY), (0, 0), top.resize((W, 140)))

# ---------- badge & hashtag ----------
badge = "SUPER LEAGUE  ·  #DAY6"
bf = inter("Bold", 22)
bw = d.textlength(badge, font=bf)
d.rounded_rectangle((48, 44, 48 + bw + 36, 92), radius=24, fill=NAVY)
d.text((66, 68), badge, font=bf, fill=WHITE, anchor="lm")
d.text((W - 48, 68), "#SuperLeague #Timnas #DewaUnited", font=inter("Medium", 20), fill=WHITE, anchor="rm")

# ---------- judul ----------
d.text((W / 2, 560), "AKHIRNYA", font=anton(92), fill=ACC, anchor="ms")
d.text((W / 2, 720), "GOL LAGI", font=anton(178), fill=WHITE, anchor="ms")
d.text((W / 2, 772), "EGY MAULANA VIKRI  ·  DEWA UNITED", font=inter("Bold", 26), fill=ACC, anchor="ms")
d.text((W / 2, 812), "Gol ke gawang Persib, 11 Oktober 2026", font=inter("Regular", 24), fill=MUTED, anchor="ms")

# ---------- panel bawah ----------
PY = 860
d.rounded_rectangle((48, PY, W - 48, 1240), radius=22, fill=NAVY2)
# kiri: 29 laga
d.text((84, PY + 30), "29", font=anton(135), fill=ACC, anchor="la")
d.text((290, PY + 70), "laga liga", font=inter("Bold", 30), fill=WHITE, anchor="la")
d.text((290, PY + 108), "berturut-turut", font=inter("Bold", 30), fill=WHITE, anchor="la")
d.text((290, PY + 146), "tanpa gol", font=inter("Bold", 30), fill=WHITE, anchor="la")
r, gap, x0, y0 = 13, 37, 98, PY + 240
for i in range(30):
    row, col = divmod(i, 10)
    cx, cy = x0 + col * gap, y0 + row * gap
    if i < 29:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=GREYDOT, width=3)
    else:
        d.ellipse((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), fill=ACC)
d.text((x0 + 9 * gap + 24, y0 + 2 * gap), "GOL", font=inter("Bold", 18), fill=ACC, anchor="lm")
d.text((84, PY + 340), "Gol klub terakhir sebelumnya: April 2025", font=inter("Regular", 19), fill=MUTED, anchor="la")

# kanan: foto Timnas (KOMPAS.com/Adil Nursalam)
t = Image.open(PHOTOS / "egy_timnas.png").convert("RGB").crop((390, 140, 830, 700))   # fokus ke Egy (no. 7)
TW, TH = 380, 225
t = t.resize((TW, int(t.height * TW / t.width)))
t = t.crop((0, 0, TW, TH))
mask = Image.new("L", (TW, TH), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, TW, TH), radius=16, fill=255)
TX, TY = W - 48 - 36 - TW, PY + 36
img.paste(t, (TX, TY), mask)
d.text((TX, TY + TH + 22), "Supersub Timnas di ASEAN Cup 2026:", font=inter("Bold", 19), fill=WHITE, anchor="la")
d.text((TX, TY + TH + 50), "pre-assist vs Bangladesh, ikut", font=inter("Regular", 18), fill=MUTED, anchor="la")
d.text((TX, TY + TH + 74), "terlibat gol penyama di final.", font=inter("Regular", 18), fill=MUTED, anchor="la")

# ---------- footer ----------
d.line((48, 1266, W - 48, 1266), fill=ACC, width=3)
d.text((48, 1290), "Foto: JawaPos.com; KOMPAS.com/Adil Nursalam", font=inter("Regular", 17), fill=MUTED, anchor="la")
d.text((48, 1316), "Data: SofaScore via @ulik.data.bola  ·  Berita: iNews, VIVA, detik  ·  Viz: Belajar Baca Data",
       font=inter("Regular", 17), fill=MUTED, anchor="la")

(HERE / "output").mkdir(exist_ok=True)
img.save(HERE / "output/day6_1_poster.png")
print("saved", HERE / "output/day6_1_poster.png")
