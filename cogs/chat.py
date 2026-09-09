import discord
from discord.ext import commands
from config import config
from services.openai_service import chat

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.bot.user not in message.mentions:
            return
        if config.chat_channel_id and message.channel.id != config.chat_channel_id:
            return

        text = message.content.replace(self.bot.user.mention, "").strip()
        if not text:
            await message.reply("Beep boop! Ask me something and I'll help. ⚡")
            return

        try:
            async with message.channel.typing():
                answer = await chat(text)
            await message.reply(answer[:1900], mention_author=False)
        except Exception:
            await message.reply("Rotom hit a tiny electrical hiccup. Try again. ⚡")

async def setup(bot):
    await bot.add_cog(ChatCog(bot))
