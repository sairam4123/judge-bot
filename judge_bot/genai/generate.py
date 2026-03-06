from judge_bot.config import JudgeBotConfig
from judge_bot.genai.client import get_client
from judge_bot.bot import JudgeBot

from google.genai import types as genai_types
from judge_bot.modules.courts.tools import (
    search_case,
    update_verdict,
    add_witness,
    close_case,
    request_evidence,
)
from judge_bot.utils import JBTool

TOOLS_PROMPT = """You have access to the following tools that you can use to interact with the court system:
{tools}
"""


async def generate_content(
    bot: JudgeBot,
    prompt: str | list[str | genai_types.Content],
    model: str = JudgeBotConfig().model,
    tools: list[JBTool] | None = None,
    max_iterations: int = 5,
) -> str:
    tools = tools or []

    google_client = get_client()

    avl_tools = [
        f"{tool[0].function_declarations[0].name} - {tool[0].function_declarations[0].description}"
        for tool in tools
        if tool[0]
        and tool[0].function_declarations
        and tool[0].function_declarations[0].name
    ]

    tools_prompt = TOOLS_PROMPT.format(tools="\n".join(avl_tools)) if avl_tools else ""

    resp = await google_client.aio.models.generate_content(
        model=model,
        contents=[prompt, tools_prompt],
        config={
            "tools": [tool[0] for tool in tools],
        },
    )
    original_response = resp.text.strip() if resp.text else ""

    i = 0
    # text_response = resp.text.strip() if resp.text else ""
    while (
        resp.function_calls and i < max_iterations
    ):  # Limit to max_iterations iterations to prevent infinite loops
        i += 1
        result = {}
        print(
            f"Processing {len(resp.function_calls) if resp.function_calls else 0} function calls from AI response...",
            f"Iteration {i}/{max_iterations}",
        )
        if resp.function_calls:
            print(
                f"Function calls detected: {[func_call.name for func_call in resp.function_calls]}"
            )
            for func_call in resp.function_calls:
                if func_call.name == "update_verdict":
                    print(
                        f"Function call detected: {func_call.name} with args: {func_call.args}"
                    )
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    verdict = func_call.args.get("verdict", "")
                    print(
                        f"Function call to update_verdict with case_id: {case_id}, verdict: {verdict}"
                    )
                    if case_id and verdict:
                        result["update_verdict"] = await update_verdict(
                            bot, case_id, verdict
                        )
                    else:
                        print(
                            f"Invalid arguments for update_verdict: case_id={case_id}, verdict={verdict}"
                        )
                        result["update_verdict"] = {
                            "status": "error",
                            "message": "Invalid arguments for update_verdict. case_id must be an integer and verdict must be a non-empty string.",
                        }

                elif func_call.name == "add_witness":
                    print(
                        f"Function call detected: {func_call.name} with args: {func_call.args}"
                    )
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    witness_id = int(func_call.args.get("witness_id", 0))
                    print(
                        f"Function call to add_witness with case_id: {case_id}, witness_id: {witness_id}"
                    )
                    if case_id and witness_id:
                        result["add_witness"] = await add_witness(
                            bot, case_id, witness_id
                        )
                    else:
                        print(
                            f"Invalid arguments for add_witness: case_id={case_id}, witness_id={witness_id}"
                        )
                        result["add_witness"] = {
                            "status": "error",
                            "message": "Invalid arguments for add_witness. case_id and witness_id must be integers.",
                        }

                elif func_call.name == "close_case":
                    print(
                        f"Function call detected: {func_call.name} with args: {func_call.args}"
                    )
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    reason = func_call.args.get("reason", "")
                    print(
                        f"Function call to close_case with case_id: {case_id}, reason: {reason}"
                    )
                    if case_id and reason:
                        result["close_case"] = await close_case(bot, case_id, reason)
                    else:
                        print(
                            f"Invalid arguments for close_case: case_id={case_id}, reason={reason}"
                        )
                        result["close_case"] = {
                            "status": "error",
                            "message": "Invalid arguments for close_case. case_id must be an integer and reason must be a non-empty string.",
                        }

                elif func_call.name == "request_evidence":
                    print(
                        f"Function call detected: {func_call.name} with args: {func_call.args}"
                    )
                    if not func_call.args:
                        continue
                    case_id = int(func_call.args.get("case_id", 0))
                    content = func_call.args.get("content", "")
                    print(
                        f"Function call to request_evidence with case_id: {case_id}, content: {content}"
                    )
                    if case_id and content:
                        result["request_evidence"] = await request_evidence(
                            bot, case_id, content
                        )
                    else:
                        print(
                            f"Invalid arguments for request_evidence: case_id={case_id}, content={content}"
                        )
                        result["request_evidence"] = {
                            "status": "error",
                            "message": "Invalid arguments for request_evidence. case_id must be an integer and content must be a non-empty string.",
                        }

                elif func_call.name == "search_case":
                    print(
                        f"Function call detected: {func_call.name} with args: {func_call.args}"
                    )
                    if not func_call.args:
                        continue
                    query = func_call.args.get("query", "")
                    print(f"Function call to search_case with query: {query}")
                    if query:
                        # Implement search_case function and add it to tools for this to work
                        result["search_case"] = await search_case(bot, query)
                    else:
                        print(f"Invalid arguments for search_case: query={query}")
                        result["search_case"] = {
                            "status": "error",
                            "message": "Invalid arguments for search_case. query must be a non-empty string.",
                        }

        print("Function call results:", result)

        function_response_part = [
            genai_types.Part.from_function_response(
                name=name, response={"result": func_response}
            )
            for name, func_response in result.items()
            if func_response
        ]
        contents = [resp.candidates[0].content] if resp.candidates else []
        contents.append(genai_types.Content(parts=function_response_part, role="User"))

        resp = await google_client.aio.models.generate_content(
            model=model,
            contents=[*prompt, *contents],
            config={
                "tools": [tool[0] for tool in tools] if tools else [],
            },
        )

    bot_response = (
        resp.text.strip()
        if resp.text
        else original_response
        if original_response
        else "I'm sorry, I couldn't generate a response at this time."
    )
    if i >= max_iterations:
        print(
            f"Reached maximum iterations ({max_iterations}) while processing function calls. Last response: {resp}"
        )
        bot_response += (
            "\n\n(Note: Function call processing is stopped. Max iterations reached.)"
        )

    if not resp.text and not original_response:
        print(
            "No text response generated after processing function calls. Returning default message."
        )

    return bot_response
