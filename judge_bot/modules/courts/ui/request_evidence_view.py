
import discord
from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.ui.attach_evidence import AttachEvidenceModal
from judge_bot.modules.courts.core.repositories import RepositoryManager

class RequestEvidenceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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
