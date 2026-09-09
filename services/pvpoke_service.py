import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings"
CACHE = Path(__file__).resolve().parent.parent / "data" / "pvpoke"
CACHE.mkdir(parents=True, exist_ok=True)

LEAGUES = {
    "great": ("Great League", 1500),
    "ultra": ("Ultra League", 2500),
    "master": ("Master League", 10000),
}

def _fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "Rotom-Discord-Bot/0.4"})
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def load_overall(league_key: str):
    title, cp = LEAGUES[league_key]
    path = CACHE / f"overall-{cp}.json"

    # Refresh if the cache is absent. A later scheduler can refresh it daily.
    if not path.exists():
        url = f"{BASE}/all/overall/rankings-{cp}.json"
        data = _fetch_json(url)
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        data = json.loads(path.read_text(encoding="utf-8"))

    return title, cp, data

def refresh_all():
    for key in LEAGUES:
        title, cp = LEAGUES[key]
        data = _fetch_json(f"{BASE}/all/overall/rankings-{cp}.json")
        (CACHE / f"overall-{cp}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

def normalize(name: str) -> str:
    return (
        name.lower()
        .replace("♀", "")
        .replace("♂", "")
        .replace("’", "'")
        .replace(" ", "_")
        .replace("-", "_")
    )

def find_pokemon(entries, query: str):
    q = normalize(query)
    exact = []
    partial = []

    for entry in entries:
        raw = str(entry.get("speciesId") or entry.get("pokemon") or "")
        base = raw.split(" ")[0].split("+")[0].split("/")[0]
        if normalize(base) == q:
            exact.append(entry)
        elif q in normalize(base):
            partial.append(entry)

    return exact or partial

def overall_ranks(pokemon: str):
    results = []
    for key in LEAGUES:
        title, cp, data = load_overall(key)
        entries = data if isinstance(data, list) else data.get("rankings", data.get("pokemon", []))
        matches = find_pokemon(entries, pokemon)

        if not matches:
            results.append({
                "league": title,
                "rank": None,
                "score": None,
            })
            continue

        # PvPoke's ranking JSON generally has an explicit rank field.
        item = matches[0]
        rank = item.get("rank")
        score = item.get("score")

        results.append({
            "league": title,
            "rank": rank,
            "score": score,
        })

    return results
