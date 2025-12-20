import discord
from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.core.repositories import RepositoryManager
from judge_bot.modules.courts.ui.case_view import CaseView
from judge_bot.modules.courts.ui.request_evidence_view import RequestEvidenceView
from judge_bot.utils import construct_header_message, register_tools, trim_message


async def update_verdict(bot: JudgeBot, case_id: int, verdict: str) -> dict[str, str] | None:
    repo = RepositoryManager(bot)
    case = repo.cases.get_case(case_id)
    print(f"Fetched case for ID {case_id}: {case}")
    if not case:
        return
    print(f"Updating verdict for case {case_id} to '{verdict}'")
    repo.cases.update_verdict(case_id, verdict)

    case = repo.cases.get_case(case_id)
    print(f"Fetched updated case for ID {case_id}: {case}")
    if not case:
        return

    case_details = await construct_header_message(bot, case)
    if not case.og_message_id:
        return
    # Fetch the thread associated with the case
    thread = bot.get_channel(case.case_id)
    if not thread or not isinstance(thread, discord.Thread):
        return
    print(f"Fetched thread for case ID {case_id}: {thread}")
    og_msg = await thread.fetch_message(case.og_message_id)
    await og_msg.edit(content=trim_message(case_details), view=CaseView())

    return {
        "status": "success",
        "message": "Verdict updated and case message edited."
    }


async def add_witness(bot: JudgeBot, case_id: int, witness_id: int) -> dict[str, str] | None:
    repo = RepositoryManager(bot)
    case = repo.cases.get_case(case_id)
    if not case:
        return

    repo.participants.add_witness_participant(case_id, witness_id)

    return {
        "status": "success",
        "message": "Witness added to the case."
    }

async def close_case(bot: JudgeBot, case_id: int, reason: str) -> dict[str, str] | None:
    repo = RepositoryManager(bot)
    case = repo.cases.get_case(case_id)
    if not case:
        return

    repo.cases.close_case(case_id, reason)

    # we need to fetch the updated case info
    case = repo.cases.get_case(case_id)
    if not case:
        return

    case_details = await construct_header_message(bot, case)
    if not case.og_message_id:
        return
    # Fetch the thread associated with the case
    thread = bot.get_channel(case.case_id)
    if not thread or not isinstance(thread, discord.Thread):
        return
    og_msg = await thread.fetch_message(case.og_message_id)
    await og_msg.edit(content=trim_message(case_details), view=CaseView())

    await thread.send("The case has been closed due to the following reason: " + reason + "\nCourt is adjourned!")
    await thread.edit(archived=True, locked=True)

    return {
        "status": "success",
        "message": "Case closed and message updated."
    }

async def request_evidence(bot: JudgeBot, case_id: int, content: str) -> dict[str, str] | None:
    repo = RepositoryManager(bot)
    print(f"Requesting evidence for case ID {case_id}")
    case = repo.cases.get_case(case_id)
    if not case:
        return
    
    print(f"Requesting evidence for case ID {case_id} with content: {content}")
    # Fetch the thread associated with the case
    thread = bot.get_channel(case.case_id)
    if not thread or not isinstance(thread, discord.Thread):
        return
    print(f"Fetched thread for case ID {case_id}: {thread}")
    
    
    await thread.send(f"{content}", view=RequestEvidenceView())

    return {
        "status": "success",
    }


async def reopen_case(bot: JudgeBot, case_id: int) -> dict[str, str] | None:
    repo = RepositoryManager(bot)
    case = repo.cases.get_case(case_id)
    if not case:
        return

    repo.cases.reopen_case(case_id)

    case = repo.cases.get_case(case_id)
    if not case:
        return

    case_details = await construct_header_message(bot, case)
    if not case.og_message_id:
        return
    # Fetch the thread associated with the case
    thread = bot.get_channel(case.case_id)
    if not thread or not isinstance(thread, discord.Thread):
        return
    og_msg = await thread.fetch_message(case.og_message_id)
    await og_msg.edit(content=trim_message(case_details), view=CaseView())

    await thread.edit(archived=False, locked=False)

    return {
        "status": "success",
        "message": "Case reopened and message updated."
    }

update_verdict_tool = {
    "name": "update_verdict",
    "func": update_verdict,
    "description": "Update the verdict of a case and edit the case message accordingly.",
    "parameters": {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "The ID of the case to update."
            },
            "verdict": {
                "type": "string",
                "description": "The new verdict for the case."
            }
        },
        "required": ["case_id", "verdict"]
    }
}

add_witness_tool = {
    "name": "add_witness",
    "func": add_witness,
    "description": "Add a witness to a case.",
    "parameters": {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "The ID of the case to which the witness will be added."
            },
            "witness_id": {
                "type": "string",
                "description": "The user ID of the witness to add to the case."
            }
        },
        "required": ["case_id", "witness_id"]
    }
}

close_case_tool = {
    "name": "close_case",
    "func": close_case,
    "description": "Close a case with a given reason and update the case message accordingly.",
    "parameters": {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "The ID of the case to close."
            },
            "reason": {
                "type": "string",
                "description": "The reason for closing the case."
            }
        },
        "required": ["case_id", "reason"]
    }
}

request_evidence_tool = {
    "name": "request_evidence",
    "func": request_evidence,
    "description": "Request evidence from participants in a case.",
    "parameters": {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "The ID of the case for which evidence is being requested."
            },
            "content": {
                "type": "string",
                "description": "The content of the evidence request message."
            }
        },
        "required": ["case_id", "content"]
    }
}

reopen_case_tool = {
    "name": "reopen_case",
    "func": reopen_case,
    "description": "Reopen a closed case and update the case message accordingly.",
    "parameters": {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "The ID of the case to reopen."
            }
        },
        "required": ["case_id"]
    }
}

tools = register_tools([update_verdict_tool, add_witness_tool, close_case_tool, request_evidence_tool])