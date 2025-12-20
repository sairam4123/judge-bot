import discord
import asyncio
from judge_bot.genai import get_client
from judge_bot.bot import JudgeBot
import typing as t

from google.genai import types as genai_types

from judge_bot.modules.courts.core.models import Case, LogEntry
from judge_bot.modules.courts.core.prompt import CASE_DETAILS, SESSION_MSG, SUMMARIZE_PROMPT, SUMMARIZE_TEXT_PROMPT, SUMMARY_MSG
from judge_bot.modules.courts.core.repositories import RepositoryManager

async def google_summarize_file(file: discord.Attachment) -> str:
    google_client = get_client()
    with open(f"attachments/{file.filename}", "wb") as f:
        await file.save(f)
    
    uploaded_file = await google_client.aio.files.upload(file=f"attachments/{file.filename}")

    while uploaded_file.state == "PROCESSING":
        await asyncio.sleep(5)
        uploaded_file = await google_client.aio.files.get(name=f"attachments/{file.filename}")

    response = await google_client.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=["Summarize the contents of the following file:\n\n", 
                 uploaded_file]
    )
    if response and response.text:
        return response.text.strip()
    return "Summary could not be generated."


async def construct_header_message(client: JudgeBot, case: Case) -> str:
    repo = RepositoryManager(client)
    accused_ids = repo.cases.get_accused(case.case_id)
    accuser_id = repo.cases.get_accuser(case.case_id)
    if not accused_ids or accuser_id is None:
        raise ValueError("Accuser or accused not found.")
    
    accused = [await client.fetch_user(user_id) for user_id in accused_ids]
    accused_mentions = ', '.join(user.mention for user in accused)
    accused_names = ', '.join(user.name for user in accused)
    accuser = await client.fetch_user(accuser_id)
    # og_msg = await channel.fetch_message(case['og_message_id'])
    # if not og_msg:
    #     raise ValueError("Original message not found.")
    
    message = CASE_DETAILS.format(
        user_name=accuser.name, 
        user_mention=accuser.mention, 
        accused_names=accused_names,
        accused_mentions=accused_mentions, 
        reason=case.reason, 
        case_type=case.type, 
        status=case.status, 
    )
    
    num_logs = repo.logs.count_logs(case.case_id)
    if num_logs < 1:
        message += "\n\n" + SESSION_MSG

    if case.summary:
        message += "\n\n" + SUMMARY_MSG.format(summary=case.summary)
    print(case.verdict)
    if case.verdict:
        message += f"\n\n## Verdict: {case.verdict}"
    

    return message

    # if not case.get('summary'):
    #     await og_msg.edit(content=CASE_DETAILS_START.format(user_name=accuser.name, accused_mentions=accused_mentions, reason=case['reason'], case_type=case['case_type'], status=case['status'], summary=case.get('summary', ''),  view=CaseView())
    # else:
    #     await og_msg.edit(content=CASE_DETAILS.format(user=accuser, accused=accused_mentions, reason=case['reason'], case_type=case['case_type'], status=case['status'], accused_names=accused_names)[:1950], view=CaseView())

def trim_message(content: str, limit: int = 2000) -> str:
    if len(content) <= limit:
        return content
    return content[:limit - 3] + "..."


# async def timeout_callable[T](callable: t.Awaitable[T], /, *, timeout: float) -> T | None:
#     try:
#         print("Starting timeout callable...")
#         return await asyncio.wait_for(callable, timeout=timeout)
#     except asyncio.TimeoutError:
#         return None

async def google_summarize_text(text: str) -> str:
    google_client = get_client()
    response = await google_client.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[SUMMARIZE_TEXT_PROMPT, text]
    )
    if response and response.text:
        return response.text.strip()
    return "Summary could not be generated."

async def google_summarize_conversation(conversation: list[LogEntry], current_summary: str) -> str:
    logs = "\n".join(f"{log.speaker}: {log.message}" for log in conversation[-24:])
    google_client = get_client()
    response = await google_client.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[SUMMARIZE_PROMPT,
                  f"Last 24 logs of Conversation:\n{logs}\n\nCurrent Summary:\n{current_summary}\n\nUpdated Summary:"]
    )
    if response and response.text:
        return response.text.strip()
    return "Summary could not be generated."

async def get_evidence_summaries(case: Case, repo: RepositoryManager) -> str:
    evidence_summaries = []
    evidences = repo.evidences.get_evidences(case.case_id)
    for evidence in evidences:
        if evidence.summary:
            evidence_summaries.append(f"{evidence.filename}: Summary: {evidence.summary}")
    
    return "\n".join(evidence_summaries)

def tool_declaration(tool_config: dict[str, t.Any]) -> genai_types.Tool:
    tool_config.pop("func")
    new_tool_config = genai_types.FunctionDeclaration.model_validate(tool_config)
    return genai_types.Tool(function_declarations=[new_tool_config])
    
def register_tools(tools_list: list[dict[str, t.Any]]) -> list[genai_types.Tool]:
    registered_tools = []
    for tool_config in tools_list:
        registered_tools.append(tool_declaration(tool_config))
    return registered_tools