import math
from discord.ext import commands
from config import config

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="haversine")
    async def haversine(self, ctx, *args):
        if config.command_channel_id and ctx.channel.id != config.command_channel_id:
            return
        if len(args) != 4:
            await ctx.reply("Usage: `!haversine <lat1> <lon1> <lat2> <lon2>`")
            return
        try:
            lat1, lon1, lat2, lon2 = map(float, args)
        except ValueError:
            await ctx.reply("All four coordinates must be valid numbers.")
            return
        if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
            await ctx.reply("Latitude must be between -90 and 90.")
            return
        if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
            await ctx.reply("Longitude must be between -180 and 180.")
            return

        R = 6_371_000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
        distance = 2 * R * math.asin(math.sqrt(a))
        await ctx.reply(f"📍 Distance: **{distance:.2f} m**")

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
