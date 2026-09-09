"""Deterministic Pokémon GO PvP IV/stat-product ranking engine.

The AI is intentionally not involved in the math. Base stats are loaded from
PvPoke's Game Master data, while the CP multiplier table is kept local.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.pvpoke_service import _fetch_json

GM_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/gamemaster.min.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "pvpoke"
DATA_DIR.mkdir(parents=True, exist_ok=True)
GM_CACHE = DATA_DIR / "gamemaster.min.json"

# Official-style CPM values used by Pokémon GO's CP formula. Half levels are
# included because PvP IV ranks depend on the exact half-level at the CP cap.
CPM = {
    1: .094, 1.5: .135137432, 2: .16639787, 2.5: .192650919,
    3: .21573247, 3.5: .236572661, 4: .25572005, 4.5: .273530381,
    5: .29024988, 5.5: .306057377, 6: .3210876, 6.5: .335445036,
    7: .34921268, 7.5: .362457751, 8: .37523559, 8.5: .387592406,
    9: .39956728, 9.5: .411193551, 10: .42250001, 10.5: .432926419,
    11: .44310755, 11.5: .453059958, 12: .46279839, 12.5: .472336083,
    13: .48168495, 13.5: .4908558, 14: .49985844, 14.5: .508701765,
    15: .51739395, 15.5: .525942511, 16: .53435433, 16.5: .542635767,
    17: .55079269, 17.5: .558830576, 18: .56675452, 18.5: .574569153,
    19: .58227891, 19.5: .589887917, 20: .59740001, 20.5: .604818814,
    21: .61215729, 21.5: .619399365, 22: .62656713, 22.5: .633644533,
    23: .64065295, 23.5: .647576426, 24: .65443563, 24.5: .661214806,
    25: .667934, 25.5: .674577537, 26: .68116492, 26.5: .687680648,
    27: .69414365, 27.5: .700538673, 28: .70688421, 28.5: .713164996,
    29: .71939909, 29.5: .725571552, 30: .7317, 30.5: .734741009,
    31: .73776948, 31.5: .740785574, 32: .74378943, 32.5: .746781211,
    33: .74976104, 33.5: .752729087, 34: .75568551, 34.5: .758630378,
    35: .76156384, 35.5: .764486065, 36: .76739717, 36.5: .770297266,
    37: .7731865, 37.5: .776064962, 38: .77893275, 38.5: .781790055,
    39: .78463697, 39.5: .787473578, 40: .79030001, 40.5: .792803968,
    41: .79530001, 41.5: .797800015, 42: .8003, 42.5: .802799995,
    43: .8053, 43.5: .8078, 44: .81029999, 44.5: .812799985,
    45: .81529999, 45.5: .81779999, 46: .82029999, 46.5: .82279999,
    47: .82529999, 47.5: .82779999, 48: .83029999, 48.5: .83279999,
    49: .83529999, 49.5: .83779999, 50: .84029999, 50.5: .84279999,
    51: .84529999,
}

LEAGUES = {
    "great": ("Great League", 1500, 50.0),
    "ultra": ("Ultra League", 2500, 50.0),
    "master": ("Master League", 10000, 50.0),
}

@dataclass(frozen=True)
class PokemonStats:
    species_id: str
    species_name: str
    atk: int
    defense: int
    hp: int
    shadow: bool = False
    form: str | None = None


def _normalize(value: str) -> str:
    value = value.lower().replace("♀", "").replace("♂", "")
    value = value.replace("’", "'")
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


def _load_gamemaster() -> dict[str, Any]:
    if not GM_CACHE.exists():
        data = _fetch_json(GM_URL)
        GM_CACHE.write_text(json.dumps(data), encoding="utf-8")
    else:
        data = json.loads(GM_CACHE.read_text(encoding="utf-8"))
    return data


def _pokemon_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("pokemon", "pokemonSpecies", "pokemonSpeciesSettings"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def find_species(query: str, *, form: str | None = None, shadow: bool = False) -> PokemonStats:
    """Resolve a species/form deterministically from PvPoke Game Master data.

    Shadow is a battle-state modifier, not a separate CP-stat species. The
    resolver therefore prefers a normal Game Master entry and records the
    requested shadow state separately.
    """
    data = _load_gamemaster()
    q = _normalize(query)
    form_q = _normalize(form or "")
    entries = _pokemon_entries(data)
    exact: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []

    for entry in entries:
        sid = str(entry.get("speciesId") or entry.get("pokemonId") or entry.get("id") or "")
        name = str(entry.get("speciesName") or entry.get("name") or sid)
        n_sid = _normalize(sid)
        n_name = _normalize(name)
        combined = f"{n_sid}_{n_name}"
        if form_q and form_q not in combined and form_q.replace("_", "") not in combined.replace("_", ""):
            continue
        # Do not let a shadow entry win unless explicitly requested.
        is_shadow_entry = "shadow" in n_sid or "shadow" in n_name
        if is_shadow_entry:
            continue
        if n_sid == q or n_name == q or _normalize(n_sid.split("_")[0]) == q:
            exact.append(entry)
        elif q in n_sid or q in n_name:
            partial.append(entry)

    matches = exact or partial
    if not matches:
        # A second pass permits a query such as "marowak" + form "alolan"
        # where the GM name carries the form but the base species ID differs.
        for entry in entries:
            sid = str(entry.get("speciesId") or entry.get("pokemonId") or entry.get("id") or "")
            name = str(entry.get("speciesName") or entry.get("name") or sid)
            n_sid = _normalize(sid)
            n_name = _normalize(name)
            if "shadow" in n_sid or "shadow" in n_name:
                continue
            combined = f"{n_sid}_{n_name}"
            if q in combined and (not form_q or form_q in combined):
                matches.append(entry)

    if not matches:
        raise ValueError(f"Pokémon/form not found: {query}{f' ({form})' if form else ''}")

    # Prefer an exact form match and the shortest species id to avoid choosing
    # a related evolution when a broad partial search is supplied.
    chosen = sorted(matches, key=lambda e: (0 if _normalize(str(e.get("speciesId", ""))) == q else 1,
                                             len(str(e.get("speciesId", "")))))[0]
    base = chosen.get("baseStats") or {}
    try:
        return PokemonStats(
            species_id=str(chosen.get("speciesId") or chosen.get("id")),
            species_name=str(chosen.get("speciesName") or chosen.get("name") or query),
            atk=int(base["atk"]),
            defense=int(base["def"] if "def" in base else base["defense"]),
            hp=int(base["hp"]),
            shadow=shadow,
            form=form,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Game Master data for {query} is incomplete") from exc


def _battle_stats(stats: PokemonStats, ivs: tuple[int, int, int], level: float) -> tuple[float, float, int]:
    cpm = CPM[level]
    attack, defense, stamina = ivs
    atk = (stats.atk + attack) * cpm
    deff = (stats.defense + defense) * cpm
    hp = int((stats.hp + stamina) * cpm)
    if stats.shadow:
        atk *= 1.2
        deff *= 0.83333331
    return atk, deff, hp


def cp_for(stats: PokemonStats, ivs: tuple[int, int, int], level: float) -> int:
    """Pokémon GO CP; Shadow bonus does not alter CP, only battle stats."""
    cpm = CPM[level]
    attack, defense, stamina = ivs
    a = stats.atk + attack
    d = stats.defense + defense
    h = stats.hp + stamina
    return max(10, int((a * math.sqrt(d) * math.sqrt(h) * cpm * cpm) / 10))


def effective_stats(stats: PokemonStats, ivs: tuple[int, int, int], level: float) -> tuple[float, float, int]:
    return _battle_stats(stats, ivs, level)


def _best_level(stats: PokemonStats, ivs: tuple[int, int, int], cap: int, max_level: float) -> float | None:
    eligible = [level for level in CPM if level <= max_level and cp_for(stats, ivs, level) <= cap]
    return max(eligible) if eligible else None


def _variant_label(stats: PokemonStats, best_buddy: bool, purified: bool) -> str:
    bits = []
    if stats.form:
        bits.append(stats.form.title())
    if stats.shadow:
        bits.append("Shadow")
    elif purified:
        bits.append("Purified")
    if best_buddy:
        bits.append("Best Buddy")
    return " · ".join(bits)


def _rows(pokemon: str, league: str, *, form: str | None = None, shadow: bool = False,
          purified: bool = False, best_buddy: bool = False) -> tuple[PokemonStats, str, int, list[tuple]]:
    if league not in LEAGUES:
        raise ValueError(f"Unknown league: {league}")
    title, cap, default_max = LEAGUES[league]
    max_level = 51.0 if best_buddy else 50.0
    stats = find_species(pokemon, form=form, shadow=shadow)
    rows: list[tuple[float, tuple[int, int, int], float, int, float, float, int]] = []
    for a in range(16):
        for d in range(16):
            for h in range(16):
                ivs = (a, d, h)
                level = _best_level(stats, ivs, cap, max_level)
                if level is None:
                    continue
                ea, ed, eh = effective_stats(stats, ivs, level)
                product = ea * ed * eh
                rows.append((product, ivs, level, cp_for(stats, ivs, level), ea, ed, eh))
    rows.sort(key=lambda row: (-row[0], row[1]))
    return stats, title, cap, rows


def calculate_rank(
    pokemon: str,
    attack: int,
    defense: int,
    stamina: int,
    league: str = "great",
    *,
    form: str | None = None,
    shadow: bool = False,
    purified: bool = False,
    best_buddy: bool = False,
) -> dict[str, Any]:
    if any(not isinstance(iv, int) or iv < 0 or iv > 15 for iv in (attack, defense, stamina)):
        raise ValueError("IVs must be whole numbers from 0 to 15")
    stats, title, cap, rows = _rows(
        pokemon, league, form=form, shadow=shadow, purified=purified, best_buddy=best_buddy
    )
    target = (attack, defense, stamina)
    target_row = next((r for r in rows if r[1] == target), None)
    if target_row is None:
        raise ValueError("Requested IV spread cannot fit the selected league")
    target_product = target_row[0]
    rank = 1 + sum(1 for r in rows if r[0] > target_product)
    percentile = (len(rows) - rank) / max(1, len(rows) - 1) * 100
    best = rows[0]
    return {
        "pokemon": stats.species_name,
        "species_id": stats.species_id,
        "form": form,
        "shadow": shadow,
        "purified": purified,
        "best_buddy": best_buddy,
        "variant": _variant_label(stats, best_buddy, purified),
        "league": title,
        "cp_cap": cap,
        "ivs": target,
        "rank": rank,
        "total": len(rows),
        "percentile": percentile,
        "level": target_row[2],
        "cp": target_row[3],
        "attack": target_row[4],
        "defense": target_row[5],
        "stamina": target_row[6],
        "best_ivs": best[1],
        "best_level": best[2],
        "best_cp": best[3],
        "best_product": best[0],
        "product": target_product,
    }


def best_ivs(pokemon: str, league: str = "great", *, form: str | None = None,
             shadow: bool = False, purified: bool = False, best_buddy: bool = False) -> dict[str, Any]:
    stats, title, cap, rows = _rows(
        pokemon, league, form=form, shadow=shadow, purified=purified, best_buddy=best_buddy
    )
    best = rows[0]
    return {
        "pokemon": stats.species_name,
        "species_id": stats.species_id,
        "form": form,
        "shadow": shadow,
        "purified": purified,
        "best_buddy": best_buddy,
        "variant": _variant_label(stats, best_buddy, purified),
        "league": title,
        "cp_cap": cap,
        "rank": 1,
        "total": len(rows),
        "ivs": best[1],
        "level": best[2],
        "cp": best[3],
        "attack": best[4],
        "defense": best[5],
        "stamina": best[6],
    }
