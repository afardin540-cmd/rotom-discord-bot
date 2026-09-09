import logging
import discord
from discord.ext import commands
from config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

class Rotom(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.chat")
        await self.load_extension("cogs.commands")
        await self.load_extension("cogs.utilities")
        await self.tree.sync()

bot = Rotom(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    logging.info("Rotom online as %s", bot.user)

if __name__ == "__main__":
    if not config.discord_token:
        raise RuntimeError("DISCORD_TOKEN is missing")
    bot.run(config.discord_token)
