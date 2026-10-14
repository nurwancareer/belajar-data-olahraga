"""
Mengubah JSON mentah SofaScore menjadi tabel rapi (CSV) di data/processed/.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

KOLOM_SHOTS = [
    "time", "addedTime", "player.name", "player.shortName", "player.position",
    "isHome", "team", "shotType", "situation", "bodyPart", "goalMouthLocation",
    "xg", "xgot", "playerCoordinates.x", "playerCoordinates.y",
]


def muat_raw(folder):
    folder = Path(folder)
    data = {}
    for nama in ["event", "shotmap", "statistics"]:
        f = folder / f"{nama}.json"
        data[nama] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    return data


def info_pertandingan(event_json):
    """Ringkasan pertandingan: nama tim, skor, turnamen, tanggal."""
    if not event_json:
        return {}
    ev = event_json["event"]
    ts = ev.get("startTimestamp")
    return {
        "event_id": ev.get("id"),
        "home": ev["homeTeam"]["name"],
        "away": ev["awayTeam"]["name"],
        "home_score": ev.get("homeScore", {}).get("current"),
        "away_score": ev.get("awayScore", {}).get("current"),
        "tournament": ev.get("tournament", {}).get("name"),
        "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d") if ts else None,
    }


def shots_df(shotmap_json, info=None):
    df = pd.json_normalize(shotmap_json["shotmap"])
    if info:
        df["team"] = df["isHome"].map({True: info["home"], False: info["away"]})
    kolom = [k for k in KOLOM_SHOTS if k in df.columns]
    return df[kolom].sort_values("time").reset_index(drop=True)


def stats_df(stats_json, info=None):
    rows = []
    for periode in (stats_json or {}).get("statistics", []):
        for grup in periode["groups"]:
            for item in grup["statisticsItems"]:
                rows.append({
                    "period": periode["period"],
                    "group": grup["groupName"],
                    "key": item.get("key"),
                    "stat": item.get("name"),
                    "home": item.get("home"),
                    "away": item.get("away"),
                    "home_value": item.get("homeValue"),
                    "away_value": item.get("awayValue"),
                })
    df = pd.DataFrame(rows)
    if info and not df.empty:
        df = df.rename(columns={"home": info["home"], "away": info["away"]})
    return df


def proses(raw_folder):
    """Proses satu folder data/raw/<pertandingan>/ -> data/processed/<pertandingan>/."""
    raw_folder = Path(raw_folder)
    data = muat_raw(raw_folder)
    info = info_pertandingan(data["event"])

    out = PROCESSED_DIR / raw_folder.name
    out.mkdir(parents=True, exist_ok=True)

    shots = shots_df(data["shotmap"], info)
    shots.to_csv(out / "shots.csv", index=False)

    stats = stats_df(data["statistics"], info)
    if not stats.empty:
        stats.to_csv(out / "stats.csv", index=False)

    (out / "match_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False))
    print(f"Data rapi tersimpan di: {out}")
    return out
