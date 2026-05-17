import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME = "adk_rag_starter"
USER_ID = "local_user"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")
logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logging.getLogger("google_genai.types").disabled = True

def get_text_from_part(part):
    part_data = part.model_dump(exclude_none=True)
    return part_data.get("text", "")

async def call_agent(runner, session_id, message):
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )
    final_response = ""

    events = runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    )

    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            final_response = "".join(
                get_text_from_part(part) for part in event.content.parts
            )

    print(f"\nAgent: {final_response}\n")

async def main():
    from rag_agent.agent import root_agent

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name = APP_NAME,
        user_id = USER_ID,
        state = {
            "user:learning_goal": "Learning google adk through a rag project"
        },
    )

    runner = Runner(app_name = APP_NAME,
                    agent = root_agent,
                    session_service = session_service)

    while True:
        user_input = input("You: ")

        if user_input.lower() in {"exit", "quit"}:
            break

        if not user_input.strip():
            continue
    
        await call_agent(runner, session.id, user_input)

if __name__ == "__main__":
    asyncio.run(main())