// Tempel di Console Chrome (DevTools) saat membuka tab www.sofascore.com.
// Mengambil shotmap 20 laga Egy Maulana Vikri (2025/26) dan mengunduh egy_shotmap_2526.csv
(async () => {
  const PLAYER_ID = 941547;
  const ids = [14214529,14214672,14214683,14214721,14214737,14214766,14214788,14214810,14721723,14214840,
               14214860,14214876,14214911,14214949,14214960,14214999,14215070,14215096,14215120,14215142];
  const cols = ["match_id","minute","added_time","x","y","xg","xgot","result","situation","body_part","is_home","goal_mouth_location"];
  const rows = [cols.join(",")], fails = [];
  for (const id of ids) {
    const r = await fetch(`/api/v1/event/${id}/shotmap`);
    if (!r.ok) { fails.push(`${id} (${r.status})`); continue; }
    const j = await r.json();
    for (const s of j.shotmap || []) {
      if (s.player?.id !== PLAYER_ID) continue;
      rows.push([id, s.time, s.addedTime ?? "", s.playerCoordinates?.x, s.playerCoordinates?.y,
                 s.xg ?? "", s.xgot ?? "", s.shotType, s.situation, s.bodyPart, s.isHome,
                 s.goalMouthLocation ?? ""].join(","));
    }
    console.log(`laga ${id}: ok`);
    await new Promise(res => setTimeout(res, 1000));
  }
  console.log(`Selesai: ${rows.length - 1} tembakan (target 36). Gagal: ${fails.length ? fails.join(", ") : "tidak ada"}`);
  if (rows.length > 1) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([rows.join("\n")], {type: "text/csv"}));
    a.download = "egy_shotmap_2526.csv";
    a.click();
  }
})();
