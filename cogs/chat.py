from collections import defaultdict, deque

import discord
from discord.ext import commands

from config import config
from services.openai_service import chat


class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Short-term memory:
        # Keep the last 10 user/Rotom exchanges per channel.
        self.memory = defaultdict(lambda: deque(maxlen=20))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bot.user not in message.mentions:
            return

        if (
            config.chat_channel_id is not None
            and message.channel.id != config.chat_channel_id
        ):
            return

        text = message.content.replace(self.bot.user.mention, "").strip()

        if not text:
            await message.reply(
                "Bzzzt! Ask me something and I'll be happy to help! ⚡"
            )
            return

        channel_id = message.channel.id

        # Copy recent conversation context before adding the new message.
        history = list(self.memory[channel_id])

        try:
            async with message.channel.typing():
                answer = await chat(text, history=history)

            # Save the conversation only after a successful AI response.
            self.memory[channel_id].append(
                {"role": "user", "content": text}
            )
            self.memory[channel_id].append(
                {"role": "assistant", "content": answer}
            )

            await message.reply(
                answer[:1900],
                mention_author=False,
            )

        except Exception:
            await message.reply(
                "Rotom hit a tiny electrical hiccup. Try again. ⚡"
            )


async def setup(bot):
    await bot.add_cog(ChatCog(bot))
