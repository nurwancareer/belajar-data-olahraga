"""
Scraper data pertandingan SofaScore (shotmap, statistik, info pertandingan).

Cara kerja: membuka halaman pertandingan dengan undetected_chromedriver,
lalu membaca respons API dari log jaringan Chrome (performance log).
"""
import json
import re
import subprocess
import time
from pathlib import Path

import undetected_chromedriver as uc

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


# ---------------------------------------------------------------- browser
def versi_chrome(chrome_path=CHROME_PATH):
    """Versi utama Chrome yang terinstal (mis. 153), agar driver selalu cocok."""
    out = subprocess.run([chrome_path, "--version"], capture_output=True, text=True).stdout
    return int(re.search(r"(\d+)\.", out).group(1))


def buka_browser(chrome_path=CHROME_PATH):
    options = uc.ChromeOptions()
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = uc.Chrome(
        options=options,
        version_main=versi_chrome(chrome_path),
        browser_executable_path=chrome_path,
    )
    driver.maximize_window()
    return driver


# ---------------------------------------------------------------- helpers
def event_id_dari_url(url):
    """'.../croatia-spain/YTbspUb#id:15534081,tab:statistics' -> 15534081"""
    m = re.search(r"id:(\d+)", url)
    if not m:
        raise ValueError("Event ID tidak ditemukan di URL (cari bagian '#id:...').")
    return int(m.group(1))


def ambil_logs(driver):
    """Ambil log jaringan. Catatan: log dikosongkan setiap kali dipanggil."""
    return [json.loads(e["message"])["message"] for e in driver.get_log("performance")]


def ambil_api(driver, logs, akhiran, event_id):
    """
    Cari request API yang path-nya berakhiran `akhiran` untuk event tertentu,
    lalu kembalikan isi JSON-nya. Kalau isi respons sudah dibuang Chrome,
    minta ulang lewat fetch() dari dalam browser.
    """
    pola = re.compile(rf"/event/{event_id}(/|$)")
    kandidat = []
    for x in logs:
        headers = x["params"].get("headers", {})
        path = headers.get(":path", "")
        p = path.split("?")[0]
        if p.endswith(akhiran) and pola.search(p):
            host = headers.get(":authority", "www.sofascore.com")
            kandidat.append((x["params"]["requestId"], host, path))

    for rid, host, path in reversed(kandidat):  # paling baru dulu
        try:
            body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": rid})
            print(f"  ✓ {path}")
            return json.loads(body["body"])
        except Exception:
            continue

    if kandidat:
        _, host, path = kandidat[-1]
        print(f"  ↻ ambil ulang via fetch: {path}")
        return driver.execute_script(f"return fetch('https://{host}{path}').then(r => r.json());")

    print(f"  ✗ '{akhiran}' tidak ditemukan di log")
    return None


# ---------------------------------------------------------------- main
def scrape_match(url, driver=None, tunggu=8, interaktif=True):
    """
    Scrape satu pertandingan dan simpan JSON mentahnya ke data/raw/<slug>_<id>/.
    Mengembalikan path folder hasil.
    """
    event_id = event_id_dari_url(url)
    tutup_sendiri = driver is None
    driver = driver or buka_browser()

    try:
        driver.get(url)
        time.sleep(tunggu)
        if interaktif:
            input("Kalau muncul verifikasi, klik manual di browser. "
                  "Setelah tab Statistics & shotmap tampil, tekan Enter...")

        logs = ambil_logs(driver)
        print("Mengambil data:")
        data = {
            "event": ambil_api(driver, logs, f"/event/{event_id}", event_id),
            "shotmap": ambil_api(driver, logs, "/shotmap", event_id),
            "statistics": ambil_api(driver, logs, "/statistics", event_id),
        }
    finally:
        if tutup_sendiri:
            driver.quit()

    return simpan_raw(data, event_id)


def simpan_raw(data, event_id):
    slug = f"event_{event_id}"
    ev = (data.get("event") or {}).get("event")
    if ev:
        slug = f"{ev['homeTeam']['slug']}-vs-{ev['awayTeam']['slug']}_{event_id}"

    folder = RAW_DIR / slug
    folder.mkdir(parents=True, exist_ok=True)
    for nama, isi in data.items():
        if isi is not None:
            with open(folder / f"{nama}.json", "w", encoding="utf-8") as f:
                json.dump(isi, f, ensure_ascii=False, indent=2)
    print(f"Data mentah tersimpan di: {folder}")
    return folder
