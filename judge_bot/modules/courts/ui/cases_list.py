import discord


class ViewCasesList(discord.ui.View):
    def __init__(self, cases):
        super().__init__()
        self.cases = cases
