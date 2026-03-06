import discord
from datetime import datetime

from judge_bot.bot import JudgeBot
from judge_bot.genai.generate import generate_content
from judge_bot.modules.courts.core.models import Evidence, LogEntry
from judge_bot.modules.courts.core.prompt import BOT_PROMPT, CASE_PROMPT
from judge_bot.modules.courts.ui.evidence_gallery import EvidenceMediaGallery
from judge_bot.utils import (
    construct_header_message,
    get_evidence_summaries,
    google_summarize_file,
    trim_message,
)
from judge_bot.modules.courts.tools import tools
from judge_bot.modules.courts.core.repositories import RepositoryManager


class AttachEvidenceModal(discord.ui.Modal, title="Attach Evidence to Case"):
    def __init__(self, *, view: discord.ui.View | None = None) -> None:
        super().__init__()
        self.view = view

    evidence_document = discord.ui.Label(
        text="Upload Evidence(s)",
        component=discord.ui.FileUpload(
            custom_id="evidence_upload",
            min_values=1,
            max_values=2,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.evidence_document.component, discord.ui.FileUpload)
        assert isinstance(interaction.client, JudgeBot)
        assert isinstance(interaction.message, discord.Message)
        assert isinstance(interaction.client.user, discord.User)

        repository = RepositoryManager(interaction.client)
        if interaction.channel and isinstance(interaction.channel, discord.Thread):
            case = repository.cases.get_case(interaction.channel.id)
            if not case:
                await interaction.response.send_message(
                    "No case found for this thread.", ephemeral=True
                )
                return

            await interaction.response.send_message(
                "Uploading and summarizing evidence. Please wait...", ephemeral=True
            )

            summaries = """
Summaries of attached evidence:
"""
            # Process each uploaded file
            for uploaded_file in self.evidence_document.component.values:
                print(f"Processing uploaded file: {uploaded_file.filename}")
                summary = await google_summarize_file(uploaded_file)
                repository.evidences.add_evidence(
                    Evidence(
                        evidence_id=0,  # Will be set by the repository
                        case_id=case.case_id,
                        filename=uploaded_file.filename,
                        url=uploaded_file.url,
                        summary=summary,
                        uploader_id=interaction.user.id,
                        created_at=datetime.now(),
                        description="",
                    )
                )
                summaries += f"- {uploaded_file.filename}: {summary}\n"

            files = [
                (await f.to_file(), f.content_type, f.url)
                for f in self.evidence_document.component.values
            ]

            print(
                f"Prepared files for attachment: {files}, {[(f.filename, f.uri) for f, _, _ in files]}"
            )

            await interaction.followup.send(
                ephemeral=True,
                view=EvidenceMediaGallery("Evidence attached to the case.", files),
                files=[f for f, _, _ in files],
            )
            files = [
                (await f.to_file(), f.content_type, f.url)
                for f in self.evidence_document.component.values
            ]
            await interaction.channel.send(
                view=EvidenceMediaGallery(
                    f"New evidence attached by {interaction.user.mention}: {summaries}",
                    files,
                ),
                files=[f for f, _, _ in files],
            )

            case_header = await construct_header_message(interaction.client, case)
            evidence_summary = await get_evidence_summaries(case, repository)

            logs = repository.logs.get_logs(interaction.channel.id)

            dialogue = "\n".join(
                f'{log.speaker}({log.author_id}): "{log.message}"' for log in logs[-24:]
            )

            case_details = CASE_PROMPT.format(
                case_header=case_header,
                evidence_summary=evidence_summary or "No evidence attached yet.",
                dialogue=dialogue,
                case_id=case.case_id,
                accuser_id=repository.cases.get_accuser(case.case_id),
                accused_ids=", ".join(
                    str(uid) for uid in repository.cases.get_accused(case.case_id)
                ),
                witness_ids=", ".join(
                    str(uid) for uid in repository.cases.get_witnesses(case.case_id)
                ),
                verdict=case.verdict if case.verdict else "No verdict yet.",
            )
            print("Constructed case details for AI:\n", case_details)

            bot_response = await generate_content(
                interaction.client, [BOT_PROMPT, case_details], tools=tools
            )

            bot_message = await interaction.channel.send(
                trim_message(bot_response), reference=interaction.message
            )

            repository.logs.add_log(
                interaction.channel.id,
                LogEntry(
                    message_id=bot_message.id,
                    message_reference_id=interaction.message.id,
                    speaker=interaction.client.user.name,
                    message=bot_response,
                    timestamp=bot_message.created_at,
                    summary=None,
                    author_id=interaction.client.user.id,
                    is_judge=True,
                ),
            )
