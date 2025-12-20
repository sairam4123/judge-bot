import discord
from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.ui.attach_evidence import AttachEvidenceModal
from judge_bot.modules.courts.ui.close_case import CloseCaseModal
from judge_bot.modules.courts.ui.update_case import UpdateCaseModal
from judge_bot.modules.courts.core.repositories import RepositoryManager

class CaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Case", style=discord.ButtonStyle.danger, custom_id="close_case_button")
    async def close_case(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert isinstance(interaction.client, JudgeBot)
        repo = RepositoryManager(interaction.client)
        if not interaction.channel or not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("This command can only be used in a case thread.", ephemeral=True)
            return
        case = repo.cases.has_case(interaction.channel.id)
        if not case:
            await interaction.response.send_message("No case found for this thread.", ephemeral=True)
            return

        await interaction.response.send_modal(CloseCaseModal(view=self))
    
    @discord.ui.button(label="Update Case", style=discord.ButtonStyle.primary, custom_id="update_case_button")
    async def update_case(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert isinstance(interaction.client, JudgeBot)
        if not interaction.channel or not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("This command can only be used in a case thread.", ephemeral=True)
            return
        repo = RepositoryManager(interaction.client)
        case = repo.cases.has_case(interaction.channel.id)
        if not case:
            await interaction.response.send_message("No case found for this thread.", ephemeral=True)
            return
        
        await interaction.response.send_modal(UpdateCaseModal(case_id=interaction.channel.id, bot=interaction.client, view=self))
    
    @discord.ui.button(label="Attach Evidence", style=discord.ButtonStyle.secondary, custom_id="attach_evidence_button")
    async def attach_evidence(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert isinstance(interaction.client, JudgeBot)
        if not interaction.channel or not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("This command can only be used in a case thread.", ephemeral=True)
            return

        repo = RepositoryManager(interaction.client)
        case = repo.cases.has_case(interaction.channel.id)
        if not case:
            await interaction.response.send_message("No case found for this thread.", ephemeral=True)
            return
        
        await interaction.response.send_modal(AttachEvidenceModal(view=self))
