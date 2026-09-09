from services.pvpoke_service import overall_ranks
from services.iv_engine import calculate_rank, best_ivs


def overall_rank(pokemon: str) -> str:
    try:
        results = overall_ranks(pokemon)
    except Exception as exc:
        return (
            f"⚠️ I couldn't refresh PvPoke data right now: `{type(exc).__name__}`. "
            "Rotom will not invent a rank."
        )

    lines = [f"⚡ **{pokemon} — PvPoke overall ranking**"]
    found = False
    for result in results:
        if result["rank"] is None:
            lines.append(f"• **{result['league']}** — not found")
        else:
            found = True
            score = result["score"]
            score_text = f" · score {score:.1f}" if isinstance(score, (int, float)) else ""
            lines.append(f"• **{result['league']}** — #{result['rank']}{score_text}")
    if found:
        lines.append("\n_Data source: PvPoke. Rankings can change when its data/simulations are updated._")
    return "\n".join(lines)


def best_iv_spread(
    pokemon: str,
    *,
    form: str | None = None,
    shadow: bool = False,
    purified: bool = False,
    best_buddy: bool = False,
) -> str:
    try:
        results = [
            best_ivs(
                pokemon,
                key,
                form=form,
                shadow=shadow,
                purified=purified,
                best_buddy=best_buddy,
            )
            for key in ("great", "ultra", "master")
        ]
    except Exception as exc:
        return f"⚠️ I couldn't calculate that IV spread: `{exc}`"

    label = results[0]["pokemon"]
    variant = results[0].get("variant")
    heading = f"⚡ **{label} — best stat-product IV spreads**"
    if variant:
        heading += f" ({variant})"
    lines = [heading]
    for r in results:
        lines.append(
            f"• **{r['league']}** — **{r['ivs'][0]}/{r['ivs'][1]}/{r['ivs'][2]}** "
            f"at Lv {r['level']:g}, CP {r['cp']}"
        )
    lines.append(
        "\n_Rotom uses deterministic stat-product math. Shadow bonuses affect battle stats, "
        "not CP; Best Buddy permits level 51. PvPoke battle rankings are separate._"
    )
    return "\n".join(lines)


def rank_for_ivs(
    pokemon: str,
    attack: int,
    defense: int,
    stamina: int,
    *,
    form: str | None = None,
    shadow: bool = False,
    purified: bool = False,
    best_buddy: bool = False,
) -> str:
    lines = [f"⚡ **{pokemon} — IV rank {attack}/{defense}/{stamina}**"]
    try:
        for result in (
            calculate_rank(
                pokemon,
                attack,
                defense,
                stamina,
                key,
                form=form,
                shadow=shadow,
                purified=purified,
                best_buddy=best_buddy,
            )
            for key in ("great", "ultra", "master")
        ):
            lines.append(
                f"• **{result['league']}** — **#{result['rank']}/{result['total']}** "
                f"({result['percentile']:.1f}th percentile) · Lv {result['level']:g} · CP {result['cp']}"
            )
        variant = next(
            calculate_rank(
                pokemon, attack, defense, stamina, "great", form=form,
                shadow=shadow, purified=purified, best_buddy=best_buddy
            )["variant"]
            for _ in [0]
        )
        if variant:
            lines.insert(1, f"Variant: **{variant}**")
        lines.append(
            "\n_Rank is based on deterministic stat product under the league CP cap. "
            "Shadow battle multipliers are included; Best Buddy allows level 51._"
        )
    except Exception as exc:
        return f"⚠️ I couldn't calculate that IV rank: `{exc}`"
    return "\n".join(lines)


def rank_for_ivs_league(
    pokemon: str,
    attack: int,
    defense: int,
    stamina: int,
    league: str,
    *,
    form: str | None = None,
    shadow: bool = False,
    purified: bool = False,
    best_buddy: bool = False,
) -> str:
    try:
        r = calculate_rank(
            pokemon, attack, defense, stamina, league,
            form=form, shadow=shadow, purified=purified, best_buddy=best_buddy,
        )
        return (
            f"⚡ **{r['pokemon']} — {r['league']}**\n"
            f"IVs **{attack}/{defense}/{stamina}** → **#{r['rank']}/{r['total']}** "
            f"({r['percentile']:.1f}th percentile)\n"
            f"Level **{r['level']:g}** · CP **{r['cp']}** · "
            f"Stats **{r['attack']:.1f}/{r['defense']:.1f}/{r['stamina']}**"
        )
    except Exception as exc:
        return f"⚠️ I couldn't calculate that IV rank: `{exc}`"
