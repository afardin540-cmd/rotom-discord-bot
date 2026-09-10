import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Legacy OpenAI setting — kept so the rest of the project remains compatible
        # Local AI / OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "local-token")
    openai_model: str = os.getenv("OPENAI_MODEL", "qwen2.5-1.5b-instruct")
    ai_server_url: str = os.getenv("AI_SERVER_URL", "https://injection-qualities-paying-engage.trycloudflare.com")


    chat_channel_id: int | None = (
        int(os.getenv("CHAT_CHANNEL_ID"))
        if os.getenv("CHAT_CHANNEL_ID")
        else None
    )

    command_channel_id: int | None = (
        int(os.getenv("COMMAND_CHANNEL_ID"))
        if os.getenv("COMMAND_CHANNEL_ID")
        else None
    )

    rules_title: str = os.getenv("RULES_TITLE", "Rotom Server Rules")


config = Config()
