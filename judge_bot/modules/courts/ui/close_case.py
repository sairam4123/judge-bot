import discord
import typing as t
from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.core.repositories import RepositoryManager
from judge_bot.utils import construct_header_message, trim_message

class CloseCaseModal(discord.ui.Modal, title="Request Case Closure"):
    def __init__(self, *, view: discord.ui.View | None = None) -> None:
        super().__init__()
        self.view = view

    reason = discord.ui.TextInput(
        label="Reason for Closing the Case",
        style=discord.TextStyle.paragraph,
        placeholder="Provide a brief reason for closing the case",
        required=True,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(interaction.client, JudgeBot)
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.response.send_message("This modal can only be submitted in a server.", ephemeral=True)
            return
        
        if not interaction.channel or not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("This modal can only be submitted in a case thread.", ephemeral=True)
            return

        repo = RepositoryManager(interaction.client)
        case =repo.cases.has_case(interaction.channel.id)
        if not case:
            await interaction.response.send_message("No case found for this thread.", ephemeral=True)
            return
        
        repo.cases.close_case(interaction.channel.id, self.reason.value)
        case = repo.cases.get_case(interaction.channel.id)
        if not case:
            await interaction.followup.send("Case not found after closure.", ephemeral=True)
            return
        if not case.og_message_id:
            await interaction.followup.send("Original case message ID not found.", ephemeral=True)
            return

        header_message = await construct_header_message(interaction.client, case)

        og_msg = await interaction.channel.fetch_message(case.og_message_id)
        if not og_msg:
            await interaction.followup.send("Original case message not found.", ephemeral=True)
            return
        
        await og_msg.edit(content=trim_message(header_message), view=self.view)

        await interaction.channel.edit(archived=True, locked=True)
        await interaction.followup.send("The case has been closed. Court is adjourned!", ephemeral=True)
