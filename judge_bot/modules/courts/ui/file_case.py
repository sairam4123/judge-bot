import discord
import typing as t
from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.core.models import Case
from judge_bot.modules.courts.core.repositories import RepositoryManager
from judge_bot.modules.courts.ui.case_view import CaseView
from judge_bot.utils import trim_message, construct_header_message
from datetime import datetime

class FileCaseModal(discord.ui.Modal, title="File a Case"):

    case_type = discord.ui.Label(
        text="Case Type",
        component=discord.ui.Select(
            placeholder="Select Case Type",
            min_values=1,
            required=True,
            max_values=1,
            options=[
                discord.SelectOption(label="Civil", description="Dispute over rights, property, or compensation", emoji="⚖️"),
                discord.SelectOption(label="Criminal", description="Alleged violation of rules or misconduct", emoji="🚨"),
                discord.SelectOption(label="Community", description="Personal relationships or community matters", emoji="👥"),
                discord.SelectOption(label="Counter-case", description="Retaliatory case by the accused", emoji="🔄"),
                discord.SelectOption(label="Other", description="Does not fit standard categories", emoji="❓"),
            ],
        )
    )

    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Provide details for your accusation",
        required=True,
        max_length=1000,
    )

    accused = discord.ui.Label(
        text="Accused User(s)",
        component=discord.ui.UserSelect(placeholder="Select the accused users", min_values=1, max_values=4, required=True)
    )

    associated_cases = discord.ui.Label(
        text="Associated Case ID (if applicable)",
        component=discord.ui.ChannelSelect(
            placeholder="Select associated case thread(s)",
            channel_types=[discord.ChannelType.public_thread],
            required=False,
            max_values=4,
            min_values=0,
        )
    )


    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(interaction.client, JudgeBot)

        if not interaction.guild:
            await interaction.response.send_message("This modal can only be submitted in a server.", ephemeral=True)
            return
        
        if not interaction.channel_id:
            await interaction.response.send_message("This modal can only be submitted in a server channel.", ephemeral=True)
            return

        repo = RepositoryManager(interaction.client)

        court = repo.courts.get_court(interaction.channel_id)
        if not court:
            await interaction.response.send_message(f"The courtroom channel is not set up. Please create it to proceed with the case. You may also use the /start command to create a new courtroom.", ephemeral=True)
            return
        court_channel = interaction.guild.get_channel(court.channel_id)
        if not court_channel:
            await interaction.response.send_message(f"The courtroom channel does not exist. Please create it to proceed with the case.", ephemeral=True)
            return
        
        assert isinstance(court_channel, discord.TextChannel)
        assert isinstance(court_channel.guild, discord.Guild)
        assert isinstance(self.case_type.component, discord.ui.Select)
        assert isinstance(self.accused.component, discord.ui.UserSelect)
        assert isinstance(self.associated_cases.component, discord.ui.ChannelSelect)

        case_type = self.case_type.component.values[0]

        if case_type == "Counter-case":
            counter_case_select = t.cast(discord.ui.ChannelSelect, self.associated_cases.component)
            if not counter_case_select.values:
                await interaction.response.send_message("You must select a case thread for a counter-case.", ephemeral=True)
                return
            counter_case_thread = counter_case_select.values[0]
            if not repo.cases.has_case(counter_case_thread.id):
                await interaction.response.send_message("The selected case thread does not correspond to an active case.", ephemeral=True)
                return
            
            accused_user_ids = repo.cases.get_accused(counter_case_thread.id)
            if interaction.user.id not in accused_user_ids:
                await interaction.response.send_message("You can only file a counter-case against a case you are accused in.", ephemeral=True)
                return

        accused = ', '.join(user.mention for user in self.accused.component.values)
        accused_names = ', '.join(user.name for user in self.accused.component.values)
        await interaction.response.send_message(f"{interaction.user.mention}, Your case has been filed against {accused} for the charges: {self.reason.value}, Case Type: {case_type}", ephemeral=True)
        
        thread = await court_channel.create_thread(name=f"Case: {interaction.user.name} vs {accused_names}", type=discord.ChannelType.public_thread, invitable=False)
        accuser_id=interaction.user.id
        accused_ids=[user.id for user in self.accused.component.values]

        if thread:
            
            case = Case(
                case_id=thread.id,
                court_id=court.court_id,
                reason=self.reason.value,
                type=case_type,
                status="open",
                og_message_id=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            repo.cases.create_case(case)
            repo.participants.add_accuser_participant(case.case_id, accuser_id)
            repo.participants.add_accused_participants(case.case_id, accused_ids)

            header_message = await construct_header_message(interaction.client, case)
            
            og_msg = await thread.send(f"{trim_message(header_message)}", view=CaseView())
            
            repo.cases.update_og_message_id(thread.id, og_msg.id)


            repo.associated_cases.link_associated_cases(
                case_id=thread.id,
                associated_case_ids=[ch.id for ch in self.associated_cases.component.values]
            )


class FileCaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="File a Case", style=discord.ButtonStyle.primary, custom_id="file_case_button")
    async def file_case(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FileCaseModal())
        # await interaction.response.send_message("To file a case, please state your accusation in the format: 'I sue @user for [reason]'", ephemeral=True)
