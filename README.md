# Belajar Data Olahraga

Kode, analisis, dan visual untuk seri thread **#BelajarDataOlahraga**: satu topik per hari, dibedah pakai data. Topiknya mencakup sepak bola, basket, dan lari, dikerjakan dengan Python (scraping, pengolahan data, visualisasi) dan Tableau Public (dashboard interaktif).

## Daftar seri

| Day | Topik | Olahraga | Tools | Output |
|---|---|---|---|---|
| [01](day01-spanyol-vs-kroasia-lamine-yamal) | Spanyol 4-1 Kroasia & sorotan Lamine Yamal | ⚽ Sepak bola | Python, SofaScore scraping, mplsoccer | Match report + shot map |
| [02](day02-jalen-brunson-shot-efficiency) | Jalen Brunson, juara NBA: peta tembakan & efisiensi | 🏀 Basket | Tableau Public | Dashboard interaktif |
| [03](day03-half-marathon-saya) | Membedah data half marathon saya | 🏃 Lari | Tableau Public | Dashboard interaktif |
| [04](day04-perburuan-gelar) | Persib vs Borneo FC: sama-sama 79 poin | ⚽ Sepak bola | Python, matplotlib | 3 kartu + notebook analisis musim |
| [05](day05-xg-borneo-vs-persib) | Siapa yang sebenarnya main lebih bagus? (xG) | ⚽ Sepak bola | Python, matplotlib | 4 kartu |
| [06](day06-egy-maulana-vikri) | Egy Maulana Vikri: supersub klub & timnas | ⚽ Sepak bola | Python, mplsoccer | Poster + 3 kartu, shot map |

## Yang dipraktikkan di seri ini

- **Pengumpulan data:** scraping API SofaScore lewat browser otomatis (Day 1), data aktivitas lari pribadi (Day 3)
- **Pengolahan data:** JSON bertingkat → tabel rapi (pandas), konversi koordinat lapangan
- **Metrik olahraga:** expected goals (xG), shot efficiency, pace & split lari
- **Visualisasi:** shot map, xG flow, kartu konten media sosial, dashboard interaktif
- **Storytelling:** setiap analisis dikemas jadi thread yang bisa dibaca awam

## Struktur repo

```
belajar-data-olahraga/
├── common.py              # gaya kartu bersama (warna, ukuran, header/footer) untuk Day 4–5
├── requirements.txt       # dependensi Day 4–6
├── data/                  # CSV Day 4–6 (tidak diunggah, lihat data/README.md)
├── fonts/                 # Anton & Inter (lisensi OFL)
├── day01-spanyol-vs-kroasia-lamine-yamal/   # proyek mandiri: pipeline scraping → report
├── day02-jalen-brunson-shot-efficiency/     # Tableau: screenshot + link dashboard
├── day03-half-marathon-saya/                # Tableau: screenshot + link dashboard
├── day04-perburuan-gelar/
├── day05-xg-borneo-vs-persib/
└── day06-egy-maulana-vikri/
```

## Cara menjalankan

**Day 1** punya pipeline dan `requirements.txt` sendiri (butuh Google Chrome untuk scraping):

```bash
cd day01-spanyol-vs-kroasia-lamine-yamal
pip install -r requirements.txt
python -m src.pipeline "<url pertandingan SofaScore>" --bahasa id --pembuat "Risna Nurmala"
```

**Day 4–6** dijalankan dari root repo:

```bash
pip install -r requirements.txt
# taruh file CSV di data/ (lihat data/README.md)
python day04-perburuan-gelar/make_cards.py
python day05-xg-borneo-vs-persib/make_cards.py
python day06-egy-maulana-vikri/make_cards.py
python day06-egy-maulana-vikri/make_poster.py
```

Hasil gambar tersimpan di folder `output/` masing-masing hari. Untuk tampilan yang sama persis, instal font **Inter** di sistem (tersedia di folder `fonts/`); kalau tidak ada, kartu memakai DejaVu Sans.

**Day 2–3** dibuat di Tableau Public; buka link dashboard di README masing-masing.

## Sumber & kredit

- **Data sepak bola:** SofaScore, di-scrape dan dirapikan oleh [@ulik.data.bola](https://www.threads.net/@ulik.data.bola).
- **Data basket (Day 2):** _[isi sumber data]_
- **Data lari (Day 3):** data aktivitas pribadi.
- **Berita (Day 6):** iNews, VIVA, detik.
- **Foto (Day 6):** JawaPos.com; KOMPAS.com/Adil Nursalam (tidak disertakan di repo).
- **Font:** Anton & Inter, SIL Open Font License (lihat `fonts/`).

Semua data digunakan untuk tujuan belajar dan portofolio pribadi.
