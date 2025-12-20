import discord
from datetime import datetime

from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.core.models import Evidence
from judge_bot.modules.courts.ui.evidence_gallery import EvidenceMediaGallery
from judge_bot.utils import google_summarize_file
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
        )
    )

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.evidence_document.component, discord.ui.FileUpload)
        assert isinstance(interaction.client, JudgeBot)
        repository = RepositoryManager(interaction.client)
        if interaction.channel and isinstance(interaction.channel, discord.Thread):
            case = repository.cases.get_case(interaction.channel.id)
            if not case:
                await interaction.response.send_message("No case found for this thread.", ephemeral=True)
                return
            
            await interaction.response.send_message("Uploading and summarizing evidence. Please wait...", ephemeral=True)

            # Process each uploaded file
            for uploaded_file in self.evidence_document.component.values:
                print(f"Processing uploaded file: {uploaded_file.filename}")
                summary = await google_summarize_file(uploaded_file)
                repository.evidences.add_evidence(Evidence(
                    evidence_id=0,  # Will be set by the repository
                    case_id=case.case_id,
                    filename=uploaded_file.filename,
                    url=uploaded_file.url,
                    summary=summary,
                    uploader_id=interaction.user.id,
                    created_at=datetime.now(),
                    description=""
                ))

            files = [(await f.to_file(), f.content_type, f.url) for f in self.evidence_document.component.values]
            
            await interaction.followup.send(ephemeral=True, view=EvidenceMediaGallery(
                "Evidence attached to the case.",
                files
            ), files=[f for f, _, _ in files])
            await interaction.channel.send(view=EvidenceMediaGallery(
                f"New evidence has been attached to the case by {interaction.user.mention}.",
                files
            ), files=[f for f, _, _ in files])