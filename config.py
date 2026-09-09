import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    chat_channel_id: int | None = int(os.getenv("CHAT_CHANNEL_ID")) if os.getenv("CHAT_CHANNEL_ID") else None
    command_channel_id: int | None = int(os.getenv("COMMAND_CHANNEL_ID")) if os.getenv("COMMAND_CHANNEL_ID") else None
    rules_title: str = os.getenv("RULES_TITLE", "Rotom Server Rules")

config = Config()
