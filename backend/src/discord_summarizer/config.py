import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_API_BASE = "https://discord.com/api/v10"
OPENAI_API_BASE = "https://api.openai.com/v1/chat/completions"
