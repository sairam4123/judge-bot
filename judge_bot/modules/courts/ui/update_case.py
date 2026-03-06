import discord
from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.core.repositories import RepositoryManager
from judge_bot.utils import construct_header_message, trim_message


class UpdateCaseModal(discord.ui.Modal, title="Update Case Details"):
    def __init__(
        self, case_id: int, bot: JudgeBot, view: discord.ui.View | None = None
    ) -> None:
        super().__init__()
        self.case_id = case_id
        self.view = view

        assert isinstance(self.case_type.component, discord.ui.Select)
        assert isinstance(self.accused.component, discord.ui.UserSelect)

        repo = RepositoryManager(bot)
        case = repo.cases.get_case(case_id)
        if not case:
            return

        self.case_type.component.options = [
            discord.SelectOption(
                label=original_option.label,
                description=original_option.description,
                emoji=original_option.emoji,
                default=(original_option.label == case.type),
            )
            for original_option in self.case_type.component.options
        ]

        accused_user_ids = repo.cases.get_accused(case_id)

        self.reason.default = case.reason
        self.accused.component.default_values = [
            discord.Object(id=user_id) for user_id in accused_user_ids
        ]

    case_type = discord.ui.Label(
        text="Case Type",
        component=discord.ui.Select(
            placeholder="Select Case Type",
            min_values=1,
            required=True,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Civil",
                    description="Dispute over rights, property, or compensation",
                    emoji="⚖️",
                ),
                discord.SelectOption(
                    label="Criminal",
                    description="Alleged violation of rules or misconduct",
                    emoji="🚨",
                ),
                discord.SelectOption(
                    label="Community",
                    description="Personal relationships or community matters",
                    emoji="👥",
                ),
                discord.SelectOption(
                    label="Counter-case",
                    description="Retaliatory case by the accused",
                    emoji="🔄",
                ),
                discord.SelectOption(
                    label="Other",
                    description="Does not fit standard categories",
                    emoji="❓",
                ),
            ],
        ),
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
        component=discord.ui.UserSelect(
            placeholder="Select the accused users",
            min_values=1,
            max_values=4,
            required=True,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(interaction.client, JudgeBot)
        assert isinstance(self.case_type.component, discord.ui.Select)
        assert isinstance(self.accused.component, discord.ui.UserSelect)

        await interaction.response.defer(ephemeral=True, thinking=True)
        repo = RepositoryManager(interaction.client)

        case = repo.cases.get_case(self.case_id)
        if not case:
            await interaction.followup.send(
                "No case found with the provided ID.", ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.followup.send(
                "This modal can only be submitted in a server.", ephemeral=True
            )
            return

        if not interaction.channel or not isinstance(
            interaction.channel, discord.Thread
        ):
            await interaction.followup.send(
                "This modal can only be submitted in a case thread.", ephemeral=True
            )
            return

        if not case.og_message_id:
            await interaction.followup.send(
                "Original case message ID not found.", ephemeral=True
            )
            return

        case_type = self.case_type.component.values[0]
        accused_user_ids = [user.id for user in self.accused.component.values]
        repo.cases.update_case(
            self.case_id,
            case_type=case_type,
            reason=self.reason.value,
            accused=accused_user_ids,
        )

        header_message = await construct_header_message(interaction.client, case)
        og_msg = await interaction.channel.fetch_message(case.og_message_id)
        if not og_msg:
            await interaction.followup.send(
                "Original case message not found.", ephemeral=True
            )
            return
        await og_msg.edit(content=trim_message(header_message), view=self.view)

        await interaction.followup.send(
            "The case details have been updated.", ephemeral=True
        )
