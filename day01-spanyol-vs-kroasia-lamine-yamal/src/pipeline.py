"""
Pipeline end-to-end: scrape -> proses -> visualisasi.

Pemakaian (dari folder utama project):
    python -m src.pipeline "https://www.sofascore.com/football/match/croatia-spain/YTbspUb#id:15534081,tab:statistics"
"""
import argparse

import matplotlib
matplotlib.use("Agg")  # simpan gambar tanpa membuka jendela

from src.scraper import scrape_match
from src.process import proses
from src.visualize import report_dari_raw, shotmap_per_tim_dari_raw


def main():
    parser = argparse.ArgumentParser(description="SofaScore match report")
    parser.add_argument("url", help="URL pertandingan SofaScore (harus mengandung #id:...)")
    parser.add_argument("--home-color", default="#c60b1e")
    parser.add_argument("--away-color", default="#2b4c9b")
    parser.add_argument("--bahasa", default="id", choices=["id", "en"])
    parser.add_argument("--pembuat", default=None, help="nama Anda untuk kredit visualisasi")
    args = parser.parse_args()

    raw_folder = scrape_match(args.url)
    proses(raw_folder)
    opsi = dict(home_color=args.home_color, away_color=args.away_color,
                bahasa=args.bahasa, pembuat=args.pembuat)
    report_dari_raw(raw_folder, **opsi)
    shotmap_per_tim_dari_raw(raw_folder, **opsi)


if __name__ == "__main__":
    main()
