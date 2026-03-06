from discord import app_commands
import discord
from discord.ext import commands
from typing import TYPE_CHECKING

from judge_bot.genai.generate import generate_content
from judge_bot.modules.courts.core.models import Court, LogEntry
from judge_bot.modules.courts.core.prompt import BOT_PROMPT, CASE_PROMPT
from judge_bot.modules.courts.core.repositories import RepositoryManager
from judge_bot.modules.courts.ui.request_evidence_view import RequestEvidenceView
from judge_bot.utils import (
    construct_header_message,
    get_evidence_summaries,
    google_summarize_conversation,
    trim_message,
)

if TYPE_CHECKING:
    from judge_bot.bot import JudgeBot

from judge_bot.modules.courts.tools import (
    tools,
)

from exts.cogs import cog_context_menu, CommandsCog
from .ui import CaseView, FileCaseView, AttachEvidenceModal


class JudgeCog(CommandsCog):
    """Cog for judge-related commands."""

    def __init__(self, bot: JudgeBot):
        super().__init__(bot)
        self.bot = bot
        self.repo = RepositoryManager(bot)

    @app_commands.command(name="start", description="Start JudgeBot in this server")
    async def start(
        self,
        interaction: discord.Interaction,
        name: str = "Default Court",
        description: str = "Default court for this server",
    ):
        assert interaction.channel_id is not None, "Channel ID should not be None"
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        if self.repo.courts.contains_court(
            interaction.guild_id, interaction.channel_id
        ):
            await interaction.response.send_message(
                "JudgeBot is already active in this server.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "JudgeBot is now active in this server! All courtroom proceedings will be handled here.",
            ephemeral=True,
        )
        channel = interaction.channel
        if channel is not None and isinstance(channel, discord.TextChannel):
            await channel.send(
                "Order! Order in this court! JudgeBot is now presiding over this courtroom. Let the proceedings begin!",
                view=FileCaseView(),
            )
            self.repo.courts.create_court(
                Court(
                    court_id=interaction.channel_id,
                    name=name,
                    description=description,
                    guild_id=interaction.guild_id,
                    channel_id=interaction.channel_id,
                    created_at=interaction.created_at,
                )
            )

    @app_commands.command(name="stop", description="Stop JudgeBot in this server")
    async def stop(self, interaction: discord.Interaction):
        assert interaction.channel_id is not None, "Channel ID should not be None"
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        if not self.repo.courts.contains_court(
            interaction.guild_id, interaction.channel_id
        ):
            await interaction.response.send_message(
                "JudgeBot is not active in this server.", ephemeral=True
            )
            return
        self.repo.courts.delete_court(interaction.channel_id)
        await interaction.response.send_message(
            "JudgeBot has been deactivated in this server. All courtroom proceedings are now closed.",
            ephemeral=True,
        )

    @app_commands.command(name="list_cases", description="List all active cases")
    async def list_cases(self, interaction: discord.Interaction):
        cases = self.repo.cases.list_cases()

        if not cases:
            await interaction.response.send_message(
                "There are no active cases at the moment.", ephemeral=True
            )
            return

        case_list = "\n".join(
            f"Case ID: <#{case.case_id}>, Accuser: <@{self.repo.cases.get_accuser(case.case_id)}>, Accused: {', '.join(f'<@{user_id}>' for user_id in self.repo.cases.get_accused(case.case_id))}, Status: {case.status}"
            for case in cases
        )
        await interaction.response.send_message(
            f"Active Cases:\n{case_list}", ephemeral=True
        )

    @app_commands.command(
        name="case_details", description="Get details of a specific case by thread ID"
    )
    @app_commands.describe(thread="Attach the thread corresponding to the case")
    async def case_details(
        self, interaction: discord.Interaction, thread: discord.Thread
    ):
        try:
            thread_id_int = int(thread.id)
        except ValueError:
            await interaction.response.send_message(
                "Invalid thread ID format. Please provide a numeric thread ID.",
                ephemeral=True,
            )
            return

        case = self.repo.cases.get_case(thread_id_int)
        if not case:
            await interaction.response.send_message(
                f"No case found with thread ID: {thread}", ephemeral=True
            )
            return

        accused = self.repo.cases.get_accused(case.case_id)
        accuser = self.repo.cases.get_accuser(case.case_id)

        accused_mentions = ", ".join(f"<@{user_id}>" for user_id in accused)
        case_info = (
            f"Case Details for Case: <#{thread_id_int}>",
            f"Accuser: <@{accuser}>",
            f"Accused: {accused_mentions}",
            f"Reason: {case.reason}",
            f"Case Type: {case.type}",
            f"Status: {case.status}",
            f"Summary: {trim_message(case.summary, 1800)}"
            if case.summary
            else "No summary available",
        )
        await interaction.response.send_message("\n".join(case_info), ephemeral=True)

    @app_commands.command(
        name="search_cases", description="Search for cases by keyword"
    )
    @app_commands.describe(query="The keyword to search for in cases")
    async def search_cases(self, interaction: discord.Interaction, query: str):
        results = self.repo.cases.search_cases(query)

        if not results:
            await interaction.response.send_message(
                "No cases found matching the query.", ephemeral=True
            )
            return

        response = "\n\n".join(
            f"""Case ID: <#{case.case_id}>\nSummary: {trim_message(case.summary, 100) if case.summary else "No summary available"}\nStatus: {case.status}\nType: {case.type}\nAccuser: <@{self.repo.cases.get_accuser(case.case_id)}>\nAccused: {", ".join(f"<@{user_id}>" for user_id in self.repo.cases.get_accused(case.case_id))}"""
            for case in results[:10]  # Limit to top 10 results
        )
        await interaction.response.send_message(trim_message(response), ephemeral=True)

    @cog_context_menu(name="Summarize")
    @app_commands.describe(message="The message to summarize the case from")
    async def summarize_case(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        await interaction.response.defer(ephemeral=True)
        if not message.channel or not isinstance(message.channel, discord.Thread):
            print("Summarize command used outside of a thread")
            await interaction.followup.send(
                "This command can only be used in case threads.", ephemeral=True
            )
            return

        case = self.repo.cases.get_case(message.channel.id)
        if not case:
            print("No case found for this thread")
            await interaction.followup.send(
                "No case found for this thread.", ephemeral=True
            )
            return

        logs: list = self.repo.logs.get_logs(message.channel.id)
        # conversation = "\n".join(f"{log['speaker']}: {log['message']}" for log in logs[-24:])

        response = await google_summarize_conversation(
            logs, case.summary if case.summary else "No summary yet."
        )

        if not response:
            await interaction.followup.send(
                "Summary could not be generated.", ephemeral=True
            )
            return
        self.repo.cases.update_summary(case.case_id, response.strip(), len(logs))

        await interaction.followup.send(
            f"Updated Summary:\n{case.summary}", ephemeral=True
        )

        header_message = await construct_header_message(self.bot, case)

        if not case.og_message_id:
            await interaction.followup.send(
                "Original case message not found.", ephemeral=True
            )
            return

        og_msg = await message.channel.fetch_message(case.og_message_id)
        await og_msg.edit(content=trim_message(header_message), view=CaseView())

    @cog_context_menu(name="Attach Evidence")
    async def attach_evidence(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        if not message.channel or not isinstance(message.channel, discord.Thread):
            await interaction.response.send_message(
                "This command can only be used in case threads.", ephemeral=True
            )
            return

        case_exists = self.repo.cases.has_case(message.channel.id)
        if not case_exists:
            await interaction.response.send_message(
                "No case found for this thread.", ephemeral=True
            )
            return
        await interaction.response.send_modal(AttachEvidenceModal())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        assert self.bot.user is not None, "Bot user should not be None"

        if message.author.bot:
            return

        if not message.channel or not isinstance(message.channel, discord.Thread):
            return

        if not self.repo.cases.has_case(message.channel.id):
            return

        case = self.repo.cases.get_case(message.channel.id)
        if not case:
            return

        if case.status == "closed":
            return

        self.repo.logs.add_log(
            message.channel.id,
            LogEntry(
                message_id=message.id,
                message_reference_id=message.reference.message_id
                if message.reference
                else None,
                speaker=message.author.name,
                message=message.content,
                timestamp=message.created_at,
                summary=None,
                author_id=message.author.id,
                is_judge=False,
            ),
        )

        await message.channel.typing()
        await message.add_reaction(
            "⏳"
        )  # Indicate that the bot is processing the message

        # PROMPT CONSTRUCTION
        case_header = await construct_header_message(self.bot, case)
        evidence_summary = await get_evidence_summaries(case, self.repo)

        logs = self.repo.logs.get_logs(message.channel.id)

        dialogue = "\n".join(
            f'{log.speaker}({log.author_id}): "{log.message}"' for log in logs[-24:]
        )

        case_details = CASE_PROMPT.format(
            case_header=case_header,
            evidence_summary=evidence_summary or "No evidence attached yet.",
            dialogue=dialogue,
            case_id=case.case_id,
            accuser_id=self.repo.cases.get_accuser(case.case_id),
            accused_ids=", ".join(
                str(uid) for uid in self.repo.cases.get_accused(case.case_id)
            ),
            witness_ids=", ".join(
                str(uid) for uid in self.repo.cases.get_witnesses(case.case_id)
            ),
            verdict=case.verdict if case.verdict else "No verdict yet.",
        )
        print("Constructed case details for AI:\n", case_details)

        bot_response = await generate_content(
            self.bot, [BOT_PROMPT, case_details], tools=tools
        )

        bot_message = await message.channel.send(
            trim_message(bot_response), reference=message
        )

        self.repo.logs.add_log(
            message.channel.id,
            LogEntry(
                message_id=bot_message.id,
                message_reference_id=message.id,
                speaker=self.bot.user.name,
                message=bot_response,
                timestamp=bot_message.created_at,
                summary=None,
                author_id=self.bot.user.id,
                is_judge=True,
            ),
        )
        await message.remove_reaction("⏳", self.bot.user)

        logs = self.repo.logs.get_logs(message.channel.id)

        last_summary_index = case.last_summary_index if case.last_summary_index else 0
        if len(logs) - last_summary_index >= 10:
            summary = await google_summarize_conversation(
                logs, case.summary if case.summary else ""
            )
        else:
            summary = case.summary if case.summary else ""

        self.repo.cases.update_summary(case.case_id, summary, len(logs))

        case_details = await construct_header_message(self.bot, case)
        if not case.og_message_id:
            return
        og_msg = await message.channel.fetch_message(case.og_message_id)

        await og_msg.edit(content=trim_message(case_details), view=CaseView())


async def setup(bot: JudgeBot):
    await bot.add_cog(JudgeCog(bot))
    bot.add_view(CaseView())
    bot.add_view(FileCaseView())
    bot.add_view(RequestEvidenceView())
