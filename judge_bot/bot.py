from discord.ext.commands import Bot
from judge_bot.db import Database

class JudgeBot(Bot):
    def __init__(self, command_prefix, intents):
        self.db = Database(db_path="db/judge_bot.db")
        super().__init__(command_prefix=command_prefix, intents=intents)

    async def on_ready(self):
        assert self.user is not None
        await self.load_extension("judge_bot.modules.courts.commands")
        print(f'Logged in as {self.user.name} - {self.user.id}')
        cmds = await self.tree.sync()  # Sync application commands
        print(f'Application commands synced. {len(cmds)} commands synced.')
        
    
    
