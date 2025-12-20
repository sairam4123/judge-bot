from discord import app_commands
import discord
from discord.ext import commands
from typing import TYPE_CHECKING

from judge_bot.genai import get_client
from judge_bot.modules.courts.core.models import Court, LogEntry
from judge_bot.modules.courts.core.prompt import BOT_PROMPT
from judge_bot.modules.courts.core.repositories import RepositoryManager
from judge_bot.modules.courts.ui.request_evidence_view import RequestEvidenceView
from judge_bot.utils import construct_header_message, get_evidence_summaries, google_summarize_conversation, trim_message
if TYPE_CHECKING:
    from judge_bot.bot import JudgeBot

from judge_bot.modules.courts.tools import close_case, request_evidence, update_verdict, add_witness, tools
from google.genai import types as genai_types

from exts.cogs import cog_context_menu, CommandsCog
from .ui import CaseView, FileCaseView, AttachEvidenceModal

class JudgeCog(CommandsCog):
    """Cog for judge-related commands."""
    def __init__(self, bot: JudgeBot):
        super().__init__(bot)
        self.bot = bot
        self.repo = RepositoryManager(bot)


    @app_commands.command(name="start", description="Start JudgeBot in this server")
    async def start(self, interaction: discord.Interaction, name: str = "Default Court", description: str = "Default court for this server"):
        assert interaction.channel_id is not None, "Channel ID should not be None"
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        if self.repo.courts.contains_court(interaction.guild_id, interaction.channel_id):
            await interaction.response.send_message("JudgeBot is already active in this server.", ephemeral=True)
            return
        await interaction.response.send_message("JudgeBot is now active in this server! All courtroom proceedings will be handled here.", ephemeral=True)
        channel = interaction.channel
        if channel is not None and isinstance(channel, discord.TextChannel):
            await channel.send("Order! Order in this court! JudgeBot is now presiding over this courtroom. Let the proceedings begin!", view=FileCaseView())
            self.repo.courts.create_court(Court(
                court_id=interaction.channel_id,
                name=name,
                description=description,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                created_at=interaction.created_at
            ))

    @app_commands.command(name="stop", description="Stop JudgeBot in this server")
    async def stop(self, interaction: discord.Interaction):
        assert interaction.channel_id is not None, "Channel ID should not be None"
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        if not self.repo.courts.contains_court(interaction.guild_id, interaction.channel_id):
            await interaction.response.send_message("JudgeBot is not active in this server.", ephemeral=True)
            return
        self.repo.courts.delete_court(interaction.channel_id)
        await interaction.response.send_message("JudgeBot has been deactivated in this server. All courtroom proceedings are now closed.", ephemeral=True)

    @app_commands.command(name="list_cases", description="List all active cases")
    async def list_cases(self, interaction: discord.Interaction):
        cases = self.repo.cases.list_cases()

        if not cases:
            await interaction.response.send_message("There are no active cases at the moment.", ephemeral=True)
            return


        case_list = "\n".join(
            f"Case ID: <#{case.case_id}>, Accuser: <@{self.repo.cases.get_accuser(case.case_id)}>, Accused: {', '.join(f'<@{user_id}>' for user_id in self.repo.cases.get_accused(case.case_id))}, Status: {case.status}"
            for case in cases
        )
        await interaction.response.send_message(f"Active Cases:\n{case_list}", ephemeral=True)

    @app_commands.command(name="case_details", description="Get details of a specific case by thread ID")
    @app_commands.describe(thread="Attach the thread corresponding to the case")
    async def case_details(self, interaction: discord.Interaction, thread: discord.Thread):
        try:
            thread_id_int = int(thread.id)
        except ValueError:
            await interaction.response.send_message("Invalid thread ID format. Please provide a numeric thread ID.", ephemeral=True)
            return

        case = self.repo.cases.get_case(thread_id_int)
        if not case:
            await interaction.response.send_message(f"No case found with thread ID: {thread}", ephemeral=True)
            return
        
        accused = self.repo.cases.get_accused(case.case_id)
        accuser = self.repo.cases.get_accuser(case.case_id)    

        accused_mentions = ', '.join(f'<@{user_id}>' for user_id in accused)
        case_info = (
            f"Case Details for Case: <#{thread_id_int}>",
            f"Accuser: <@{accuser}>",
            f"Accused: {accused_mentions}",
            f"Reason: {case.reason}",
            f"Case Type: {case.type}",
            f"Status: {case.status}",
            f"Summary: {trim_message(case.summary, 1800)}" if case.summary else "No summary available",
            
        )
        await interaction.response.send_message("\n".join(case_info), ephemeral=True)

    @cog_context_menu(name="Summarize")
    @app_commands.describe(message="The message to summarize the case from")
    async def summarize_case(self,interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)
        if not message.channel or not isinstance(message.channel, discord.Thread):
            print("Summarize command used outside of a thread")
            await interaction.followup.send("This command can only be used in case threads.", ephemeral=True)
            return
        


        case = self.repo.cases.get_case(message.channel.id)
        if not case:
            print("No case found for this thread")
            await interaction.followup.send("No case found for this thread.", ephemeral=True)
            return
        
        accused = self.repo.cases.get_accused(case.case_id)
        accuser = self.repo.cases.get_accuser(case.case_id)    

        logs: list = self.repo.logs.get_logs(message.channel.id)
        # conversation = "\n".join(f"{log['speaker']}: {log['message']}" for log in logs[-24:])

        response = await google_summarize_conversation(logs, case.summary if case.summary else 'No summary yet.')

        if not response:
            await interaction.followup.send("Summary could not be generated.", ephemeral=True)
            return
        self.repo.cases.update_summary(case.case_id, response.strip(), len(logs))

        await interaction.followup.send(f"Updated Summary:\n{case.summary}", ephemeral=True)

        header_message = await construct_header_message(self.bot, case)
        
        if not case.og_message_id:
            await interaction.followup.send("Original case message not found.", ephemeral=True)
            return

        og_msg = await message.channel.fetch_message(case.og_message_id)
        await og_msg.edit(content=trim_message(header_message), view=CaseView())


    @cog_context_menu(name="Attach Evidence")
    async def attach_evidence(self, interaction: discord.Interaction, message: discord.Message):
        if not message.channel or not isinstance(message.channel, discord.Thread):
            await interaction.response.send_message("This command can only be used in case threads.", ephemeral=True)
            return
        
        case_exists = self.repo.cases.has_case(message.channel.id)
        if not case_exists:
            await interaction.response.send_message("No case found for this thread.", ephemeral=True)
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

        google_client = get_client()


        self.repo.logs.add_log(message.channel.id, LogEntry(
            message_id=message.id,
            message_reference_id=message.reference.message_id if message.reference else None,
            speaker=message.author.name,
            message=message.content,
            timestamp=message.created_at,
            summary=None,
            author_id=message.author.id,
            is_judge=False,
        ))

        # PROMPT CONSTRUCTION
        case_details = await construct_header_message(self.bot, case)        
        evidence_summary = await get_evidence_summaries(case, self.repo)
        if case.summary:
            case_details += f"\n\nCase Summary:\n{case.summary}"
        if evidence_summary:
            case_details += f"\n\nEvidence Summaries:\n{evidence_summary}"
        
        logs = self.repo.logs.get_logs(message.channel.id)
        
        dialogue = "\n".join(f"{log.speaker}: {log.message}" for log in logs[-24:])
        case_details += f"\n\nRecent Dialogue:\n{dialogue}"

        case_details += f"\n\nCase ID: {case.case_id}\nAccuser ID: {self.repo.cases.get_accuser(case.case_id)}\nAccused IDs: {', '.join(str(uid) for uid in self.repo.cases.get_accused(case.case_id))}"
        case_details += f"\nCurrent Verdict: {case.verdict if case.verdict else 'No verdict yet.'}"
        case_details += f"\nFunction calls available: {', '.join(tool.function_declarations[0].name for tool in tools if tool.function_declarations and tool.function_declarations[0].name)}"
        # sending to google gemini
        resp = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[BOT_PROMPT, case_details],
            config={
                "tools": tools,
            }
        )
        
        result = {}
        print("Processing function calls from AI response...", len(resp.function_calls) if resp.function_calls else 0)
        if resp.function_calls:
            print(f"Function calls detected: {[func_call.name for func_call in resp.function_calls]}")
            for func_call in resp.function_calls:
                if func_call.name == "update_verdict":
                    print(f"Function call detected: {func_call.name} with args: {func_call.args}")
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    verdict = func_call.args.get("verdict", "")
                    print(f"Function call to update_verdict with case_id: {case_id}, verdict: {verdict}")
                    if case_id and verdict:
                        result["update_verdict"] = await update_verdict(self.bot, case_id, verdict)
                elif func_call.name == "add_witness":
                    print(f"Function call detected: {func_call.name} with args: {func_call.args}")
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    witness_id = int(func_call.args.get("witness_id", 0))
                    print(f"Function call to add_witness with case_id: {case_id}, witness_id: {witness_id}")
                    if case_id and witness_id:
                       result["add_witness"] = await add_witness(self.bot, case_id, witness_id)
                elif func_call.name == "close_case":
                    print(f"Function call detected: {func_call.name} with args: {func_call.args}")
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    reason = func_call.args.get("reason", "")
                    print(f"Function call to close_case with case_id: {case_id}, reason: {reason}")
                    if case_id and reason:
                        result["close_case"] = await close_case(self.bot, case_id, reason)
                
                elif func_call.name == "request_evidence":
                    print(f"Function call detected: {func_call.name} with args: {func_call.args}")
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    content = func_call.args.get("content", "")
                    print(f"Function call to request_evidence with case_id: {case_id}, content: {content}")
                    if case_id and content:
                        result["request_evidence"] = await request_evidence(self.bot, case_id, content)
                    
        
        print("Function call results:", result)

        function_response_part = [genai_types.Part.from_function_response(name=name, response={"result": func_response}) for name, func_response in result.items() if func_response]
        contents = [resp.candidates[0].content] if resp.candidates else []
        contents.append(genai_types.Content(parts=function_response_part, role="User"))
        
        new_resp = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config={
                "tools": tools,
            }
        )

        bot_response = new_resp.text.strip() if new_resp.text else resp.text.strip() if resp.text else ""
        if not bot_response:
            print("No text in AI response", resp, new_resp)
            await message.channel.send("Sorry, I couldn't generate a response at this time.")
            return
    
        bot_message = await message.channel.send(trim_message(bot_response), reference=message)

        self.repo.logs.add_log(message.channel.id, LogEntry(
            message_id=bot_message.id,
            message_reference_id=message.id,
            speaker=self.bot.user.name,
            message=bot_response,
            timestamp=bot_message.created_at,
            summary=None,
            author_id=self.bot.user.id,
            is_judge=True,
        ))

        logs = self.repo.logs.get_logs(message.channel.id)

        last_summary_index = case.last_summary_index if case.last_summary_index else 0
        if len(logs) - last_summary_index >= 10:
            summary = await google_summarize_conversation(logs, case.summary if case.summary else '')
        else:
            summary = case.summary if case.summary else ''
        
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

    