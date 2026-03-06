import dotenv

import os
import discord

from judge_bot.bot import JudgeBot


dotenv.load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if token is None:
    raise ValueError("DISCORD_TOKEN environment variable not set")

dbot = JudgeBot(command_prefix="!", intents=discord.Intents.all())

dbot.run(token)
