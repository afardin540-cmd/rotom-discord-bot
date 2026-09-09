import json
import re
import discord
from discord import app_commands
from discord.ext import commands
from config import config
from services.pvp_engine import best_iv_spread, overall_rank, rank_for_ivs
from services.sync_service import next_expected_sync
from services.iv_engine import calculate_rank
from services.openai_service import parse_rankcheck_image

RULES = [
    "Be respectful to other members.",
    "No harassment, hate speech, or targeted abuse.",
    "No spam or disruptive behavior.",
    "Do not share private/personal information.",
    "Discussion or promotion of Pokémon GO / Wayfarer TOS violations is not allowed.",
    "Follow Discord's Terms and server staff directions.",
]

def allowed(ctx):
    return not config.command_channel_id or ctx.channel.id == config.command_channel_id


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("vision response was not an object")
    return obj


def _rankcheck_result(
    data: dict,
    *,
    best_buddy: bool = False,
    form_override: str | None = None,
    shadow_override: bool | None = None,
    purified_override: bool | None = None,
) -> str:
    pokemon = data.get("pokemon")
    a, d, s = data.get("attack_iv"), data.get("defense_iv"), data.get("stamina_iv")
    if not pokemon or not all(isinstance(x, int) and 0 <= x <= 15 for x in (a, d, s)):
        return (
            "⚠️ I could not confidently read all three appraisal IVs. "
            "Please send a clearer appraisal screenshot showing the Pokémon name and all three bars."
        )

    form = form_override or data.get("form")
    shadow = data.get("shadow") is True if shadow_override is None else shadow_override
    purified = data.get("purified") is True if purified_override is None else purified_override
    if shadow and purified:
        return "⚠️ A Pokémon cannot be both Shadow and Purified. Choose one variant."

    lines = [f"⚡ **Rankcheck: {pokemon} — {a}/{d}/{s}**"]
    variant_bits = []
    if form:
        variant_bits.append(str(form).title())
    if shadow:
        variant_bits.append("Shadow")
    elif purified:
        variant_bits.append("Purified")
    if best_buddy:
        variant_bits.append("Best Buddy")
    if variant_bits:
        lines.append("Variant: **" + " · ".join(variant_bits) + "**")
    if data.get("cp") is not None:
        lines.append(f"CP: **{data['cp']}**")
    if data.get("weather_boosted") is True:
        lines.append("Weather boosted: **yes**")

    for league in ("great", "ultra", "master"):
        try:
            r = calculate_rank(
                pokemon, a, d, s, league,
                form=form,
                shadow=shadow,
                purified=purified,
                best_buddy=best_buddy,
            )
            lines.append(
                f"• **{r['league']}** — **#{r['rank']}/{r['total']}** "
                f"({r['percentile']:.1f}th percentile), Lv {r['level']:g}, CP {r['cp']}"
            )
        except Exception as exc:
            lines.append(f"• **{league.title()} League** — unavailable (`{type(exc).__name__}`)")
    lines.append(
        "\n_Rankcheck uses deterministic stat-product math. Shadow bonuses affect battle stats, "
        "not CP. Best Buddy permits level 51. It never guesses unreadable IVs._"
    )
    return "\n".join(lines)


class CommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rules", description="Show Rotom server rules.")
    async def rules(self, interaction):
        embed = discord.Embed(title=config.rules_title, description="\n".join(f"• {r}" for r in RULES))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="Show expected game/map sync times.")
    async def sync(self, interaction):
        embed = discord.Embed(title="⚡ Rotom Sync Status")
        for service, value in next_expected_sync().items():
            embed.add_field(name=service, value=value, inline=False)
        embed.set_footer(text="Expected times only; syncs can be delayed.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rankcheck", description="Read a Pokémon GO appraisal screenshot and calculate PvP IV ranks.")
    @app_commands.describe(
        screenshot="Pokémon GO appraisal screenshot",
        form="Optional form, e.g. alolan, galarian, hisuian, origin",
        shadow="Treat this as a Shadow Pokémon",
        purified="Treat this as a Purified Pokémon",
        best_buddy="Allow the Best Buddy level 51 cap",
    )
    async def rankcheck(
        self,
        interaction: discord.Interaction,
        screenshot: discord.Attachment,
        form: str | None = None,
        shadow: bool | None = None,
        purified: bool | None = None,
        best_buddy: bool = False,
    ):
        if not screenshot.content_type or not screenshot.content_type.startswith("image/"):
            await interaction.response.send_message("⚠️ Please attach an image screenshot.", ephemeral=True)
            return
        if shadow is True and purified is True:
            await interaction.response.send_message("⚠️ A Pokémon cannot be both Shadow and Purified.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        try:
            raw = await parse_rankcheck_image(screenshot.url)
            data = _parse_json_object(raw)
            await interaction.followup.send(
                _rankcheck_result(
                    data,
                    best_buddy=best_buddy,
                    form_override=form,
                    shadow_override=shadow,
                    purified_override=purified,
                )[:1900]
            )
        except Exception as exc:
            await interaction.followup.send(
                f"⚠️ Rankcheck hit an error: `{type(exc).__name__}`. "
                "Try a clearer screenshot and make sure the OpenAI vision/API settings are configured."
            )

    @commands.command(name="rankcheck")
    async def rankcheck_prefix(self, ctx, *args):
        if not allowed(ctx):
            return
        if not ctx.message.attachments:
            await ctx.reply("Attach a Pokémon GO appraisal screenshot to `!rankcheck`.")
            return
        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith("image/"):
            await ctx.reply("Please attach an image screenshot.")
            return

        flags = {str(a).lower().strip() for a in args}
        best_buddy = bool(flags & {"bestbuddy", "best_buddy", "bb"})
        shadow = bool("shadow" in flags)
        purified = bool("purified" in flags or "pure" in flags)
        if shadow and purified:
            await ctx.reply("⚠️ A Pokémon cannot be both Shadow and Purified.")
            return
        known_flags = {"bestbuddy", "best_buddy", "bb", "shadow", "purified", "pure"}
        form_tokens = [x for x in args if str(x).lower() not in known_flags]
        form = " ".join(form_tokens).strip() or None

        async with ctx.typing():
            try:
                raw = await parse_rankcheck_image(attachment.url)
                data = _parse_json_object(raw)
                await ctx.reply(
                    _rankcheck_result(
                        data,
                        best_buddy=best_buddy,
                        form_override=form,
                        shadow_override=shadow if shadow else None,
                        purified_override=purified if purified else None,
                    )[:1900],
                    mention_author=False,
                )
            except Exception as exc:
                await ctx.reply(f"⚠️ Rankcheck failed: `{type(exc).__name__}`")

    @commands.command(name="pvpiv")
    async def pvpiv(self, ctx, pokemon: str, *args):
        if not allowed(ctx):
            return

        # Optional flags after the IVs: form words, shadow, purified, bestbuddy.
        flags = {str(a).lower().strip() for a in args}
        shadow = "shadow" in flags
        purified = bool(flags & {"purified", "pure"})
        best_buddy = bool(flags & {"bestbuddy", "best_buddy", "bb"})
        known_flags = {"shadow", "purified", "pure", "bestbuddy", "best_buddy", "bb"}
        numeric = [x for x in args if str(x).lower() not in known_flags]

        # If the first three non-flag args are integers, this is an exact-IV query.
        # Otherwise treat all non-flag args as the optional form and return best spreads.
        is_exact = len(numeric) >= 3
        if is_exact:
            try:
                ivs = tuple(map(int, numeric[:3]))
            except ValueError:
                is_exact = False

        if not is_exact:
            form = " ".join(numeric).strip() or None
            await ctx.reply(
                best_iv_spread(
                    pokemon,
                    form=form,
                    shadow=shadow,
                    purified=purified,
                    best_buddy=best_buddy,
                )
            )
            return
        if any(iv < 0 or iv > 15 for iv in ivs):
            await ctx.reply("IVs must be between 0 and 15.")
            return
        form = " ".join(numeric[3:]).strip() or None
        if shadow and purified:
            await ctx.reply("⚠️ A Pokémon cannot be both Shadow and Purified.")
            return
        await ctx.reply(
            rank_for_ivs(
                pokemon, *ivs,
                form=form,
                shadow=shadow,
                purified=purified,
                best_buddy=best_buddy,
            )
        )

    @commands.command(name="rank")
    async def rank(self, ctx, *, pokemon):
        if not allowed(ctx):
            return
        await ctx.reply(overall_rank(pokemon))

    @commands.command(name="help_rotom")
    async def help_rotom(self, ctx):
        if not allowed(ctx):
            return
        embed = discord.Embed(title="⚡ Rotom Commands")
        embed.description = (
            "`/rules` — server rules\n"
            "`/sync` — expected sync\n"
            "`/rankcheck <screenshot>` — read appraisal + calculate PvP IV ranks\n"
            "`!rankcheck` + image — same workflow\n"
            "`!pvpiv <pokemon>` — best-IV spread\n"
            "`!pvpiv <pokemon> <A> <D> <S> [form] [shadow|purified] [bestbuddy]` — exact IV rank\n"
            "`!rank <pokemon>` — PvPoke ranking\n"
            "`!haversine <lat1> <lon1> <lat2> <lon2>` — distance\n"
            "`@Rotom <question>` — normal chat"
        )
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandCog(bot))
